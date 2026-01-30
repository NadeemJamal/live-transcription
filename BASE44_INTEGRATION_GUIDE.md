# Base44 Integration Guide - Live Transcription

## Server Details

**WebSocket Endpoint**: `ws://YOUR_SERVER_IP:5001/ws/transcribe`

**Query Parameters**:
- `provider` - STT engine to use (default: `deepgram-nova2`)
  - `deepgram-nova2` - Deepgram Nova-2 with menu keyterm boosting
  - `deepgram-nova3` - Deepgram Nova-3 with menu keyterm boosting
  - `speechmatics` - Speechmatics with custom dictionary

## Quick Start - JavaScript/TypeScript

### 1. Basic Connection

```javascript
// Connect to transcription server
const ws = new WebSocket('ws://localhost:5001/ws/transcribe?provider=deepgram-nova2');

ws.onopen = () => {
    console.log('✅ Connected to transcription server');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'connected') {
        console.log(`✅ ${data.provider} ready`);
        // Start sending audio here
    }

    if (data.type === 'transcript') {
        console.log(`${data.is_final ? '[FINAL]' : '[interim]'} ${data.text}`);

        // Show correction if applied
        if (data.original) {
            console.log(`🔧 Corrected: '${data.original}' → '${data.text}'`);
        }
    }

    if (data.type === 'error') {
        console.error('❌ Error:', data.message);
    }
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = () => {
    console.log('🔌 Disconnected');
};
```

### 2. Microphone Capture & Audio Streaming

```javascript
async function startLiveTranscription(provider = 'deepgram-nova2') {
    // Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:5001/ws/transcribe?provider=${provider}`);

    await new Promise((resolve, reject) => {
        ws.onopen = resolve;
        ws.onerror = reject;
    });

    console.log('✅ WebSocket connected');

    // Capture microphone (16kHz, mono)
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

        const audioData = e.inputBuffer.getChannelData(0); // Float32Array

        // Convert Float32 to PCM Int16
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

    console.log('🎙️ Microphone active - streaming audio...');

    // Handle transcripts
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'transcript') {
            // Update UI with transcript
            displayTranscript(data.text, data.is_final, data.original);
        }
    };

    // Return cleanup function
    return () => {
        processor.disconnect();
        audioContext.close();
        stream.getTracks().forEach(track => track.stop());
        ws.close();
    };
}

// Usage
const cleanup = await startLiveTranscription('deepgram-nova2');

// Later: stop transcription
cleanup();
```

## Complete React/TypeScript Example

### Hook: `useLiveTranscription.ts`

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';

interface Transcript {
    text: string;
    isFinal: boolean;
    timestamp: Date;
    provider: string;
    original?: string; // If phonetic correction was applied
}

interface UseLiveTranscriptionOptions {
    provider?: 'deepgram-nova2' | 'deepgram-nova3' | 'speechmatics';
    serverUrl?: string;
    onTranscript?: (transcript: Transcript) => void;
    onError?: (error: string) => void;
}

export function useLiveTranscription(options: UseLiveTranscriptionOptions = {}) {
    const {
        provider = 'deepgram-nova2',
        serverUrl = 'ws://localhost:5001',
        onTranscript,
        onError
    } = options;

    const [isConnected, setIsConnected] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [transcripts, setTranscripts] = useState<Transcript[]>([]);

    const wsRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    const connect = useCallback(async () => {
        try {
            const ws = new WebSocket(`${serverUrl}/ws/transcribe?provider=${provider}`);

            ws.onopen = () => {
                console.log('✅ Connected to transcription server');
                setIsConnected(true);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'transcript') {
                    const transcript: Transcript = {
                        text: data.text,
                        isFinal: data.is_final,
                        timestamp: new Date(),
                        provider: data.provider,
                        original: data.original
                    };

                    setTranscripts(prev => [...prev, transcript]);
                    onTranscript?.(transcript);
                }

                if (data.type === 'error') {
                    onError?.(data.message);
                }
            };

            ws.onerror = () => {
                onError?.('WebSocket connection error');
                setIsConnected(false);
            };

            ws.onclose = () => {
                console.log('🔌 Disconnected');
                setIsConnected(false);
            };

            wsRef.current = ws;

        } catch (error) {
            onError?.(`Failed to connect: ${error}`);
        }
    }, [provider, serverUrl, onTranscript, onError]);

    const startRecording = useCallback(async () => {
        try {
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

            streamRef.current = stream;

            // Create audio processing pipeline
            const audioContext = new AudioContext({ sampleRate: 16000 });
            const source = audioContext.createMediaStreamSource(stream);
            const processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

                const audioData = e.inputBuffer.getChannelData(0);

                // Convert Float32 to PCM Int16
                const pcm = new Int16Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    const s = Math.max(-1, Math.min(1, audioData[i]));
                    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                // Send to WebSocket
                wsRef.current.send(pcm.buffer);
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            audioContextRef.current = audioContext;
            processorRef.current = processor;

            setIsRecording(true);
            console.log('🎙️ Recording started');

        } catch (error) {
            onError?.(`Microphone error: ${error}`);
        }
    }, [onError]);

    const stopRecording = useCallback(() => {
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }

        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        setIsRecording(false);
        console.log('🎙️ Recording stopped');
    }, []);

    const disconnect = useCallback(() => {
        stopRecording();

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setIsConnected(false);
    }, [stopRecording]);

    const clearTranscripts = useCallback(() => {
        setTranscripts([]);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        isConnected,
        isRecording,
        transcripts,
        connect,
        disconnect,
        startRecording,
        stopRecording,
        clearTranscripts
    };
}
```

### Component: `LiveTranscriptionPanel.tsx`

```typescript
import React from 'react';
import { useLiveTranscription } from './useLiveTranscription';

export function LiveTranscriptionPanel() {
    const {
        isConnected,
        isRecording,
        transcripts,
        connect,
        disconnect,
        startRecording,
        stopRecording,
        clearTranscripts
    } = useLiveTranscription({
        provider: 'deepgram-nova2',
        serverUrl: 'ws://localhost:5001',
        onTranscript: (transcript) => {
            if (transcript.isFinal) {
                console.log('Final transcript:', transcript.text);
            }
        },
        onError: (error) => {
            console.error('Transcription error:', error);
        }
    });

    return (
        <div className="live-transcription-panel">
            <h2>🎙️ Live Transcription</h2>

            <div className="controls">
                {!isConnected ? (
                    <button onClick={connect}>Connect</button>
                ) : (
                    <>
                        <button onClick={disconnect}>Disconnect</button>
                        {!isRecording ? (
                            <button onClick={startRecording}>Start Recording</button>
                        ) : (
                            <button onClick={stopRecording}>Stop Recording</button>
                        )}
                        <button onClick={clearTranscripts}>Clear</button>
                    </>
                )}
            </div>

            <div className="status">
                <span>Connection: {isConnected ? '✅ Connected' : '❌ Disconnected'}</span>
                <span>Recording: {isRecording ? '🎙️ Active' : '⏸️ Inactive'}</span>
            </div>

            <div className="transcripts">
                {transcripts.map((t, idx) => (
                    <div
                        key={idx}
                        className={`transcript ${t.isFinal ? 'final' : 'interim'}`}
                    >
                        <span className="time">
                            {t.timestamp.toLocaleTimeString()}
                        </span>
                        <span className="text">{t.text}</span>
                        {t.original && (
                            <span className="correction">
                                (corrected from: "{t.original}")
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
```

## Message Format

### Messages FROM Server (JSON)

**Connection Ready:**
```json
{
    "type": "connected",
    "provider": "deepgram-nova2",
    "status": "ready"
}
```

**Transcript (Interim):**
```json
{
    "type": "transcript",
    "text": "chicken take a",
    "is_final": false,
    "provider": "deepgram-nova-2"
}
```

**Transcript (Final):**
```json
{
    "type": "transcript",
    "text": "Chicken Tikka Masala",
    "is_final": true,
    "provider": "deepgram-nova-2"
}
```

**Transcript (With Correction):**
```json
{
    "type": "transcript",
    "text": "Jalfrezi",
    "is_final": true,
    "provider": "deepgram-nova-2",
    "original": "gel crazy"
}
```

**Error:**
```json
{
    "type": "error",
    "message": "DEEPGRAM_API_KEY not set"
}
```

### Messages TO Server (Binary)

**Audio Data:**
- Format: PCM signed 16-bit little-endian (Int16Array)
- Sample Rate: 16000 Hz
- Channels: 1 (mono)
- Encoding: linear16

## Audio Format Conversion

### Browser (JavaScript)

```javascript
// Input: Float32Array from AudioContext (range: -1.0 to 1.0)
const audioData = e.inputBuffer.getChannelData(0);

// Convert to Int16Array (range: -32768 to 32767)
const pcm = new Int16Array(audioData.length);
for (let i = 0; i < audioData.length; i++) {
    const s = Math.max(-1, Math.min(1, audioData[i]));
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
}

// Send as binary
ws.send(pcm.buffer);
```

### Deno/Node.js

```typescript
// If you have raw PCM Int16 buffer
const audioBuffer = new Int16Array(audioData);
ws.send(audioBuffer.buffer);
```

## Testing

### Test Connection Only

```javascript
const ws = new WebSocket('ws://localhost:5001/ws/transcribe?provider=deepgram-nova2');
ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
```

### Test with File Upload

```javascript
// Read audio file as ArrayBuffer
const file = document.querySelector('input[type="file"]').files[0];
const arrayBuffer = await file.arrayBuffer();
const pcmData = new Int16Array(arrayBuffer);

// Send in chunks (simulate streaming)
const chunkSize = 4096;
for (let i = 0; i < pcmData.length; i += chunkSize) {
    const chunk = pcmData.slice(i, i + chunkSize);
    ws.send(chunk.buffer);
    await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
}
```

## Troubleshooting

### WebSocket Connection Fails

**Problem**: `Error 1006` or connection timeout

**Solutions**:
1. Check server is running: `netstat -ano | findstr :5001`
2. Check firewall settings
3. Try `ws://127.0.0.1:5001` instead of `ws://localhost:5001`
4. Check CORS settings if connecting from different origin

### No Audio Detected

**Problem**: Connected but no transcripts appearing

**Solutions**:
1. Check microphone permissions in browser
2. Verify audio format: Must be PCM Int16, 16kHz, mono
3. Check browser console for errors
4. Test with test page first: `test_websocket.html`

### Incorrect Transcriptions

**Problem**: Menu items not recognized correctly

**Solutions**:
1. Try Deepgram Nova-3: `?provider=deepgram-nova3`
2. Try Speechmatics: `?provider=speechmatics`
3. Check phonetic corrections are being applied (look for `original` field)
4. Menu keyterm boosting is automatic - no config needed

### Server Crashes

**Problem**: Server stops responding

**Solutions**:
1. Check server logs in terminal
2. Restart server: `python testing_framework/webapp/live_transcription_server.py`
3. Check API keys in `.env` file

## Production Deployment

### 1. Environment Variables

Ensure these are set in `.env`:
```
DEEPGRAM_API_KEY=your_key_here
SPEECHMATICS_API_KEY=your_key_here
```

### 2. Run Server

```bash
cd C:/BlueBerryTech/VoiceAgent/Pipecat
.venv/Scripts/python.exe testing_framework/webapp/live_transcription_server.py
```

Server runs on: `http://0.0.0.0:5001`

### 3. Update Base44 URL

In Base44, change WebSocket URL to:
```
ws://YOUR_SERVER_IP:5001/ws/transcribe?provider=deepgram-nova2
```

Replace `YOUR_SERVER_IP` with actual server IP address.

## Features

✅ **Menu Keyterm Boosting** - 50 restaurant menu terms automatically boosted
✅ **Phonetic Correction** - Auto-corrects misheard menu items (e.g., "gel crazy" → "Jalfrezi")
✅ **Interim Results** - Real-time partial transcripts as user speaks
✅ **Final Results** - Complete, finalized transcripts
✅ **Multi-Provider** - Switch between Deepgram Nova-2, Nova-3, and Speechmatics
✅ **CORS Enabled** - Works with any frontend origin

## API Reference

### WebSocket Endpoint

```
ws://localhost:5001/ws/transcribe
```

**Query Parameters:**
- `provider` (optional) - STT provider to use
  - Default: `deepgram-nova2`
  - Options: `deepgram-nova2`, `deepgram-nova3`, `speechmatics`

**Example:**
```
ws://localhost:5001/ws/transcribe?provider=speechmatics
```
