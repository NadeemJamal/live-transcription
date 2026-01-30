"""
Simple live transcription server using Deepgram SDK directly
Following Deepgram's official examples
"""
import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

load_dotenv(override=True)

app = FastAPI(title="Live Transcription Server (Simple)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/transcribe")
async def transcribe(websocket: WebSocket):
    """WebSocket endpoint for live transcription"""
    await websocket.accept()
    logger.info("🎙️ Client connected")

    try:
        # Send ready signal
        await websocket.send_json({
            'type': 'connected',
            'provider': 'deepgram-sdk',
            'status': 'ready'
        })

        api_key = os.getenv('DEEPGRAM_API_KEY')
        if not api_key:
            raise Exception("DEEPGRAM_API_KEY not set")

        logger.info(f"🔑 Using API key: {api_key[:20]}...")

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
                    'provider': 'deepgram-sdk'
                })
                logger.info(f"📝 {'[FINAL]' if is_final else '[interim]'} {sentence}")

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

        # Menu keywords for boosting
        menu_keywords = [
            "chicken tikka", "chicken tikka masala", "tikka masala", "jalfrezi",
            "korma", "rogan josh", "vindaloo", "madras", "biryani", "tandoori",
            "naan", "samosa", "bhaji", "onion bhaji", "poppadom", "chutney",
            "raita", "lassi", "mango", "lamb", "paneer", "saag", "balti",
            "pathia", "dhansak", "dopiaza", "pasanda", "keema", "chicken",
            "lamb rogan josh", "chicken korma", "lamb korma", "chicken madras",
            "lamb vindaloo", "chicken jalfrezi", "lamb bhuna", "prawn",
            "king prawn", "garlic naan", "peshwari naan", "pilau rice"
        ]

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
            keywords=menu_keywords,  # Add keyword boosting
        )

        # Start Deepgram connection
        if not await dg_connection.start(options):
            raise Exception("Failed to connect to Deepgram")

        logger.info("🎙️ Ready to receive audio")

        # Process audio from browser
        try:
            while True:
                # Receive binary audio from client (PCM Int16, 16kHz, mono)
                audio_data = await websocket.receive_bytes()

                if audio_data and len(audio_data) > 0:
                    # Send audio to Deepgram
                    await dg_connection.send(audio_data)

        except WebSocketDisconnect:
            logger.info("🔌 Client disconnected")
        except Exception as e:
            logger.error(f"❌ Error processing audio: {e}")
            await websocket.send_json({'type': 'error', 'message': str(e)})
        finally:
            # Clean up
            await dg_connection.finish()
            logger.info("✅ Deepgram connection closed")

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
