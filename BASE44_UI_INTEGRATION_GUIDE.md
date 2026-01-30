# Base44 UI Team - Integration Guide
## How to Add Voice Ordering

---

## Quick Start (Copy & Paste)

### Step 1: Include the Library

Add this to your HTML:

```html
<script src="https://nadeemjamal.github.io/live-transcription/base44_simple_example.js"></script>
```

### Step 2: Add Voice Ordering Button

```html
<button id="voice-order-btn">🎤 Start Voice Order</button>
<div id="voice-status"></div>
<div id="transcripts"></div>
```

### Step 3: Add JavaScript (Recommended Settings)

```javascript
let transcription = null;

document.getElementById('voice-order-btn').onclick = async () => {
    if (!transcription) {
        // Start voice ordering
        transcription = await startTranscription({
            serverUrl: 'wss://live-transcription-production.up.railway.app',
            provider: 'speechmatics',
            keywords: 'top_20',         // Fast loading (5 seconds)
            maxDelay: 3.0,              // Quick responses

            onTranscript: (transcript) => {
                if (transcript.isFinal) {
                    // Customer said something - add to order
                    const word = transcript.text;
                    console.log('Customer said:', word);

                    // YOUR CODE: Process the word
                    addToOrder(word);

                    // Show in UI
                    document.getElementById('transcripts').innerHTML += word + ' ';
                }
            },

            onStatusChange: (status) => {
                if (status.recording) {
                    document.getElementById('voice-status').textContent = '🔴 Listening...';
                } else {
                    document.getElementById('voice-status').textContent = '⚪ Not listening';
                }
            },

            onError: (error) => {
                alert('Voice ordering error: ' + error);
            }
        });

        document.getElementById('voice-order-btn').textContent = '⏹️ Stop Voice Order';

    } else {
        // Stop voice ordering
        transcription.stopRecording();
        transcription.disconnect();
        transcription = null;

        document.getElementById('voice-order-btn').textContent = '🎤 Start Voice Order';
    }
};
```

**That's it!** Voice ordering is now working.

---

## What Your Code Needs to Do

### 1. Process Each Word

Speechmatics sends **one word at a time** (like the test page you saw working):

```javascript
onTranscript: (transcript) => {
    if (transcript.isFinal) {
        const word = transcript.text;

        // Examples of what you'll receive:
        // - "chicken"
        // - "tikka"
        // - "masala"
        // - "garlic"
        // - "naan"

        // YOUR CODE: Check if word matches menu item
        if (isMenuItem(word)) {
            addToCart(word);
        }

        // OR build a phrase and check periodically
        currentPhrase += word + ' ';
        if (matchesMenuItem(currentPhrase)) {
            addToCart(currentPhrase);
            currentPhrase = '';
        }
    }
}
```

### 2. Match Against Menu

You'll need to match words/phrases against your menu:

```javascript
function addToOrder(text) {
    const lowerText = text.toLowerCase();

    // Check menu items
    if (lowerText.includes('chicken tikka')) {
        cart.add('Chicken Tikka Masala');
        showConfirmation('Added: Chicken Tikka Masala');
    }
    else if (lowerText === 'naan' || lowerText.includes('garlic naan')) {
        cart.add('Garlic Naan');
        showConfirmation('Added: Garlic Naan');
    }
    // ... etc
}
```

### 3. Show User Feedback

```javascript
onTranscript: (transcript) => {
    if (transcript.isFinal) {
        // Show what customer said
        showUserMessage(transcript.text);

        // Try to process it
        const result = processOrder(transcript.text);

        if (result.matched) {
            showSuccess(`Added: ${result.item}`);
        } else {
            // Customer said something we don't understand
            showHelp('Try saying: chicken tikka, garlic naan, pilau rice');
        }
    } else {
        // Interim - show live preview
        showLivePreview(transcript.text);
    }
}
```

---

## Important Settings Explained

### `keywords: 'top_20'`

This tells the system to focus on the 20 most common menu items:
- Fast loading (~5 seconds)
- Better accuracy for popular items
- Good for 80% of orders

**Options:**
- `'top_20'` - 20 items, ~5 sec load (recommended)
- `'top_50'` - 50 items, ~10 sec load
- `'all'` - 109 items, ~15 sec load
- `'none'` - No keywords, instant (less accurate)

### `maxDelay: 3.0`

How long Speechmatics waits before finalizing a word:
- `2.0` - Very fast (good for single words like "naan")
- `3.0` - Balanced (recommended)
- `5.0` - Patient (good for slow speakers)

### `provider: 'speechmatics'`

Which speech-to-text service to use:
- `'speechmatics'` - What we tested, works well
- `'deepgram'` - Alternative, slightly faster

---

## Complete Working Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voice Ordering</title>
    <script src="https://nadeemjamal.github.io/live-transcription/base44_simple_example.js"></script>
    <style>
        #voice-order-btn { padding: 20px; font-size: 18px; }
        #voice-status { margin: 10px; font-weight: bold; }
        #transcripts { padding: 20px; background: #f5f5f5; margin: 10px; }
        .item-added { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Voice Ordering</h1>
    <button id="voice-order-btn">🎤 Start Voice Order</button>
    <div id="voice-status">⚪ Not listening</div>
    <div id="transcripts"></div>
    <div id="cart"></div>

    <script>
        let transcription = null;
        let cart = [];
        let currentPhrase = '';

        document.getElementById('voice-order-btn').onclick = async () => {
            if (!transcription) {
                // Start
                transcription = await startTranscription({
                    serverUrl: 'wss://live-transcription-production.up.railway.app',
                    provider: 'speechmatics',
                    keywords: 'top_20',
                    maxDelay: 3.0,

                    onTranscript: (t) => {
                        if (t.isFinal) {
                            processWord(t.text);
                        }
                    },

                    onStatusChange: (status) => {
                        document.getElementById('voice-status').textContent =
                            status.recording ? '🔴 Listening...' : '⚪ Not listening';
                    },

                    onError: (error) => alert('Error: ' + error)
                });

                document.getElementById('voice-order-btn').textContent = '⏹️ Stop';

            } else {
                // Stop
                transcription.stopRecording();
                transcription.disconnect();
                transcription = null;
                document.getElementById('voice-order-btn').textContent = '🎤 Start Voice Order';
            }
        };

        function processWord(word) {
            console.log('Word:', word);

            // Add to phrase
            currentPhrase += word + ' ';

            // Show what we heard
            document.getElementById('transcripts').innerHTML += word + ' ';

            // Check if we have a menu item
            const phrase = currentPhrase.toLowerCase().trim();

            if (phrase.includes('chicken tikka masala') ||
                (phrase.includes('chicken') && phrase.includes('tikka') && phrase.includes('masala'))) {
                addToCart('Chicken Tikka Masala');
                currentPhrase = '';
            }
            else if (phrase.includes('garlic naan') ||
                     (phrase.includes('garlic') && phrase.includes('naan'))) {
                addToCart('Garlic Naan');
                currentPhrase = '';
            }
            else if (phrase.includes('pilau rice') || phrase.includes('rice')) {
                addToCart('Pilau Rice');
                currentPhrase = '';
            }
            // Add more menu items...
        }

        function addToCart(item) {
            cart.push(item);
            document.getElementById('cart').innerHTML =
                '<div class="item-added">✅ Added: ' + item + '</div>' +
                '<h3>Cart:</h3>' + cart.join('<br>');
        }
    </script>
</body>
</html>
```

---

## What Users Will Experience

1. **Click "Start Voice Order"**
   - Browser asks for microphone permission
   - Wait ~5 seconds for system to load
   - See "🔴 Listening..."

2. **Customer speaks: "Chicken tikka masala"**
   - System hears: "chicken" "tikka" "masala"
   - Each word appears on screen as they speak
   - Your code matches "chicken tikka masala" → adds to cart
   - Show confirmation: "✅ Added: Chicken Tikka Masala"

3. **Customer continues: "And garlic naan"**
   - System hears: "and" "garlic" "naan"
   - Your code matches "garlic naan" → adds to cart
   - Show confirmation: "✅ Added: Garlic Naan"

4. **Click "Stop"**
   - Recording stops
   - Show final order for confirmation

---

## Testing

### Test Locally First

1. Copy the complete example above
2. Save as `test.html`
3. Open in Chrome
4. Click "Start Voice Order"
5. Say: "chicken tikka masala"
6. Check if words appear and get matched

### Test on Your Site

1. Add the library to your existing Base44 page
2. Add voice order button
3. Connect the `onTranscript` callback to your existing order processing
4. Test with real menu items

---

## Common Issues & Solutions

### Issue: Nothing happens when I click Start

**Solution:** Check browser console (F12) for errors. Make sure:
- Script is loaded: `https://nadeemjamal.github.io/live-transcription/base44_simple_example.js`
- Browser has microphone permission
- Server URL is correct

### Issue: Words are missing

**Solution:** Use `keywords: 'top_20'` instead of `'all'` for better performance

### Issue: Wrong words recognized

**Solution:**
- Make sure keywords include your menu items
- Use `keywords: 'top_50'` for more coverage
- Train customers: "Say items like: chicken tikka, garlic naan"

### Issue: Too slow

**Solution:** Reduce `maxDelay` to 2.0 for faster finalization

---

## Production Checklist

Before going live:

- [ ] Test with 10+ different menu items
- [ ] Test with different accents
- [ ] Test in noisy environment
- [ ] Add error handling (microphone denied, network error)
- [ ] Add visual feedback (listening animation)
- [ ] Add confirmation before finalizing order
- [ ] Add "Did you mean...?" for unclear items
- [ ] Add text fallback if voice doesn't work
- [ ] Test on mobile (iOS Safari, Android Chrome)
- [ ] Test on different browsers (Chrome, Firefox, Safari)

---

## Support

**Test Page:** https://live-transcription-production.up.railway.app/test

**Documentation:**
- FRONTEND_CONFIGURATION_GUIDE.md - All parameters
- KEYWORDS_API_GUIDE.md - Keyword management
- BASE44_INTEGRATION_BRIEF.md - Technical details

**Need Help?**
Check browser console for errors and test with the raw test page first to isolate issues.

---

## Summary for Your Team

**Tell them:**

1. "Include this script: `https://nadeemjamal.github.io/live-transcription/base44_simple_example.js`"

2. "Call `startTranscription()` with these settings:
   - `provider: 'speechmatics'`
   - `keywords: 'top_20'`
   - `maxDelay: 3.0`"

3. "In `onTranscript` callback, you'll receive words one at a time - match them against the menu and add to cart"

4. "Test at: https://live-transcription-production.up.railway.app/test to see how it works"

**That's it!** The system is ready to use.
