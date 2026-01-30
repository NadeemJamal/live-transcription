"""
Simple live transcription server using Deepgram SDK and Speechmatics
Deployed on Railway with multi-provider support
"""
import os
import asyncio
import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
import websockets

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

load_dotenv(override=True)

app = FastAPI(title="Live Transcription Server (Multi-Provider)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Menu keywords for boosting
MENU_KEYWORDS = [
    "chicken tikka", "chicken tikka masala", "tikka masala", "jalfrezi",
    "korma", "rogan josh", "vindaloo", "madras", "biryani", "tandoori",
    "naan", "samosa", "bhaji", "onion bhaji", "poppadom", "chutney",
    "raita", "lassi", "mango", "lamb", "paneer", "saag", "balti",
    "pathia", "dhansak", "dopiaza", "pasanda", "keema", "chicken",
    "lamb rogan josh", "chicken korma", "lamb korma", "chicken madras",
    "lamb vindaloo", "chicken jalfrezi", "lamb bhuna", "prawn",
    "king prawn", "garlic naan", "peshwari naan", "pilau rice"
]


async def handle_deepgram(websocket: WebSocket):
    """Handle Deepgram transcription"""
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not set")

    logger.info(f"🔑 Using Deepgram API key: {api_key[:20]}...")

    # Create Deepgram client
    config = DeepgramClientOptions(
        options={"keepalive": "true"}
    )
    deepgram = DeepgramClient(api_key, config)

    # Create WebSocket connection to Deepgram
    dg_connection = deepgram.listen.asyncwebsocket.v("1")

    # Event handlers
    async def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) > 0:
            is_final = result.is_final
            await websocket.send_json({
                'type': 'transcript',
                'text': sentence,
                'is_final': is_final,
                'provider': 'deepgram'
            })
            logger.info(f"📝 [Deepgram] {'[FINAL]' if is_final else '[interim]'} {sentence}")

    async def on_error(self, error, **kwargs):
        logger.error(f"❌ Deepgram error: {error}")
        await websocket.send_json({'type': 'error', 'message': str(error)})

    async def on_open(self, open, **kwargs):
        logger.info("✅ Connected to Deepgram")

    async def on_close(self, close, **kwargs):
        logger.info("🔌 Deepgram connection closed")

    # Register event handlers
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)
    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)

    # Configure Deepgram options with keyword boosting
    options = LiveOptions(
        model="nova-2",
        language="en-GB",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        punctuate=True,
        smart_format=True,
        interim_results=True,
        keywords=MENU_KEYWORDS,
    )

    # Start Deepgram connection
    if not await dg_connection.start(options):
        raise Exception("Failed to connect to Deepgram")

    logger.info("🎙️ Ready to receive audio (Deepgram)")

    # Process audio from browser
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            if audio_data and len(audio_data) > 0:
                await dg_connection.send(audio_data)

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected")
    except Exception as e:
        logger.error(f"❌ Error processing audio: {e}")
        await websocket.send_json({'type': 'error', 'message': str(e)})
    finally:
        await dg_connection.finish()
        logger.info("✅ Deepgram connection closed")


async def handle_speechmatics(websocket: WebSocket):
    """Handle Speechmatics transcription"""
    api_key = os.getenv('SPEECHMATICS_API_KEY')
    if not api_key:
        raise Exception("SPEECHMATICS_API_KEY not set")

    logger.info(f"🔑 Using Speechmatics API key: {api_key[:20]}...")

    # Speechmatics WebSocket URL
    sm_url = "wss://eu2.rt.speechmatics.com/v2/en"

    logger.info("🔗 Connecting to Speechmatics...")

    # Add Authorization header with API key
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    async with websockets.connect(sm_url, extra_headers=headers) as sm_ws:
        logger.info("✅ Connected to Speechmatics")

        # Start recognition session
        start_recognition = {
            "message": "StartRecognition",
            "audio_format": {
                "type": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000
            },
            "transcription_config": {
                "language": "en",
                "enable_partials": True,
                "max_delay": 2.0,
                "additional_vocab": MENU_KEYWORDS,
                "enable_entities": False
            }
        }

        await sm_ws.send(json.dumps(start_recognition))
        logger.info("🎙️ Speechmatics session started")

        # Task to forward audio from client to Speechmatics
        async def forward_audio():
            try:
                while True:
                    audio_data = await websocket.receive_bytes()
                    if audio_data and len(audio_data) > 0:
                        # Speechmatics expects base64 encoded audio in JSON message
                        audio_message = {
                            "message": "AddAudio",
                            "audio": base64.b64encode(audio_data).decode('utf-8')
                        }
                        await sm_ws.send(json.dumps(audio_message))
            except WebSocketDisconnect:
                logger.info("🔌 Client disconnected")
                # Send EndOfStream
                await sm_ws.send(json.dumps({"message": "EndOfStream"}))
            except Exception as e:
                logger.error(f"❌ Audio forwarding error: {e}")

        # Task to forward transcripts from Speechmatics to client
        async def forward_transcripts():
            try:
                async for message in sm_ws:
                    data = json.loads(message)
                    msg_type = data.get('message')

                    if msg_type == 'AddPartialTranscript':
                        # Interim transcript
                        transcript = data.get('metadata', {}).get('transcript', '')
                        if transcript:
                            await websocket.send_json({
                                'type': 'transcript',
                                'text': transcript,
                                'is_final': False,
                                'provider': 'speechmatics'
                            })
                            logger.info(f"📝 [Speechmatics] [interim] {transcript}")

                    elif msg_type == 'AddTranscript':
                        # Final transcript
                        transcript = data.get('metadata', {}).get('transcript', '')
                        if transcript:
                            await websocket.send_json({
                                'type': 'transcript',
                                'text': transcript,
                                'is_final': True,
                                'provider': 'speechmatics'
                            })
                            logger.info(f"📝 [Speechmatics] [FINAL] {transcript}")

                    elif msg_type == 'Error':
                        error_msg = data.get('reason', 'Unknown error')
                        logger.error(f"❌ Speechmatics error: {error_msg}")
                        await websocket.send_json({'type': 'error', 'message': error_msg})

                    elif msg_type == 'RecognitionStarted':
                        logger.info("✅ Speechmatics recognition started")

            except Exception as e:
                logger.error(f"❌ Transcript forwarding error: {e}")

        # Run both tasks concurrently
        await asyncio.gather(
            forward_audio(),
            forward_transcripts()
        )


@app.websocket("/ws/transcribe")
async def transcribe(
    websocket: WebSocket,
    provider: str = Query(default="deepgram", description="STT provider: deepgram or speechmatics")
):
    """WebSocket endpoint for live transcription with multi-provider support"""
    await websocket.accept()
    logger.info(f"🎙️ Client connected - Provider: {provider}")

    try:
        # Send ready signal
        await websocket.send_json({
            'type': 'connected',
            'provider': provider,
            'status': 'ready'
        })

        # Route to appropriate provider
        # Handle provider variants (deepgram-nova2, deepgram-nova3, etc.)
        if provider.startswith("deepgram"):
            await handle_deepgram(websocket)
        elif provider == "speechmatics":
            await handle_speechmatics(websocket)
        else:
            raise Exception(f"Unknown provider: {provider}")

    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({'type': 'error', 'message': str(e)})
        except:
            pass


if __name__ == '__main__':
    import uvicorn
    # Use PORT from environment (Railway) or default to 5005
    port = int(os.getenv('PORT', 5005))
    uvicorn.run(app, host='0.0.0.0', port=port, reload=False)
