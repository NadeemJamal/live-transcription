# Keywords API Guide for Base44
## Control Menu Keywords for Better Recognition

---

## Overview

Base44 can now **control which keywords are used** for each transcription session. This allows you to:

✅ **Choose preset keyword lists** (top 20, top 50, all menu items)
✅ **Use custom keyword lists** (specific to your needs)
✅ **Control loading time** (fewer keywords = faster startup)
✅ **View available keywords** organized by menu category

---

## API Endpoints

### 1. Get All Keywords

**GET** `/api/keywords`

Returns all currently active keywords (menu + custom).

**Response:**
```json
{
  "keywords": ["chicken tikka masala", "lamb rogan josh", ...],
  "menu_keywords": 109,
  "custom_keywords": 5,
  "total": 114
}
```

**Example:**
```javascript
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords');
const data = await response.json();
console.log(`Total keywords: ${data.total}`);
```

---

### 2. Get Menu Keywords by Category

**GET** `/api/keywords/menu`

Returns menu keywords organized by category (starters, mains, etc.).

**Response:**
```json
{
  "success": true,
  "categories": {
    "starters": ["Tandoori King Prawn", "Onion Bhaji", ...],
    "chef_specialities": ["Bangla Fish", "Butter Chicken", ...],
    "curry_styles": ["Balti", "Bhuna", "Madras", ...],
    "biryanis": ["Chicken Tikka Biryani", ...],
    "rice": ["Pilau Rice", "Boiled Rice", ...],
    "naans": ["Garlic Naan", "Peshwari Naan", ...],
    ...
  },
  "total_items": 109
}
```

**Example:**
```javascript
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords/menu');
const data = await response.json();

// Get all naan items
const naanItems = data.categories.naans;
console.log('Naan options:', naanItems);
```

---

### 3. Get Keyword Presets

**GET** `/api/keywords/presets`

Returns predefined keyword sets with different performance characteristics.

**Response:**
```json
{
  "presets": {
    "top_20": {
      "name": "Top 20 (Fast)",
      "description": "Most common items - fastest loading (~5 seconds)",
      "keywords": ["chicken tikka masala", "lamb rogan josh", ...],
      "count": 20,
      "load_time": "~5 seconds"
    },
    "top_50": {
      "name": "Top 50 (Balanced)",
      "description": "Extended coverage - moderate loading (~10 seconds)",
      "keywords": [...],
      "count": 50,
      "load_time": "~10 seconds"
    },
    "all": {
      "name": "All Menu Items (Complete)",
      "description": "Complete menu coverage - slower loading (~15 seconds)",
      "keywords": [...],
      "count": 109,
      "load_time": "~15 seconds"
    }
  }
}
```

**Example:**
```javascript
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords/presets');
const data = await response.json();

// Show user the preset options
const presets = data.presets;
console.log('Available presets:');
for (const [key, preset] of Object.entries(presets)) {
    console.log(`${preset.name}: ${preset.count} keywords, ${preset.load_time}`);
}
```

---

## Using Keywords in Transcription

### Option 1: Use Preset (Recommended)

```javascript
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',

    // Use a preset
    keywords: 'top_20',  // Fast loading, most common items

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            console.log('Order:', transcript.text);
        }
    }
});
```

**Preset Options:**
- `'top_20'` - 20 most common items (~5 second load)
- `'top_50'` - 50 popular items (~10 second load)
- `'all'` - All 109+ menu items (~15 second load)
- `'none'` - No keywords (fastest, but less accurate)

---

### Option 2: Custom Keyword List

```javascript
// Fetch presets first
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords/presets');
const data = await response.json();

// Get specific keywords you want
const myKeywords = [
    'chicken tikka masala',
    'lamb rogan josh',
    'garlic naan',
    'pilau rice'
];

const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'deepgram',

    // Pass custom comma-separated list
    keywords: myKeywords.join(','),

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            console.log('Order:', transcript.text);
        }
    }
});
```

---

### Option 3: Build Keyword List from User's Order History

```javascript
// Get user's favorite items from order history
const userFavorites = getUserFavoriteItems(); // Your function
// Returns: ['chicken tikka masala', 'garlic naan', 'pilau rice']

// Fetch top 20 preset as base
const response = await fetch('https://live-transcription-production.up.railway.app/api/keywords/presets');
const presets = await response.json();
const top20 = presets.presets.top_20.keywords;

// Combine: user favorites + top 20 (remove duplicates)
const customKeywords = [...new Set([...userFavorites, ...top20])];

const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',
    keywords: customKeywords.join(','),
    onTranscript: handleOrder
});
```

---

### Option 4: Dynamic Keywords Based on Time of Day

```javascript
async function getKeywordsForTimeOfDay() {
    const hour = new Date().getHours();

    // Lunch menu (11am-3pm)
    if (hour >= 11 && hour < 15) {
        return 'top_20';  // Fast service for lunch rush
    }

    // Dinner menu (5pm-10pm)
    if (hour >= 17 && hour < 22) {
        return 'top_50';  // More options for dinner
    }

    // Off-peak
    return 'all';  // All options available
}

const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',
    keywords: await getKeywordsForTimeOfDay(),
    onTranscript: handleOrder
});
```

---

## Performance vs Accuracy Trade-offs

| Keywords | Count | Load Time | Accuracy | Best For |
|----------|-------|-----------|----------|----------|
| `none` | 0 | Instant | Lower | Testing only |
| `top_20` | 20 | ~5 sec | Good | Fast service, popular items |
| `top_50` | 50 | ~10 sec | Better | Balanced service |
| `all` | 109+ | ~15 sec | Best | Complete menu coverage |
| Custom | Varies | Varies | Varies | Specific use cases |

---

## Complete Integration Example

```javascript
// 1. Show user the loading message
showLoadingMessage('Preparing voice ordering...');

// 2. Fetch available presets (optional - show user choices)
const presetsResponse = await fetch('https://live-transcription-production.up.railway.app/api/keywords/presets');
const presetsData = await presetsResponse.json();

// 3. Let user choose (or pick automatically)
const userChoice = await askUser('Choose keyword set:', [
    { label: 'Fast (20 keywords)', value: 'top_20' },
    { label: 'Balanced (50 keywords)', value: 'top_50' },
    { label: 'Complete (all items)', value: 'all' }
]);

// 4. Start transcription with chosen keywords
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',
    keywords: userChoice,

    onTranscript: (transcript) => {
        if (transcript.isFinal) {
            // Process customer's order
            parseOrder(transcript.text);
            addToCart(transcript.text);
            showConfirmation(transcript.text);
        } else {
            // Show live preview
            showLiveTranscript(transcript.text);
        }
    },

    onStatusChange: (status) => {
        if (status.connected && status.recording) {
            hideLoadingMessage();
            showListeningIndicator();
        }
    },

    onError: (error) => {
        showError(`Voice ordering failed: ${error}`);
    }
});

// 5. Stop when order is complete
document.getElementById('finish-order-btn').onclick = () => {
    transcription.stopRecording();
    transcription.disconnect();
    processOrder();
};
```

---

## Recommended Strategy for Base44

### For Production Use:

1. **Start with `top_20`** for fastest experience
2. **Collect analytics** on what items customers order
3. **Build custom keyword list** based on popular items
4. **Update periodically** based on seasonal menu changes

### Example Implementation:

```javascript
// Monthly: Analyze order data
const topOrderedItems = analyzeLastMonthOrders(); // Your analytics
// Returns: ['chicken tikka masala', 'lamb rogan josh', ...]

// Store in Base44 config
const base44Config = {
    voiceOrderingKeywords: topOrderedItems.slice(0, 30)  // Top 30 items
};

// Use for all voice orders
const transcription = await startTranscription({
    serverUrl: 'wss://live-transcription-production.up.railway.app',
    provider: 'speechmatics',
    keywords: base44Config.voiceOrderingKeywords.join(','),
    maxDelay: 3.0,
    onTranscript: processVoiceOrder
});
```

---

## Testing Different Keyword Sets

```javascript
// Test helper function
async function testKeywordSet(keywordSet) {
    console.log(`Testing keyword set: ${keywordSet}`);

    const startTime = Date.now();

    const transcription = await startTranscription({
        serverUrl: 'wss://live-transcription-production.up.railway.app',
        provider: 'speechmatics',
        keywords: keywordSet,

        onStatusChange: (status) => {
            if (status.connected && status.recording) {
                const loadTime = Date.now() - startTime;
                console.log(`${keywordSet} loaded in ${loadTime}ms`);
            }
        },

        onTranscript: (t) => {
            if (t.isFinal) {
                console.log(`[${keywordSet}] Final:`, t.text);
            }
        }
    });

    return transcription;
}

// Run tests
await testKeywordSet('top_20');
await testKeywordSet('top_50');
await testKeywordSet('all');
```

---

## FAQ

### Q: What if I don't specify keywords?
**A:** Defaults to `'all'` (all menu items)

### Q: Can I update keywords mid-session?
**A:** No, you need to disconnect and reconnect with new keywords

### Q: Do custom keywords persist?
**A:** Keywords added via `/api/keywords/add` persist globally. Query parameter keywords are session-only.

### Q: Which is faster - Deepgram or Speechmatics with keywords?
**A:** Deepgram has faster initialization with keywords. Speechmatics has 5-15 second delay for large keyword lists.

### Q: Can I use different keywords for different providers?
**A:** Yes, both providers support the keywords parameter

---

## Summary

✅ **3 keyword presets** available (top_20, top_50, all)
✅ **Custom keyword lists** via comma-separated strings
✅ **API endpoints** to view and manage keywords
✅ **Performance control** - fewer keywords = faster startup
✅ **Works with both** Deepgram and Speechmatics

**Recommendation:** Start with `keywords: 'top_20'` for production!

---

## Quick Reference

```javascript
// Fastest (5 seconds)
keywords: 'top_20'

// Balanced (10 seconds)
keywords: 'top_50'

// Complete (15 seconds)
keywords: 'all'

// No keywords (instant, less accurate)
keywords: 'none'

// Custom list
keywords: 'chicken tikka masala,lamb rogan josh,garlic naan'
```
