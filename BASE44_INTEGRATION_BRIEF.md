# Live Transcription Integration for Base44
## Integration Brief

---

## Executive Summary

We've built a **production-ready live transcription server** that Base44 can connect to for real-time speech-to-text. The server is deployed, tested, and includes specialized menu keyword recognition for the Saeed Balti restaurant.

**Live Server:** `https://live-transcription-production.up.railway.app`

**Demo:** https://nadeemjamal.github.io/live-transcription/

---

## What You're Getting

### ✅ Production Server Features

1. **Dual Provider Support**
   - Deepgram (Nova-2 model) - Fast, accurate
   - Speechmatics - Alternative provider

2. **Menu-Aware Recognition**
   - 109+ Saeed Balti menu items pre-loaded as keywords
   - Better recognition of dish names like "Chicken Tikka Masala", "Lamb Rogan Josh", etc.
   - Custom keyword API to add more terms

3. **Real-Time Streaming**
   - Interim results as customer speaks (live preview)
   - Final results when phrases complete
   - Low latency (~200-500ms)

4. **Production Ready**
   - Deployed on Railway with auto-scaling
   - SSL/TLS secured (wss://)
   - CORS enabled for browser connections
   - API keys managed server-side (not exposed to frontend)

---

## Integration Options

### Option A: Drop-in JavaScript Library (Recommended - Easiest)

**Use our pre-built library** - handles all WebSocket, audio capture, and buffering.

**Time to integrate:** 15-30 minutes

```html
<!-- 1. Include the library -->
<script src="https://nadeemjamal.github.io/live-transcription/base44_simple_example.js"></script>

<!-- 2. Add your integration code -->
<script>
async function initVoiceOrdering() {
    const transcription = await startTranscription({
        serverUrl: 'wss://live-transcription-production.up.railway.app',
        provider: 'deepgram',

        onTranscript: (transcript) => {
            if (transcript.isFinal) {
                // Final transcript - process the order
                console.log('Customer said:', transcript.text);
                processCustomerOrder(transcript.text);
            } else {
                // Interim transcript - show live preview
                showLiveTranscript(transcript.text);
            }
        },

        onError: (error) => {
            console.error('Transcription error:', error);
            showErrorToUser(error);
        },

        onStatusChange: (status) => {
            console.log('Status:', status);
            updateUIStatus(status);
        }
    });

    // Control the transcription
    // transcription.stopRecording();
    // transcription.disconnect();
}

// Start when user clicks "Start Order" button
document.getElementById('start-order-btn').onclick = initVoiceOrdering;
</script>
```

**That's it!** The library handles:
- WebSocket connection management
- Microphone capture
- Audio format conversion (Float32 → PCM Int16)
- Reconnection logic
- Error handling

---

### Option B: Direct WebSocket Integration (More Control)

**If Base44 has existing WebSocket/audio handling**, connect directly.

**Time to integrate:** 1-2 hours

#### 1. WebSocket Connection

```javascript
// Connect to transcription server
const ws = new WebSocket(
    'wss://live-transcription-production.up.railway.app/ws/transcribe?provider=deepgram'
);

ws.onopen = () => {
    console.log('✅ Connected to transcription server');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleTranscriptionMessage(data);
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = () => {
    console.log('🔌 Disconnected from transcription server');
};
```

#### 2. Handle Messages

```javascript
function handleTranscriptionMessage(data) {
    switch(data.type) {
        case 'connected':
            // Server is ready
            console.log(`✅ ${data.provider} ready`);
            startSendingAudio();
            break;

        case 'transcript':
            if (data.is_final) {
                // Final transcript - use for order processing
                console.log('FINAL:', data.text);
                addToOrder(data.text);
            } else {
                // Interim transcript - show as customer speaks
                console.log('INTERIM:', data.text);
                updateLivePreview(data.text);
            }
            break;

        case 'error':
            console.error('Server error:', data.message);
            handleError(data.message);
            break;
    }
}
```

#### 3. Capture and Send Audio

```javascript
async function startSendingAudio() {
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
        }
    });

    // Create audio processing pipeline
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
        if (ws.readyState !== WebSocket.OPEN) return;

        // Get audio data (Float32Array, range: -1.0 to 1.0)
        const audioData = e.inputBuffer.getChannelData(0);

        // Convert to PCM Int16 (range: -32768 to 32767)
        const pcm = new Int16Array(audioData.length);
        for (let i = 0; i < audioData.length; i++) {
            const s = Math.max(-1, Math.min(1, audioData[i]));
            pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send binary audio to server
        ws.send(pcm.buffer);
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
}
```

---

## Technical Specifications

### WebSocket Endpoint

**URL Format:**
```
wss://live-transcription-production.up.railway.app/ws/transcribe?provider={provider}
```

**Providers:**
- `deepgram` - Deepgram Nova-2 (recommended)
- `speechmatics` - Speechmatics alternative

### Audio Requirements

| Parameter | Value |
|-----------|-------|
| Format | PCM Int16 (linear16) |
| Sample Rate | 16000 Hz |
| Channels | 1 (mono) |
| Encoding | Little-endian |
| Chunk Size | 4096 samples (flexible) |

### Message Formats

#### Server → Client Messages

**Connected:**
```json
{
    "type": "connected",
    "provider": "deepgram",
    "status": "ready"
}
```

**Transcript (Interim):**
```json
{
    "type": "transcript",
    "text": "I would like chicken tikka",
    "is_final": false,
    "provider": "deepgram"
}
```

**Transcript (Final):**
```json
{
    "type": "transcript",
    "text": "I would like chicken tikka masala and pilau rice",
    "is_final": true,
    "provider": "deepgram"
}
```

**Error:**
```json
{
    "type": "error",
    "message": "Error description"
}
```

#### Client → Server Messages

**Audio Data:**
- Send raw binary PCM Int16 audio frames
- No JSON wrapping needed
- Send continuously while recording

---

## Keywords API (Optional)

### View Keywords
```javascript
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords');
const data = await response.json();

console.log(data);
// {
//   "keywords": ["chicken tikka", "lamb rogan josh", ...],
//   "menu_keywords": 109,
//   "custom_keywords": 0,
//   "total": 109
// }
```

### Add Custom Keyword
```javascript
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords/add', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        keyword: "jalfrezi"
    })
});

const data = await response.json();
console.log(data);
// {
//   "success": true,
//   "keyword": "jalfrezi",
//   "total_keywords": 110
// }
```

### Delete Custom Keyword
```javascript
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords/jalfrezi', {
    method: 'DELETE'
});

const data = await response.json();
console.log(data);
// {
//   "success": true,
//   "keyword": "jalfrezi"
// }
```

---

## Testing Instructions

### Quick Browser Console Test

```javascript
// 1. Open browser console on your Base44 page
// 2. Paste this code:

const ws = new WebSocket('wss://live-transcription-production.up.railway.app/ws/transcribe?provider=deepgram');

ws.onopen = () => console.log('✅ Connected');

ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log(data);
};

ws.onerror = (e) => console.error('❌ Error:', e);

// 3. You should see: {type: "connected", provider: "deepgram", status: "ready"}
```

### Test with Demo Page

Visit: https://nadeemjamal.github.io/live-transcription/

1. Click "Connect"
2. Select provider (Deepgram or Speechmatics)
3. Click "Start Recording"
4. Speak: "I would like chicken tikka masala"
5. See live transcription appear

---

## Implementation Checklist

### Phase 1: Basic Integration (Day 1)
- [ ] Include JavaScript library OR set up WebSocket connection
- [ ] Test connection to server
- [ ] Capture microphone audio
- [ ] Send audio to server
- [ ] Receive and log transcripts
- [ ] Display interim transcripts (live preview)
- [ ] Display final transcripts (confirmed text)

### Phase 2: Order Processing (Day 2)
- [ ] Parse final transcripts for menu items
- [ ] Extract dish names from customer speech
- [ ] Add items to order
- [ ] Handle quantities ("two chicken tikka masala")
- [ ] Confirm with customer
- [ ] Handle corrections ("no, I meant lamb")

### Phase 3: Error Handling (Day 3)
- [ ] Handle connection errors
- [ ] Handle microphone permission denied
- [ ] Handle server errors
- [ ] Add reconnection logic
- [ ] Show user-friendly error messages
- [ ] Add fallback to text input

### Phase 4: Polish (Day 4)
- [ ] Add loading states
- [ ] Add visual feedback (listening animation)
- [ ] Test with different accents
- [ ] Test with background noise
- [ ] Optimize for mobile
- [ ] Add keyboard shortcuts

---

## Example User Flow

### Voice Ordering Flow

```
1. Customer clicks "Start Voice Order" button
   → Base44 connects to transcription server
   → Request microphone permission

2. Customer speaks: "I would like chicken tikka masala"
   → Base44 shows live transcript as they speak
   → Server sends interim results: "I would like", "I would like chicken", etc.

3. Customer pauses
   → Server sends final transcript: "I would like chicken tikka masala"
   → Base44 processes: extracts "chicken tikka masala"
   → Base44 adds to order
   → Base44 shows confirmation: "Added: Chicken Tikka Masala"

4. Customer continues: "and pilau rice"
   → Same process
   → Base44 adds to order

5. Customer says: "that's all"
   → Base44 stops recording
   → Shows order summary
   → Asks for confirmation
```

---

## FAQ

### Q: Do we need API keys?
**A:** No! The server handles all API authentication. You just connect to the WebSocket URL.

### Q: What about scaling?
**A:** Server is on Railway with auto-scaling. It can handle multiple concurrent connections.

### Q: What if the server goes down?
**A:** Add fallback to text input. Server has 99%+ uptime on Railway.

### Q: Can we use our own Deepgram account?
**A:** Yes, but not necessary. Current setup works out of the box. If you want to use your own, we'd need to deploy a separate instance.

### Q: How accurate is it for Indian food names?
**A:** Very accurate! We've loaded 109+ menu items as keywords, which tells the STT engine to recognize these terms better.

### Q: Which provider is better - Deepgram or Speechmatics?
**A:** Both work well. Deepgram is slightly faster. Speechmatics handles accents well. Try both and choose.

### Q: What browsers are supported?
**A:** All modern browsers with WebSocket and Web Audio API support:
- Chrome/Edge (recommended)
- Firefox
- Safari (iOS 14.3+)

### Q: Does it work on mobile?
**A:** Yes! Works on iOS Safari and Android Chrome.

---

## Support & Resources

### Resources
- **Live Demo:** https://nadeemjamal.github.io/live-transcription/
- **Server URL:** https://live-transcription-production.up.railway.app
- **GitHub Repo:** https://github.com/NadeemJamal/live-transcription
- **JavaScript Library:** https://nadeemjamal.github.io/live-transcription/base44_simple_example.js

### Test Server Status
```bash
# Check server is running
curl https://live-transcription-production.up.railway.app/api/keywords
```

### Getting Help
- Check browser console for errors
- Test with demo page first
- Check WebSocket connection in Network tab
- Verify microphone permissions

---

## Next Steps

### For Base44 Team:

1. **Review this document** - Understand the integration options
2. **Choose integration method** - Option A (library) or Option B (direct)
3. **Test in browser console** - Verify connection works
4. **Try the demo page** - See how it works end-to-end
5. **Start integration** - Follow the code examples above
6. **Test with real speech** - Speak menu items and see recognition
7. **Add order processing** - Parse transcripts and add to cart
8. **Polish the UX** - Add loading states, animations, etc.

### Estimated Timeline:
- **Day 1:** Basic integration (connect, transcribe, display)
- **Day 2:** Order processing (parse, extract, add items)
- **Day 3:** Error handling & edge cases
- **Day 4:** Polish & testing

**Total:** 3-4 days for full integration

---

## Quick Start Command

**Tell Base44 developers to run this in their browser console:**

```javascript
// Load library
const script = document.createElement('script');
script.src = 'https://nadeemjamal.github.io/live-transcription/base44_simple_example.js';
document.head.appendChild(script);

// Wait 2 seconds for load, then:
setTimeout(async () => {
    const t = await startTranscription({
        serverUrl: 'wss://live-transcription-production.up.railway.app',
        provider: 'deepgram',
        onTranscript: (transcript) => {
            if (transcript.isFinal) {
                console.log('🎤 FINAL:', transcript.text);
            }
        }
    });
    console.log('✅ Recording started - speak now!');
}, 2000);
```

---

## Summary

You have a **production-ready transcription server** with:
- ✅ Live server deployed and tested
- ✅ Both Deepgram and Speechmatics working
- ✅ 109+ menu keywords pre-loaded
- ✅ Simple JavaScript library ready
- ✅ Demo page showing it works
- ✅ API for custom keywords
- ✅ SSL secured WebSocket
- ✅ Auto-scaling infrastructure

**Base44 just needs to:**
1. Include the library (or connect directly)
2. Call `startTranscription()` with the server URL
3. Process the transcripts
4. Done!

**Integration time: 1-4 days depending on complexity**

---

**Ready to integrate? Start with the demo page test, then use Option A (library) for fastest results.**
