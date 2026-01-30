/**
 * Simple Live Transcription Integration for Base44
 *
 * Drop this into your Base44 project and call startTranscription()
 */

class LiveTranscription {
    constructor(options = {}) {
        this.serverUrl = options.serverUrl || 'ws://localhost:5001';
        this.provider = options.provider || 'deepgram-nova2';
        this.onTranscript = options.onTranscript || ((transcript) => console.log(transcript));
        this.onError = options.onError || ((error) => console.error(error));
        this.onStatusChange = options.onStatusChange || ((status) => console.log(status));

        this.ws = null;
        this.audioContext = null;
        this.processor = null;
        this.mediaStream = null;
        this.isConnected = false;
        this.isRecording = false;
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        return new Promise((resolve, reject) => {
            const url = `${this.serverUrl}/ws/transcribe?provider=${this.provider}`;
            console.log(`🔗 Connecting to ${url}...`);

            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.onStatusChange({ connected: true, recording: false });
                resolve();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'connected') {
                    console.log(`✅ ${data.provider} ready`);
                }

                if (data.type === 'transcript') {
                    this.onTranscript({
                        text: data.text,
                        isFinal: data.is_final,
                        provider: data.provider,
                        original: data.original,
                        timestamp: new Date()
                    });
                }

                if (data.type === 'error') {
                    this.onError(data.message);
                }
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.isConnected = false;
                this.onStatusChange({ connected: false, recording: false });
                this.onError('WebSocket connection error');
                reject(error);
            };

            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.isConnected = false;
                this.isRecording = false;
                this.onStatusChange({ connected: false, recording: false });
            };
        });
    }

    /**
     * Start microphone capture and streaming
     */
    async startRecording() {
        if (!this.isConnected) {
            throw new Error('Not connected to server. Call connect() first.');
        }

        try {
            console.log('🎙️ Requesting microphone access...');

            // Request microphone with specific constraints
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Create audio processing pipeline
            this.audioContext = new AudioContext({ sampleRate: 16000 });
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            this.processor.onaudioprocess = (e) => {
                if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    return;
                }

                // Get audio data (Float32Array, range: -1.0 to 1.0)
                const audioData = e.inputBuffer.getChannelData(0);

                // Convert to PCM Int16 (range: -32768 to 32767)
                const pcm = new Int16Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    const s = Math.max(-1, Math.min(1, audioData[i]));
                    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                // Send binary audio to server
                this.ws.send(pcm.buffer);
            };

            source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            this.isRecording = true;
            this.onStatusChange({ connected: true, recording: true });
            console.log('✅ Recording started - speak now!');

        } catch (error) {
            console.error('❌ Microphone error:', error);
            this.onError(`Microphone error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Stop recording
     */
    stopRecording() {
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        this.isRecording = false;
        this.onStatusChange({ connected: this.isConnected, recording: false });
        console.log('⏸️ Recording stopped');
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        this.stopRecording();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
        this.onStatusChange({ connected: false, recording: false });
        console.log('🔌 Disconnected');
    }

    /**
     * Change provider (requires reconnect)
     */
    async changeProvider(provider) {
        const wasRecording = this.isRecording;
        this.disconnect();
        this.provider = provider;
        await this.connect();
        if (wasRecording) {
            await this.startRecording();
        }
    }
}

// =============================================================================
// USAGE EXAMPLES
// =============================================================================

/**
 * Example 1: Basic Usage
 */
async function basicExample() {
    const transcription = new LiveTranscription({
        serverUrl: 'ws://localhost:5001',
        provider: 'deepgram-nova2',
        onTranscript: (transcript) => {
            console.log(`${transcript.isFinal ? '[FINAL]' : '[interim]'} ${transcript.text}`);

            // Update your UI here
            document.getElementById('transcript').textContent += transcript.text + ' ';
        },
        onError: (error) => {
            console.error('Error:', error);
        }
    });

    // Connect and start recording
    await transcription.connect();
    await transcription.startRecording();

    // Later: stop
    // transcription.stopRecording();
    // transcription.disconnect();
}

/**
 * Example 2: With UI Integration
 */
async function uiIntegratedExample() {
    let currentTranscript = '';

    const transcription = new LiveTranscription({
        serverUrl: 'ws://localhost:5001',
        provider: 'deepgram-nova2',

        onTranscript: (transcript) => {
            if (transcript.isFinal) {
                // Final transcript - add to permanent display
                const finalDiv = document.createElement('div');
                finalDiv.className = 'transcript-final';
                finalDiv.textContent = transcript.text;

                // Show correction if applied
                if (transcript.original) {
                    const correctionSpan = document.createElement('span');
                    correctionSpan.className = 'correction';
                    correctionSpan.textContent = ` (was: "${transcript.original}")`;
                    finalDiv.appendChild(correctionSpan);
                }

                document.getElementById('final-transcripts').appendChild(finalDiv);
                currentTranscript = '';
            } else {
                // Interim transcript - update preview
                currentTranscript = transcript.text;
                document.getElementById('interim-transcript').textContent = transcript.text;
            }
        },

        onStatusChange: (status) => {
            document.getElementById('status-indicator').textContent =
                status.connected ? (status.recording ? '🔴 Recording' : '✅ Connected') : '⚫ Disconnected';
        },

        onError: (error) => {
            document.getElementById('error-display').textContent = error;
        }
    });

    // Wire up buttons
    document.getElementById('connect-btn').onclick = async () => {
        await transcription.connect();
    };

    document.getElementById('start-btn').onclick = async () => {
        await transcription.startRecording();
    };

    document.getElementById('stop-btn').onclick = () => {
        transcription.stopRecording();
    };

    document.getElementById('disconnect-btn').onclick = () => {
        transcription.disconnect();
    };

    // Provider selector
    document.getElementById('provider-select').onchange = async (e) => {
        await transcription.changeProvider(e.target.value);
    };
}

/**
 * Example 3: All-in-One Start Function
 */
async function startTranscription(options = {}) {
    const {
        provider = 'deepgram-nova2',
        serverUrl = 'ws://localhost:5001',
        onTranscript = (t) => console.log(t),
        onError = (e) => console.error(e)
    } = options;

    const transcription = new LiveTranscription({
        serverUrl,
        provider,
        onTranscript,
        onError
    });

    await transcription.connect();
    await transcription.startRecording();

    return transcription; // Return instance for later control
}

// =============================================================================
// QUICK START - Copy this to your code
// =============================================================================

/*
// 1. Include this file in your HTML
<script src="base44_simple_example.js"></script>

// 2. Start transcription with one line
const transcription = await startTranscription({
    provider: 'deepgram-nova2',
    onTranscript: (t) => {
        if (t.isFinal) {
            console.log('Final:', t.text);
            // Update your UI here
        }
    }
});

// 3. Stop when done
transcription.stopRecording();
transcription.disconnect();
*/

// =============================================================================
// Export for module systems
// =============================================================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LiveTranscription, startTranscription };
}
