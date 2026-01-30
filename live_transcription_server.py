"""
FastAPI WebSocket server for live transcription with Deepgram and Speechmatics
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from loguru import logger
import websockets
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv(override=True)

app = FastAPI(title="Live Transcription Server")

# Allow Base44 frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/transcribe")
async def transcribe(
    websocket: WebSocket,
    provider: str = Query(default="deepgram-nova2", description="STT provider: deepgram-nova2, deepgram-nova3, speechmatics")
):
    """WebSocket endpoint for live transcription"""
    await websocket.accept()
    logger.info(f"🎙️ Client connected - Provider: {provider}")

    try:
        # Send ready signal
        await websocket.send_json({
            'type': 'connected',
            'provider': provider,
            'status': 'ready'
        })

        # Start transcription based on provider
        if provider.startswith('deepgram'):
            model = 'nova-3' if provider == 'deepgram-nova3' else 'nova-2'
            await deepgram_transcription(websocket, model)
        elif provider == 'speechmatics':
            await speechmatics_transcription(websocket)
        else:
            await websocket.send_json({'type': 'error', 'message': f'Unknown provider: {provider}'})

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected")
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        error_msg = str(e)
        try:
            # Send detailed error to browser
            await websocket.send_json({
                'type': 'error',
                'message': error_msg,
                'details': f'Provider: {provider}'
            })
        except Exception as send_err:
            logger.error(f"Failed to send error to client: {send_err}")
            pass


async def deepgram_transcription(client_ws: WebSocket, model='nova-2'):
    """
    Connect to Deepgram and proxy between client and Deepgram
    """
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not set")

    # Get menu keyterms for boosting (if available)
    try:
        from saeed_balti.bot.saeed_balti_menu import get_top_priority_keyterms
        keyterms = get_top_priority_keyterms()
        logger.info(f"✅ Loaded {len(keyterms)} menu keyterms for boosting")
    except ImportError:
        logger.warning("⚠️ saeed_balti module not found - using default keyterms")
        keyterms = [
            "chicken tikka", "chicken tikka masala", "jalfrezi", "korma", "rogan josh",
            "vindaloo", "madras", "biryani", "tandoori", "naan", "samosa", "bhaji",
            "poppadom", "chutney", "raita", "lassi", "mango", "lamb", "paneer", "saag"
        ]

    # Build Deepgram WebSocket URL - START SIMPLE (no keywords for testing)
    params = f"model={model}&language=en-GB&punctuate=true&smart_format=true&interim_results=true&encoding=linear16&sample_rate=16000"

    # TODO: Add keywords back after basic connection works
    # # Add keyterms for Nova-2 (with intensity)
    # if model == 'nova-2':
    #     for keyterm in keyterms:
    #         encoded_keyterm = quote(keyterm)
    #         params += f"&keywords={encoded_keyterm}:3"
    # else:
    #     # Nova-3 uses 'keyterm' parameter (no intensity)
    #     for keyterm in keyterms:
    #         encoded_keyterm = quote(keyterm)
    #         params += f"&keyterm={encoded_keyterm}"

    dg_url = f"wss://api.deepgram.com/v1/listen?{params}"

    logger.info(f"🔗 Connecting to Deepgram ({model})...")
    logger.info(f"📋 Full URL: {dg_url}")
    logger.info(f"🔑 Using API key: {api_key[:20]}...")

    try:
        async with websockets.connect(
            dg_url,
            extra_headers={'Authorization': f'Token {api_key}'}
        ) as dg_ws:
            logger.info("✅ Connected to Deepgram")

            # Send initial keepalive
            await dg_ws.send(json.dumps({'type': 'KeepAlive'}))

            # Task to forward audio from client to Deepgram
            async def forward_audio():
                try:
                    while True:
                        # Receive binary audio from client (PCM Int16)
                        audio_data = await client_ws.receive_bytes()
                        if audio_data:
                            # Forward to Deepgram
                            await dg_ws.send(audio_data)
                except WebSocketDisconnect:
                    logger.info("Client disconnected during audio forwarding")
                except Exception as e:
                    logger.error(f"Audio forwarding error: {e}")

            # Task to forward transcripts from Deepgram to client
            async def forward_transcripts():
                try:
                    async for message in dg_ws:
                        data = json.loads(message)

                        # Extract transcript
                        if 'channel' in data:
                            alternatives = data['channel'].get('alternatives', [])
                            if alternatives:
                                transcript = alternatives[0].get('transcript', '')
                                is_final = data.get('is_final', False)

                                if transcript:
                                    # Apply phonetic resolver to fix menu terms (if available)
                                    try:
                                        from saeed_balti.bot.menu_phonetic_resolver import resolve_menu_phrase
                                        corrected_transcript = resolve_menu_phrase(transcript)
                                    except ImportError:
                                        # No phonetic resolver available - use original transcript
                                        corrected_transcript = transcript

                                    # Send to client
                                    await client_ws.send_json({
                                        'type': 'transcript',
                                        'text': corrected_transcript,
                                        'is_final': is_final,
                                        'provider': f'deepgram-{model}',
                                        'original': transcript if corrected_transcript != transcript else None
                                    })

                                    if corrected_transcript != transcript:
                                        logger.info(f"🔧 Corrected: '{transcript}' → '{corrected_transcript}'")

                                    logger.info(f"📝 {'[FINAL]' if is_final else '[interim]'} {corrected_transcript}")
                except Exception as e:
                    logger.error(f"Transcript forwarding error: {e}")

            # Run both tasks concurrently
            await asyncio.gather(
                forward_audio(),
                forward_transcripts()
            )
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"❌ Deepgram rejected connection: HTTP {e.status_code}")
        logger.error(f"📋 Response headers: {e.headers}")
        logger.error(f"📋 URL was: {dg_url}")
        # Try to get error body
        error_body = "No error body available"
        try:
            if hasattr(e, 'response_body'):
                error_body = e.response_body
        except:
            pass
        logger.error(f"📋 Error body: {error_body}")
        raise Exception(f"Deepgram error: HTTP {e.status_code} - {error_body}")
    except Exception as e:
        logger.error(f"❌ Deepgram connection error: {e}")
        raise


async def speechmatics_transcription(client_ws: WebSocket):
    """
    Connect to Speechmatics and proxy between client and Speechmatics
    """
    api_key = os.getenv('SPEECHMATICS_API_KEY')
    if not api_key:
        raise Exception("SPEECHMATICS_API_KEY not set")

    sm_url = "wss://eu2.rt.speechmatics.com/v2/en"

    logger.info("🔗 Connecting to Speechmatics...")

    async with websockets.connect(sm_url) as sm_ws:
        logger.info("✅ Connected to Speechmatics")

        # Start recognition
        await sm_ws.send(json.dumps({
            "message": "StartRecognition",
            "audio_format": {
                "type": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000
            },
            "transcription_config": {
                "language": "en",
                "enable_partials": True,
                "max_delay": 3.0
            },
            "authentication": {
                "type": "token",
                "token": api_key
            }
        }))

        # Forward audio
        async def forward_audio():
            try:
                while True:
                    audio_data = await client_ws.receive_bytes()
                    if audio_data:
                        # Add audio message
                        await sm_ws.send(json.dumps({
                            "message": "AddAudio",
                            "audio": audio_data.hex()  # Hex encode binary
                        }))
            except WebSocketDisconnect:
                logger.info("Client disconnected during audio forwarding")
            except Exception as e:
                logger.error(f"Audio forwarding error: {e}")

        # Forward transcripts
        async def forward_transcripts():
            try:
                async for message in sm_ws:
                    data = json.loads(message)

                    if data['message'] in ['AddPartialTranscript', 'AddTranscript']:
                        transcript = data.get('metadata', {}).get('transcript', '')
                        is_final = data['message'] == 'AddTranscript'

                        if transcript:
                            await client_ws.send_json({
                                'type': 'transcript',
                                'text': transcript,
                                'is_final': is_final,
                                'provider': 'speechmatics'
                            })

                            logger.info(f"📝 {'[FINAL]' if is_final else '[interim]'} {transcript}")

            except Exception as e:
                logger.error(f"Transcript forwarding error: {e}")

        await asyncio.gather(
            forward_audio(),
            forward_transcripts()
        )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("live_transcription_server:app", host='0.0.0.0', port=5003, reload=True)
