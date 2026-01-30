# Frontend Configuration Guide
## Control Transcription Timing & Behavior

---

## Overview

Your frontend can **fully control transcription timing and behavior** by passing configuration parameters to the `LiveTranscription` class.

---

## Available Parameters

### Timing Control

| Parameter | Type | Default | Description | Applies To |
|-----------|------|---------|-------------|------------|
| `maxDelay` | float | 5.0 | Seconds before finalizing transcript | Speechmatics |
| `enableBuffering` | bool | false | Enable client-side buffering for Speechmatics word-by-word finals | Client-side (Speechmatics only) |
| `bufferFlushDelay` | int | 2500 | Milliseconds before flushing display buffer (only if enableBuffering=true) | Client-side (Speechmatics display) |

### Feature Control

| Parameter | Type | Default | Description | Applies To |
|-----------|------|---------|-------------|------------|
| `interimResults` | bool | true | Enable live/interim transcripts | Both providers |
| `punctuate` | bool | true | Enable automatic punctuation | Both providers |
| `smartFormat` | bool | true | Enable smart formatting (e.g., "5 dollars" → "$5") | Deepgram only |

### Connection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `serverUrl` | string | (Railway URL) | WebSocket server URL |
| `provider` | string | 'deepgram' | STT provider: 'deepgram' or 'speechmatics' |

---

## Usage Examples

### Example 1: Fast Responses (Restaurant Ordering)

**Use case:** Customer ordering food - need quick responses

```javascript
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',

    // FAST TIMING
    maxDelay: 2.0,              // Finalize after 2 seconds (default: 5.0)
    bufferFlushDelay: 800,      // Show after 0.8 seconds (default: 1500ms)

    interimResults: true,       // Show live preview
    punctuate: true,

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            console.log('Quick response:', transcript.text);
            processOrder(transcript.text);
        }
    }
});
```

**Result:** Transcripts finalize quickly, good for short commands like "chicken tikka masala"

---

### Example 2: Longer Sentences (Detailed Instructions)

**Use case:** Customer giving detailed dietary requirements or complex orders

```javascript
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',

    // PATIENT TIMING
    maxDelay: 8.0,              // Wait 8 seconds before finalizing
    bufferFlushDelay: 2500,     // Wait 2.5 seconds before displaying

    interimResults: true,
    punctuate: true,

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            console.log('Complete sentence:', transcript.text);
            processLongOrder(transcript.text);
        }
    }
});
```

**Result:** Allows customer to speak longer sentences without premature finalization

---

### Example 3: Final-Only (No Live Preview)

**Use case:** Simple UI that only shows confirmed transcripts

```javascript
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'deepgram',

    // FINAL ONLY
    interimResults: false,      // Disable live preview
    maxDelay: 3.0,
    punctuate: true,
    smartFormat: true,

    onTranscript: (transcript) => {
        // Will only receive final transcripts
        console.log('Final only:', transcript.text);
        addToCart(transcript.text);
    }
});
```

**Result:** Only confirmed final transcripts, no live preview as customer speaks

---

### Example 4: Raw Text (No Formatting)

**Use case:** You want to do your own text processing

```javascript
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'deepgram',

    // NO FORMATTING
    punctuate: false,           // No punctuation
    smartFormat: false,         // No smart formatting
    interimResults: true,

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            // Raw text without formatting
            const rawText = transcript.text;
            const processed = myCustomProcessor(rawText);
            console.log('Processed:', processed);
        }
    }
});
```

**Result:** Raw text like "chicken tikka masala" instead of "Chicken tikka masala."

---

### Example 5: Ultra-Responsive (Drive-Through Style)

**Use case:** Fast-paced environment where speed is critical

```javascript
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'deepgram',  // Deepgram is slightly faster

    // ULTRA FAST
    maxDelay: 1.0,              // Finalize after 1 second
    bufferFlushDelay: 500,      // Show after 0.5 seconds
    interimResults: true,
    punctuate: true,
    smartFormat: true,

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            console.log('Ultra-fast:', transcript.text);
            quickAddToOrder(transcript.text);
        }
    }
});
```

**Result:** Nearly instant finalization, good for single-item orders

---

## Parameter Tuning Guide

### `maxDelay` (Speechmatics only)

**What it does:** How long to wait before finalizing a transcript

| Value | Behavior | Best For |
|-------|----------|----------|
| 1.0-2.0s | Very fast finalization | Short commands, single items |
| 3.0-5.0s | Balanced (default) | Normal conversation |
| 6.0-10.0s | Patient, waits for complete thoughts | Long sentences, complex orders |

**Example:**
```javascript
maxDelay: 2.0  // "chicken tikka" → finalizes quickly
maxDelay: 8.0  // "I would like chicken tikka masala with extra spice and no onions" → waits for complete sentence
```

---

### `enableBuffering` (Client-side, Speechmatics only)

**What it does:** Controls whether Speechmatics word-by-word finals are buffered and combined into phrases

| Value | Behavior | Best For |
|-------|----------|----------|
| `false` (default) | Pass through every word immediately | Real-time display, word-by-word processing |
| `true` | Buffer words and combine into phrases | Cleaner UI, phrase-level processing |

**Default:** `false` (no buffering, pass through immediately)

**When to enable buffering:**
- ✅ You want to show complete phrases instead of individual words
- ✅ Your UI processes transcripts at phrase level
- ✅ You're okay with a short delay before displaying (bufferFlushDelay)

**When to disable buffering (default):**
- ✅ You want real-time word-by-word display
- ✅ You want to process each word immediately
- ✅ You want the fastest possible response

---

### `bufferFlushDelay` (Client-side, Speechmatics display)

**What it does:** How long to wait before displaying accumulated words in UI

**Only applies when `enableBuffering: true`**

| Value | Behavior | Best For |
|-------|----------|----------|
| 500-800ms | Shows very quickly | Fast-paced, short commands |
| 1000-1500ms | Balanced | Normal continuous speech |
| 2000-3000ms | Patient (default) | Natural pauses between words |
| 3000-4000ms | Very patient | Slow/deliberate speech |

**Default:** Automatically set to 50% of `maxDelay` (e.g., maxDelay=5.0s → bufferFlushDelay=2500ms)

**Note:** This is **display-only**, doesn't affect when transcripts finalize

---

### `interimResults`

**What it does:** Enable/disable live preview as customer speaks

```javascript
interimResults: true   // Show "I would like..." as they speak
interimResults: false  // Only show complete: "I would like chicken tikka masala"
```

**Recommendation:** Keep `true` for better UX - shows the system is listening

---

### `punctuate`

**What it does:** Add punctuation to transcripts

```javascript
punctuate: true   // "I would like chicken tikka masala."
punctuate: false  // "i would like chicken tikka masala"
```

**Recommendation:** Keep `true` unless you need raw text

---

### `smartFormat` (Deepgram only)

**What it does:** Apply smart formatting rules

```javascript
smartFormat: true   // "5 dollars" → "$5", "January 1st" → "January 1st"
smartFormat: false  // "five dollars", "january first"
```

**Recommendation:** Keep `true` for better readability

---

## Dynamic Configuration

You can change configuration mid-session:

```javascript
// Start with fast timing
const transcription = await startTranscription({
    provider: 'speechmatics',
    maxDelay: 2.0,
    onTranscript: handleTranscript
});

// Later: switch to patient timing for complex order
await transcription.changeProvider('speechmatics'); // Reconnects
// Or manually disconnect and reconnect with new config

transcription.disconnect();

const newTranscription = await startTranscription({
    provider: 'speechmatics',
    maxDelay: 8.0,  // Now wait longer
    onTranscript: handleTranscript
});
```

---

## Recommended Configurations by Use Case

### 🍕 Fast Food / Drive-Through
```javascript
{
    provider: 'deepgram',
    maxDelay: 1.5,
    bufferFlushDelay: 600,
    interimResults: true,
    punctuate: true
}
```

### 🍽️ Sit-Down Restaurant
```javascript
{
    provider: 'speechmatics',
    maxDelay: 4.0,
    bufferFlushDelay: 1200,
    interimResults: true,
    punctuate: true
}
```

### 📱 Mobile App
```javascript
{
    provider: 'deepgram',
    maxDelay: 3.0,
    bufferFlushDelay: 1000,
    interimResults: true,
    punctuate: true,
    smartFormat: true
}
```

### 🎤 Dictation / Long-Form
```javascript
{
    provider: 'speechmatics',
    maxDelay: 10.0,
    bufferFlushDelay: 2500,
    interimResults: true,
    punctuate: true
}
```

### 🖥️ Desktop / Kiosk
```javascript
{
    provider: 'deepgram',
    maxDelay: 2.5,
    bufferFlushDelay: 1000,
    interimResults: true,
    punctuate: true,
    smartFormat: true
}
```

---

## Testing Different Configurations

```javascript
// Test function to try different configs
async function testConfig(config) {
    console.log('Testing config:', config);

    const transcription = await startTranscription({
        serverUrl: 'wss://live-transcription-production.up.railway.app',
        ...config,
        onTranscript: (t) => {
            if (t.isFinal) {
                console.log(`[${config.maxDelay}s delay] Final:`, t.text);
            }
        }
    });

    return transcription;
}

// Try different max_delay values
await testConfig({ provider: 'speechmatics', maxDelay: 2.0 });
await testConfig({ provider: 'speechmatics', maxDelay: 5.0 });
await testConfig({ provider: 'speechmatics', maxDelay: 8.0 });
```

---

## Summary

✅ **Full frontend control** over timing and behavior
✅ **No server changes needed** - just pass parameters
✅ **Works immediately** - server accepts query parameters
✅ **Test easily** - change values and see results
✅ **Tune per use case** - fast food vs. complex orders

**Key parameters to tune:**
- `maxDelay`: How long to wait before finalizing (1-10 seconds)
- `bufferFlushDelay`: How long to wait before displaying (500-3000ms)
- `interimResults`: Show live preview or not

**Start with defaults, then adjust based on user testing!**

---

## Quick Reference

```javascript
// Default (balanced)
maxDelay: 5.0
bufferFlushDelay: 1500
interimResults: true
punctuate: true
smartFormat: true

// Fast (quick responses)
maxDelay: 2.0
bufferFlushDelay: 800

// Patient (long sentences)
maxDelay: 8.0
bufferFlushDelay: 2500

// Final-only (no live preview)
interimResults: false
```
