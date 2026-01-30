"""
Live transcription server using Pipecat's Deepgram service
Based on Pipecat's proven examples
"""
import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

from pipecat.services.deepgram.stt import DeepgramSTTService, LiveOptions, Language
from pipecat.frames.frames import AudioRawFrame, TranscriptionFrame, Frame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

load_dotenv(override=True)

app = FastAPI(title="Live Transcription Server (Pipecat)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebSocketTranscriptSender(FrameProcessor):
    """Sends transcripts back to the WebSocket client"""

    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            # Send transcript to browser
            await self.websocket.send_json({
                'type': 'transcript',
                'text': frame.text,
                'is_final': True,  # Pipecat's TranscriptionFrame is always final
                'provider': 'deepgram-pipecat',
                'timestamp': frame.timestamp if hasattr(frame, 'timestamp') else None
            })
            logger.info(f"📝 [FINAL] {frame.text}")

        # Push frame through
        await self.push_frame(frame, direction)


@app.websocket("/ws/transcribe")
async def transcribe(websocket: WebSocket):
    """WebSocket endpoint for live transcription"""
    await websocket.accept()
    logger.info("🎙️ Client connected")

    try:
        # Send ready signal
        await websocket.send_json({
            'type': 'connected',
            'provider': 'deepgram-pipecat',
            'status': 'ready'
        })

        # Create Deepgram STT service using Pipecat's proven implementation
        api_key = os.getenv('DEEPGRAM_API_KEY')
        if not api_key:
            raise Exception("DEEPGRAM_API_KEY not set")

        logger.info(f"🔑 Using API key: {api_key[:20]}...")

        stt = DeepgramSTTService(
            api_key=api_key,
            live_options=LiveOptions(
                model="nova-2",
                language=Language.EN_GB,
                punctuate=True,
                smart_format=True,
                interim_results=True,
                encoding="linear16",
                sample_rate=16000,
                channels=1,
            )
        )

        # Create WebSocket sender
        transcript_sender = WebSocketTranscriptSender(websocket)

        # Start the STT service
        await stt.start()
        logger.info("✅ Deepgram service started")

        # Process audio from WebSocket
        try:
            while True:
                # Receive binary audio from client (PCM Int16, 16kHz, mono)
                audio_data = await websocket.receive_bytes()

                if audio_data:
                    # Create Pipecat audio frame
                    audio_frame = AudioRawFrame(
                        audio=audio_data,
                        sample_rate=16000,
                        num_channels=1
                    )

                    # Process through STT service
                    async for frame in stt.process_frame(audio_frame, FrameDirection.DOWNSTREAM):
                        # Forward transcripts to WebSocket
                        await transcript_sender.process_frame(frame, FrameDirection.DOWNSTREAM)

        except WebSocketDisconnect:
            logger.info("🔌 Client disconnected")
        except Exception as e:
            logger.error(f"❌ Error processing audio: {e}")
            await websocket.send_json({'type': 'error', 'message': str(e)})
        finally:
            await stt.stop()
            logger.info("✅ STT service stopped")

    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        try:
            await websocket.send_json({'type': 'error', 'message': str(e)})
        except:
            pass


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5004, reload=False)
