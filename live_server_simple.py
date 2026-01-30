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


async def handle_deepgram(websocket: WebSocket, keywords_list: List[str], interim_results: bool = True, smart_format: bool = True, punctuate: bool = True):
    """Handle Deepgram transcription"""
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not set")

    logger.info(f"🔑 Using Deepgram API key: {api_key[:20]}...")
    logger.info(f"⚙️ Deepgram config - keywords: {len(keywords_list)}, interim: {interim_results}, smart_format: {smart_format}, punctuate: {punctuate}")

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
        punctuate=punctuate,
        smart_format=smart_format,
        interim_results=interim_results,
        keywords=keywords_list if keywords_list else [],
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


async def handle_speechmatics(websocket: WebSocket, keywords_list: List[str], max_delay: float = 5.0, interim_results: bool = True):
    """Handle Speechmatics transcription"""
    api_key = os.getenv('SPEECHMATICS_API_KEY')
    if not api_key:
        raise Exception("SPEECHMATICS_API_KEY not set")

    logger.info(f"🔑 Using Speechmatics API key: {api_key[:20]}...")
    logger.info(f"⚙️ Speechmatics config - keywords: {len(keywords_list)}, max_delay: {max_delay}s, enable_partials: {interim_results}")

    # Speechmatics WebSocket URL
    sm_url = "wss://eu2.rt.speechmatics.com/v2/en"

    logger.info("🔗 Connecting to Speechmatics...")

    # Add Authorization header with API key
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    async with websockets.connect(sm_url, extra_headers=headers) as sm_ws:
        logger.info("✅ Connected to Speechmatics")

        # Format keywords for Speechmatics (requires objects with "content" field)
        speechmatics_vocab = [{"content": keyword} for keyword in keywords_list] if keywords_list else []
        logger.info(f"📋 Using {len(speechmatics_vocab)} keywords for Speechmatics")
        if keywords_list:
            logger.info(f"📋 Sample keywords: {keywords_list[:5]}")

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
                "additional_vocab": speechmatics_vocab,
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


@app.get("/api/keywords/menu")
async def get_menu_keywords():
    """Get all menu keywords organized by category"""
    try:
        from saeed_balti_menu import MENU

        categorized = {}
        for category, items in MENU.items():
            if isinstance(items, dict):
                categorized[category] = list(items.keys())

        return {
            "success": True,
            "categories": categorized,
            "total_items": len(MENU_KEYWORDS)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load menu: {str(e)}"}
        )


@app.get("/api/keywords/presets")
async def get_keyword_presets():
    """Get predefined keyword presets for different performance needs"""

    # Top priority items (fastest - ~5 second load)
    top_20 = [
        "chicken tikka masala", "chicken tikka", "lamb tikka",
        "butter chicken", "chicken korma", "lamb rogan josh",
        "garlic naan", "pilau rice", "onion bhaji",
        "tandoori chicken", "chicken biryani", "lamb biryani",
        "madras", "vindaloo", "korma", "balti",
        "poppadoms", "samosa", "naan", "rice"
    ]

    # Expanded set (moderate - ~10 second load)
    top_50 = top_20 + [
        "peshwari naan", "keema naan", "saag aloo", "tarka dhal",
        "chicken jalfrezi", "lamb bhuna", "prawn", "king prawn",
        "tikka masala", "rogan josh", "pathia", "dhansak",
        "dopiaza", "paneer", "saag paneer", "aloo gobi",
        "bombay aloo", "mushroom rice", "egg fried rice",
        "special fried rice", "boiled rice", "vegetable rice",
        "paratha", "chapati", "raita", "chutney",
        "mango chutney", "chicken tikka biryani", "mixed grill"
    ]

    # All keywords (slow - ~15 second load)
    all_keywords = list(set(MENU_KEYWORDS + CUSTOM_KEYWORDS))

    return {
        "presets": {
            "top_20": {
                "name": "Top 20 (Fast)",
                "description": "Most common items - fastest loading (~5 seconds)",
                "keywords": top_20,
                "count": len(top_20),
                "load_time": "~5 seconds"
            },
            "top_50": {
                "name": "Top 50 (Balanced)",
                "description": "Extended coverage - moderate loading (~10 seconds)",
                "keywords": top_50[:50],  # Ensure exactly 50
                "count": 50,
                "load_time": "~10 seconds"
            },
            "all": {
                "name": "All Menu Items (Complete)",
                "description": "Complete menu coverage - slower loading (~15 seconds)",
                "keywords": all_keywords,
                "count": len(all_keywords),
                "load_time": "~15 seconds"
            }
        }
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
    punctuate: bool = Query(default=True, description="Enable automatic punctuation"),
    keywords: str = Query(default="all", description="Keywords preset: 'all', 'top_20', 'top_50', 'none', or comma-separated list")
):
    """WebSocket endpoint for live transcription with multi-provider support"""
    await websocket.accept()
    logger.info(f"🎙️ Client connected - Provider: {provider}, keywords: {keywords}, max_delay: {max_delay}s, interim: {interim_results}")

    try:
        # Parse keywords parameter
        selected_keywords = []

        if keywords == "none":
            selected_keywords = []
        elif keywords == "top_20":
            selected_keywords = [
                "chicken tikka masala", "chicken tikka", "lamb tikka",
                "butter chicken", "chicken korma", "lamb rogan josh",
                "garlic naan", "pilau rice", "onion bhaji",
                "tandoori chicken", "chicken biryani", "lamb biryani",
                "madras", "vindaloo", "korma", "balti",
                "poppadoms", "samosa", "naan", "rice"
            ]
        elif keywords == "top_50":
            selected_keywords = [
                "chicken tikka masala", "chicken tikka", "lamb tikka",
                "butter chicken", "chicken korma", "lamb rogan josh",
                "garlic naan", "pilau rice", "onion bhaji",
                "tandoori chicken", "chicken biryani", "lamb biryani",
                "madras", "vindaloo", "korma", "balti",
                "poppadoms", "samosa", "naan", "rice",
                "peshwari naan", "keema naan", "saag aloo", "tarka dhal",
                "chicken jalfrezi", "lamb bhuna", "prawn", "king prawn",
                "tikka masala", "rogan josh", "pathia", "dhansak",
                "dopiaza", "paneer", "saag paneer", "aloo gobi",
                "bombay aloo", "mushroom rice", "egg fried rice",
                "special fried rice", "boiled rice", "vegetable rice",
                "paratha", "chapati", "raita", "chutney",
                "mango chutney", "chicken tikka biryani", "mixed grill"
            ]
        elif keywords == "all":
            selected_keywords = list(set(MENU_KEYWORDS + CUSTOM_KEYWORDS))
        else:
            # Custom comma-separated list
            selected_keywords = [k.strip().lower() for k in keywords.split(",") if k.strip()]

        logger.info(f"📋 Using {len(selected_keywords)} keywords")

        # Send ready signal
        await websocket.send_json({
            'type': 'connected',
            'provider': provider,
            'status': 'ready',
            'keywords_count': len(selected_keywords)
        })

        # Route to appropriate provider
        # Handle provider variants (deepgram-nova2, deepgram-nova3, etc.)
        if provider.startswith("deepgram"):
            await handle_deepgram(websocket, selected_keywords, interim_results, smart_format, punctuate)
        elif provider == "speechmatics":
            await handle_speechmatics(websocket, selected_keywords, max_delay, interim_results)
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


@app.get("/demo")
async def demo_page():
    """Demo page with sentence-level buffering"""
    from fastapi.responses import HTMLResponse

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Demo - Sentence Level (With Buffering)</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        button { padding: 15px 30px; margin: 5px; font-size: 18px; cursor: pointer; }
        #transcripts { margin-top: 20px; padding: 20px; background: #f5f5f5; border-radius: 8px; min-height: 200px; }
        .transcript { margin: 10px 0; padding: 15px; background: white; border-left: 4px solid #28a745; border-radius: 4px; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .info { background: #d1ecf1; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🎤 Sentence-Level Transcription</h1>
    <div class="info">
        <strong>How it works:</strong> Words are buffered and combined into complete sentences.
        Speak continuously, then wait 6 seconds of silence to see your sentence.
    </div>
    <p><strong>Try saying:</strong> "How are you doing today my name is Nadeem Jamal"</p>
    <div>
        <button id="start">Start (Speechmatics - Sentence Mode)</button>
        <button id="stop">Stop</button>
    </div>
    <div id="transcripts"></div>
    <script>
        let ws = null, audioContext = null, processor = null, stream = null;
        let buffer = '', bufferTimeout = null;
        const FLUSH_DELAY = 6000; // 6 seconds

        document.getElementById('start').onclick = async () => {
            const url = 'wss://live-transcription-production.up.railway.app/ws/transcribe?provider=speechmatics&keywords=top_20&max_delay=10.0';
            console.log('Connecting:', url);
            ws = new WebSocket(url);

            ws.onopen = () => console.log('✅ Connected');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'connected') startAudio();
                if (data.type === 'transcript' && data.is_final) {
                    // Buffer words
                    buffer += (buffer ? ' ' : '') + data.text;
                    console.log('Buffering:', buffer);

                    // Reset timeout
                    if (bufferTimeout) clearTimeout(bufferTimeout);
                    bufferTimeout = setTimeout(() => {
                        if (buffer.trim()) {
                            console.log('═══ SENTENCE ═══');
                            console.log(buffer.trim());
                            console.log('═══════════════');

                            const div = document.createElement('div');
                            div.className = 'transcript';
                            div.innerHTML = buffer.trim() + '<br><small>' + new Date().toLocaleTimeString() + '</small>';
                            document.getElementById('transcripts').insertBefore(div, document.getElementById('transcripts').firstChild);
                            buffer = '';
                        }
                    }, FLUSH_DELAY);
                }
            };
            ws.onerror = (err) => console.error('❌ Error:', err);
            ws.onclose = () => console.log('🔌 Disconnected');
        };

        async function startAudio() {
            console.log('🎙️ Starting audio...');
            stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }});
            audioContext = new AudioContext({ sampleRate: 16000 });
            const source = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);
            processor.onaudioprocess = (e) => {
                if (!ws || ws.readyState !== WebSocket.OPEN) return;
                const audioData = e.inputBuffer.getChannelData(0);
                const pcm = new Int16Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    const s = Math.max(-1, Math.min(1, audioData[i]));
                    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                ws.send(pcm.buffer);
            };
            source.connect(processor);
            processor.connect(audioContext.destination);
            console.log('✅ Recording... Speak now!');
        }

        document.getElementById('stop').onclick = () => {
            // Flush any remaining buffer
            if (bufferTimeout) clearTimeout(bufferTimeout);
            if (buffer.trim()) {
                const div = document.createElement('div');
                div.className = 'transcript';
                div.innerHTML = buffer.trim() + '<br><small>' + new Date().toLocaleTimeString() + '</small>';
                document.getElementById('transcripts').insertBefore(div, document.getElementById('transcripts').firstChild);
                buffer = '';
            }

            if (processor) processor.disconnect();
            if (audioContext) audioContext.close();
            if (stream) stream.getTracks().forEach(track => track.stop());
            if (ws) ws.close();
            console.log('⏸️ Stopped');
        };
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)


@app.get("/test")
async def test_page():
    """Test page with no buffering (word-by-word)"""
    from fastapi.responses import HTMLResponse

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Test - Raw Word-by-Word (No Buffering)</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        button { padding: 10px 20px; margin: 5px; font-size: 16px; }
        #transcripts { margin-top: 20px; padding: 20px; background: #f5f5f5; border-radius: 8px; min-height: 200px; }
        .transcript { margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #28a745; border-radius: 4px; }
        .interim { border-left-color: #ffc107; font-style: italic; }
    </style>
</head>
<body>
    <h1>Test - No Buffering (Raw Output)</h1>
    <p>Shows EVERY transcript as it arrives, NO buffering.</p>
    <div>
        <button id="start">Start (Speechmatics - top_20)</button>
        <button id="stop">Stop</button>
    </div>
    <div id="transcripts"></div>
    <script>
        let ws = null, audioContext = null, processor = null, stream = null;

        document.getElementById('start').onclick = async () => {
            const url = 'wss://live-transcription-production.up.railway.app/ws/transcribe?provider=speechmatics&keywords=top_20&max_delay=5.0';
            console.log('Connecting:', url);
            ws = new WebSocket(url);

            ws.onopen = () => console.log('✅ Connected');
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'connected') {
                    console.log('✅ Connected:', data);
                    startAudio();
                }

                if (data.type === 'transcript') {
                    // Log to console with actual text
                    console.log(`${data.is_final ? '🟢 FINAL' : '🟡 INTERIM'}: "${data.text}"`);

                    // Display on page
                    const div = document.createElement('div');
                    div.className = data.is_final ? 'transcript' : 'transcript interim';
                    div.innerHTML = `<strong>${data.is_final ? 'FINAL' : 'INTERIM'}</strong>: ${data.text}<br><small>${new Date().toLocaleTimeString()}</small>`;
                    document.getElementById('transcripts').insertBefore(div, document.getElementById('transcripts').firstChild);
                }
            };
            ws.onerror = (err) => console.error('❌ Error:', err);
            ws.onclose = () => console.log('🔌 Disconnected');
        };

        async function startAudio() {
            console.log('🎙️ Starting audio...');
            stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }});
            audioContext = new AudioContext({ sampleRate: 16000 });
            const source = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);
            processor.onaudioprocess = (e) => {
                if (!ws || ws.readyState !== WebSocket.OPEN) return;
                const audioData = e.inputBuffer.getChannelData(0);
                const pcm = new Int16Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    const s = Math.max(-1, Math.min(1, audioData[i]));
                    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                ws.send(pcm.buffer);
            };
            source.connect(processor);
            processor.connect(audioContext.destination);
            console.log('✅ Recording...');
        }

        document.getElementById('stop').onclick = () => {
            if (processor) processor.disconnect();
            if (audioContext) audioContext.close();
            if (stream) stream.getTracks().forEach(track => track.stop());
            if (ws) ws.close();
            console.log('⏸️ Stopped');
        };
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)


if __name__ == '__main__':
    import uvicorn
    # Use PORT from environment (Railway) or default to 5005
    port = int(os.getenv('PORT', 5005))
    uvicorn.run(app, host='0.0.0.0', port=port, reload=False)
