/**
 * Order Parser - Extract menu items and quantities from speech
 *
 * Usage:
 *   const parser = new OrderParser();
 *
 *   onTranscript: (transcript) => {
 *       if (transcript.isFinal) {
 *           parser.addWord(transcript.text);
 *
 *           const items = parser.getMatches();
 *           items.forEach(item => {
 *               addToCart(item.name, item.quantity);
 *           });
 *       }
 *   }
 */

class OrderParser {
    constructor() {
        this.buffer = [];
        this.maxBufferSize = 10; // Keep last 10 words

        // Filler words to ignore
        this.fillerWords = new Set([
            'can', 'you', 'please', 'give', 'me', 'get', 'have',
            'want', 'like', 'order', 'and', 'with', 'of', 'the',
            'a', 'an', 'some', 'would', 'could', 'may', 'i', 'id',
            'to', 'for', 'also', 'plus', 'um', 'uh', 'er'
        ]);

        // Number words to quantities
        this.numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            '6': 6, '7': 7, '8': 8, '9': 9, '10': 10
        };

        // Top 20 menu items (matches server keywords preset)
        this.menuItems = [
            { keywords: ['chicken', 'tikka', 'masala'], name: 'Chicken Tikka Masala', minMatch: 2 },
            { keywords: ['chicken', 'tikka'], name: 'Chicken Tikka', minMatch: 2 },
            { keywords: ['lamb', 'tikka'], name: 'Lamb Tikka', minMatch: 2 },
            { keywords: ['butter', 'chicken'], name: 'Butter Chicken', minMatch: 2 },
            { keywords: ['chicken', 'korma'], name: 'Chicken Korma', minMatch: 2 },
            { keywords: ['lamb', 'rogan', 'josh'], name: 'Lamb Rogan Josh', minMatch: 2 },
            { keywords: ['garlic', 'naan'], name: 'Garlic Naan', minMatch: 2 },
            { keywords: ['pilau', 'rice'], name: 'Pilau Rice', minMatch: 2 },
            { keywords: ['onion', 'bhaji'], name: 'Onion Bhaji', minMatch: 2 },
            { keywords: ['tandoori', 'chicken'], name: 'Tandoori Chicken', minMatch: 2 },
            { keywords: ['chicken', 'biryani'], name: 'Chicken Biryani', minMatch: 2 },
            { keywords: ['lamb', 'biryani'], name: 'Lamb Biryani', minMatch: 2 },
            { keywords: ['madras'], name: 'Chicken Madras', minMatch: 1 },
            { keywords: ['vindaloo'], name: 'Chicken Vindaloo', minMatch: 1 },
            { keywords: ['korma'], name: 'Chicken Korma', minMatch: 1 },
            { keywords: ['balti'], name: 'Chicken Balti', minMatch: 1 },
            { keywords: ['poppadoms'], name: 'Poppadoms', minMatch: 1 },
            { keywords: ['samosa'], name: 'Samosa', minMatch: 1 },
            { keywords: ['naan'], name: 'Plain Naan', minMatch: 1 },
            { keywords: ['rice'], name: 'Pilau Rice', minMatch: 1 }
        ];

        this.matches = [];
    }

    /**
     * Add a word from speech recognition
     */
    addWord(word) {
        if (!word) return;

        const cleanWord = word.toLowerCase().trim();

        // Ignore filler words
        if (this.fillerWords.has(cleanWord)) {
            console.log(`[Parser] Ignored filler: "${word}"`);
            return;
        }

        // Add to buffer
        this.buffer.push(cleanWord);

        // Keep buffer size limited
        if (this.buffer.length > this.maxBufferSize) {
            this.buffer.shift();
        }

        console.log(`[Parser] Buffer: [${this.buffer.join(', ')}]`);

        // Try to match menu items
        this.tryMatch();
    }

    /**
     * Try to match menu items from current buffer
     */
    tryMatch() {
        for (const item of this.menuItems) {
            const matchCount = this.countMatches(item.keywords);

            if (matchCount >= item.minMatch) {
                // Found a match!
                const quantity = this.extractQuantity();

                const match = {
                    name: item.name,
                    quantity: quantity,
                    matchedWords: item.keywords.filter(k => this.buffer.includes(k))
                };

                console.log(`[Parser] ✅ Matched: ${match.quantity}x ${match.name}`);

                this.matches.push(match);

                // Clear buffer after match
                this.buffer = [];

                return match;
            }
        }

        return null;
    }

    /**
     * Count how many keywords from item are in buffer
     */
    countMatches(keywords) {
        let count = 0;
        for (const keyword of keywords) {
            if (this.buffer.includes(keyword)) {
                count++;
            }
        }
        return count;
    }

    /**
     * Extract quantity from buffer (looks for numbers before menu item)
     */
    extractQuantity() {
        for (const word of this.buffer) {
            if (this.numbers[word]) {
                return this.numbers[word];
            }
        }
        return 1; // Default to 1
    }

    /**
     * Get all matched items and clear
     */
    getMatches() {
        const result = [...this.matches];
        this.matches = [];
        return result;
    }

    /**
     * Clear buffer and matches
     */
    clear() {
        this.buffer = [];
        this.matches = [];
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrderParser;
}
