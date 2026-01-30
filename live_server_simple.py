"""
Simple live transcription server using Deepgram SDK and Speechmatics
Deployed on Railway with multi-provider support
"""
import os
import asyncio
import json
import base64
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


# Load menu keywords from Saeed Balti menu
try:
    from saeed_balti_menu import MENU

    # Extract all menu item names from all categories
    menu_keywords = []
    for category, items in MENU.items():
        if isinstance(items, dict):
            menu_keywords.extend(items.keys())

    # Convert to lowercase and remove duplicates
    MENU_KEYWORDS = sorted(list(set([kw.lower() for kw in menu_keywords])))
    logger.info(f"✅ Loaded {len(MENU_KEYWORDS)} keywords from Saeed Balti menu")
    logger.info(f"📋 Sample keywords: {MENU_KEYWORDS[:5]}")
except Exception as e:
    logger.error(f"⚠️ Could not load Saeed Balti menu: {e}")
    import traceback
    traceback.print_exc()
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
    logger.warning(f"⚠️ Using {len(MENU_KEYWORDS)} default keywords")

# Store custom keywords added by users
CUSTOM_KEYWORDS = []


async def handle_deepgram(websocket: WebSocket, interim_results: bool = True, smart_format: bool = True, punctuate: bool = True):
    """Handle Deepgram transcription"""
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not set")

    logger.info(f"🔑 Using Deepgram API key: {api_key[:20]}...")
    logger.info(f"⚙️ Deepgram config - interim: {interim_results}, smart_format: {smart_format}, punctuate: {punctuate}")

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

    # Get all keywords (menu + custom)
    all_keywords = list(set(MENU_KEYWORDS + CUSTOM_KEYWORDS))

    # Configure Deepgram options with keyword boosting
    options = LiveOptions(
        model="nova-2",
        language="en-GB",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        punctuate=punctuate,
        smart_format=smart_format,
        interim_results=interim_results,
        keywords=all_keywords,
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


async def handle_speechmatics(websocket: WebSocket, max_delay: float = 5.0, interim_results: bool = True):
    """Handle Speechmatics transcription"""
    api_key = os.getenv('SPEECHMATICS_API_KEY')
    if not api_key:
        raise Exception("SPEECHMATICS_API_KEY not set")

    logger.info(f"🔑 Using Speechmatics API key: {api_key[:20]}...")
    logger.info(f"⚙️ Speechmatics config - max_delay: {max_delay}s, enable_partials: {interim_results}")

    # Speechmatics WebSocket URL
    sm_url = "wss://eu2.rt.speechmatics.com/v2/en"

    logger.info("🔗 Connecting to Speechmatics...")

    # Add Authorization header with API key
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    async with websockets.connect(sm_url, extra_headers=headers) as sm_ws:
        logger.info("✅ Connected to Speechmatics")

        # Get all keywords (menu + custom)
        all_keywords = list(set(MENU_KEYWORDS + CUSTOM_KEYWORDS))

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
                "enable_partials": interim_results,
                "max_delay": max_delay,
                "additional_vocab": all_keywords,
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
                        # Speechmatics expects raw binary audio frames (not JSON)
                        await sm_ws.send(audio_data)
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


@app.get("/api/keywords")
async def get_keywords():
    """Get all active keywords (menu + custom)"""
    all_keywords = list(set(MENU_KEYWORDS + CUSTOM_KEYWORDS))
    all_keywords.sort()
    return {
        "keywords": all_keywords,
        "menu_keywords": len(MENU_KEYWORDS),
        "custom_keywords": len(CUSTOM_KEYWORDS),
        "total": len(all_keywords)
    }


@app.post("/api/keywords/add")
async def add_keyword(keyword: str = Body(..., embed=True)):
    """Add a custom keyword for boosting"""
    keyword_lower = keyword.lower().strip()
    if not keyword_lower:
        return JSONResponse(
            status_code=400,
            content={"error": "Keyword cannot be empty"}
        )

    if keyword_lower in CUSTOM_KEYWORDS:
        return JSONResponse(
            status_code=400,
            content={"error": "Keyword already exists"}
        )

    CUSTOM_KEYWORDS.append(keyword_lower)
    logger.info(f"➕ Added custom keyword: {keyword_lower}")

    return {
        "success": True,
        "keyword": keyword_lower,
        "total_keywords": len(MENU_KEYWORDS) + len(CUSTOM_KEYWORDS)
    }


@app.delete("/api/keywords/{keyword}")
async def delete_keyword(keyword: str):
    """Delete a custom keyword"""
    keyword_lower = keyword.lower().strip()
    if keyword_lower in CUSTOM_KEYWORDS:
        CUSTOM_KEYWORDS.remove(keyword_lower)
        logger.info(f"➖ Removed custom keyword: {keyword_lower}")
        return {"success": True, "keyword": keyword_lower}
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Keyword not found in custom keywords"}
        )


@app.websocket("/ws/transcribe")
async def transcribe(
    websocket: WebSocket,
    provider: str = Query(default="deepgram", description="STT provider: deepgram or speechmatics"),
    max_delay: float = Query(default=5.0, description="Speechmatics: Max delay in seconds before finalizing (1.0-10.0)"),
    interim_results: bool = Query(default=True, description="Enable interim (partial) results"),
    smart_format: bool = Query(default=True, description="Deepgram: Enable smart formatting"),
    punctuate: bool = Query(default=True, description="Enable automatic punctuation")
):
    """WebSocket endpoint for live transcription with multi-provider support"""
    await websocket.accept()
    logger.info(f"🎙️ Client connected - Provider: {provider}, max_delay: {max_delay}s, interim: {interim_results}")

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
            await handle_deepgram(websocket, interim_results, smart_format, punctuate)
        elif provider == "speechmatics":
            await handle_speechmatics(websocket, max_delay, interim_results)
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
