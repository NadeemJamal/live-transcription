"""
Saeed Balti Restaurant Menu Data
Complete menu with categories, prices, and metadata
"""

MENU = {
    "starters": {
        "2x Poppadoms": {"price": 1.50, "allergens": []},
        "Tandoori King Prawn": {"price": 5.95, "allergens": ["Milk", "Crustaceans"]},
        "King Prawn Butterfly": {"price": 5.95, "allergens": ["Egg", "Crustaceans"]},
        "Mixed Kebabs": {"price": 4.95, "allergens": ["Egg", "Milk"]},
        "Tandoori Chicken (Starter)": {"price": 3.95, "allergens": ["Milk"]},
        "Lamb Tikka (Starter)": {"price": 3.95, "allergens": ["Milk"]},
        "Chicken Tikka (Starter)": {"price": 3.95, "allergens": ["Milk"]},
        "Onion Bhaji": {"price": 3.25, "allergens": ["Egg"]},
        "Prawn On Puri": {"price": 4.75, "allergens": ["Crustaceans", "Gluten"]},
        "King Prawn On Puri": {"price": 5.75, "allergens": ["Crustaceans", "Gluten"]},
        "Shami Kebabs": {"price": 3.95, "allergens": ["Egg"]},
        "Keema Samosa": {"price": 3.25, "allergens": ["Egg"]},
        "Vegetable Samosa": {"price": 3.25, "allergens": ["Egg"]},
        "Chicken Tikka Pakora": {"price": 3.95, "allergens": ["Milk"]},
        "Chicken Chat": {"price": 3.95, "allergens": ["Milk"]},
        "Chana Aloo Chat": {"price": 3.50, "allergens": []},
        "Mixed Combo": {"price": 4.95, "allergens": ["Egg", "Gluten"]},
        "Paneer Chilli": {"price": 4.95, "allergens": ["Milk"]},
        "Lamb Chops (Starter)": {"price": 5.75, "allergens": ["Milk"]},
        "Chicken Stir Fry": {"price": 4.25, "allergens": ["Milk"]},
    },

    "chef_specialities": {
        "Bangla Fish": {"price": 9.95, "protein": "fish"},
        "Tandoori Garlic Chilli Chicken": {"price": 8.95, "protein": "chicken"},
        "Chicken Tikka Rezala": {"price": 8.95, "protein": "chicken"},
        "Chicken Tikka Pasanda": {"price": 8.95, "protein": "chicken"},
        "Begum Bahar": {"price": 8.95, "protein": "chicken"},
        "Butter Chicken": {"price": 8.95, "protein": "chicken"},
        "Chicken Tikka Patia": {"price": 8.95, "protein": "chicken"},
        "Chicken Tikka Ponnir": {"price": 8.95, "protein": "chicken"},
        "Bombay Sweet Chilli Chicken": {"price": 8.95, "protein": "chicken"},
        "Saeed's Special Balti": {"price": 8.95, "protein": "mixed"},
        "Chicken Tikka Naga": {"price": 8.95, "protein": "chicken"},
        "Lamb Tikka Naga": {"price": 8.95, "protein": "lamb"},
        "Chicken Tikka Sagwala": {"price": 8.95, "protein": "chicken"},
        "Lamb Tikka Sagwala": {"price": 8.95, "protein": "lamb"},
        "Chicken Tikka Rajastani": {"price": 8.95, "protein": "chicken"},
        "Lamb Tikka Rajastani": {"price": 8.95, "protein": "lamb"},
        "Chicken Tikka Nairal": {"price": 8.95, "protein": "chicken"},
        "Mango Chicken": {"price": 8.95, "protein": "chicken"},
        "Lamb Chops Bhuna": {"price": 11.95, "protein": "lamb"},
        "Quorn Dansak": {"price": 9.95, "protein": "quorn"},
    },

    "tandoori_dishes": {
        "Machli Shashlik": {"price": 10.95, "protein": "fish"},
        "Tandoori Mixed Kebab": {"price": 9.50, "protein": "mixed"},
        "Chicken Tikka (Main)": {"price": 8.95, "protein": "chicken"},
        "Lamb Tikka (Main)": {"price": 8.95, "protein": "lamb"},
        "Tandoori King Prawns": {"price": 11.95, "protein": "king_prawn"},
        "Special Tandoori Mixed Grill": {"price": 11.50, "protein": "mixed"},
        "Chicken Shashlik": {"price": 9.95, "protein": "chicken"},
        "Lamb Shashlik": {"price": 9.95, "protein": "lamb"},
        "Tandoori Chicken (Half)": {"price": 9.95, "protein": "chicken"},
        "Lamb Chops": {"price": 11.95, "protein": "lamb"},
    },

    "curry_styles": {
        "Balti": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Bhuna": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Curry": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Madras": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Chilli": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Masala": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Vindaloo": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Phall": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Dansak": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Rogan": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
        "Korma": {"chicken": 7.95, "lamb": 8.50, "prawn": 9.50, "king_prawn": 11.95, "vegetable": 6.95},
    },

    "biryanis": {
        "Chicken Tikka Biryani": {"price": 10.50},
        "Tandoori Chicken Biryani": {"price": 10.95},
        "Chicken Biryani": {"price": 9.25},
        "Lamb Biryani": {"price": 9.50},
        "Prawn Biryani": {"price": 9.95},
        "King Prawn Biryani": {"price": 12.95},
        "Special Mix Biryani": {"price": 12.50},
        "Vegetable Biryani": {"price": 8.50},
        "Quorn Biryani": {"price": 11.25},
    },

    "rice": {
        "Pilau Rice": {"price": 2.95},
        "Boiled Rice": {"price": 2.50},
        "Vegetable Rice": {"price": 3.25},
        "Mushroom Rice": {"price": 3.25},
        "Egg Fried Rice": {"price": 3.25},
        "Special Fried Rice": {"price": 3.50},
        "Chicken Tikka Fried Rice": {"price": 4.95},
        "Keema Rice": {"price": 4.25},
        "Garlic Fried Rice": {"price": 3.25},
        "Coconut Rice": {"price": 3.50},
        "Lemon Rice": {"price": 3.50},
    },

    "naans": {
        "Plain Naan": {"price": 2.50},
        "Garlic Naan": {"price": 3.25},
        "Peshwari Naan": {"price": 3.25},
        "Keema Naan": {"price": 3.50},
        "Cheese Naan": {"price": 3.50},
        "Garlic & Coriander Naan": {"price": 3.25},
        "Paratha": {"price": 2.95},
        "Stuffed Paratha": {"price": 3.25},
        "Keema & Cheese Naan": {"price": 4.25},
        "Tikka Naan": {"price": 3.50},
        "Chappati": {"price": 2.50},
        "Garlic Cheese Naan": {"price": 3.95},
        "Special Naan": {"price": 4.50},
    },

    "vegetable_sides": {
        "Aloo Gobi": {"price": 4.25},
        "Bombay Aloo": {"price": 4.25},
        "Bhindi Bhajee": {"price": 4.25},
        "Baigun Bhajee": {"price": 4.25},
        "Tarka Dhal": {"price": 4.25},
        "Chana Bhajee": {"price": 4.25},
        "Saag Aloo": {"price": 4.25},
        "Garlic Mushroom": {"price": 4.25},
        "Saag Ponnir": {"price": 4.25},
    },

    "drinks": {
        "Coke (Can)": {"price": 1.50},
        "Coke Zero (Can)": {"price": 1.50},
        "Fanta (Can)": {"price": 1.50},
        "Sprite": {"price": 1.50},
        "Rio": {"price": 1.50},
        "Water": {"price": 1.50},
    }
}

RESTAURANT_INFO = {
    "name": "Saeed Balti",
    "location": "Quedgeley, GL1",
    "cuisine": "Indian",
    "hours": "5:00 PM – 10:30 PM"
}

# STT Recognition Terms - For vocabulary boosting ONLY
# These items are NOT on the menu, but help Deepgram recognize customer requests
# so the bot can politely inform customers when items aren't available

STT_RECOGNITION_CURRY_STYLES = [
    "Jalfrezi",        # Spicy with peppers and onions
    "Pathia",          # Sweet and sour
    "Patia",           # Alternate spelling of Pathia
    "Dopiaza",         # Double onion
    "Ceylon",          # Coconut based
    "Kashmir",         # Fruity, mild
    "Tikka Masala",    # Common way customers say it (we have "Masala")
    "Saag",            # Spinach (we have "Sagwala")
    "Lamb Madras",     # Popular dish combination
]

STT_RECOGNITION_EXTRAS = [
    # Common variations of menu items
    "Paneer",          # Cheese curry (we spell it "Ponnir")
    "Naan Bread",      # Customers say "naan bread" (we have "naan")
    "Pilau",           # Alternate spelling of Pilau

    # Common misheard items
    "Gel Crazy",       # Misheard Jalfrezi
    "Chicken Gel",     # Partial misheard Jalfrezi
]

# Combine all STT recognition terms
STT_RECOGNITION_TERMS = STT_RECOGNITION_CURRY_STYLES + STT_RECOGNITION_EXTRAS

def get_curry_price(style, protein):
    """Get price for curry style with specific protein"""
    if style in MENU["curry_styles"]:
        return MENU["curry_styles"][style].get(protein, 0)
    return 0

def format_price(price):
    """Format price in GBP"""
    return f"£{price:.2f}"


def extract_menu_keyterms(prioritize_dishes=True):
    """
    Extract keyterms from menu for STT boosting.

    Returns complete list of menu items for vocabulary boosting.

    Args:
        prioritize_dishes: If True, prioritize chef specialities and complex names

    Returns:
        list: Menu items as keyterms for Deepgram
    """
    keyterms = []

    # High priority: Chef specialities (complex multi-word items)
    if prioritize_dishes:
        for item_name in MENU["chef_specialities"].keys():
            keyterms.append(item_name)
        for item_name in MENU["tandoori_dishes"].keys():
            keyterms.append(item_name)
        for item_name in MENU["biryanis"].keys():
            keyterms.append(item_name)

    # Starters with complex names
    for item_name in MENU["starters"].keys():
        if len(item_name.split()) > 1:
            keyterms.append(item_name)

    # Curry styles
    for style_name in MENU["curry_styles"].keys():
        keyterms.append(style_name)

    # Rice and naan varieties
    for item_name in MENU["rice"].keys():
        keyterms.append(item_name)
    for item_name in MENU["naans"].keys():
        keyterms.append(item_name)

    # Vegetable sides
    for item_name in MENU["vegetable_sides"].keys():
        keyterms.append(item_name)

    # Common proteins
    keyterms.extend([
        "chicken", "lamb", "prawn", "king prawn",
        "vegetable", "quorn", "fish", "paneer"
    ])

    # Common modifiers
    keyterms.extend([
        "tikka", "tandoori", "masala", "korma", "madras",
        "vindaloo", "balti", "bhuna", "naan", "rice",
        "garlic", "butter", "spicy", "mild"
    ])

    return keyterms


def get_top_priority_keyterms(limit=50):
    """
    Get the most important keyterms for STT boosting.
    Limited list for optimal performance.

    Includes BOTH:
    - Menu items we actually sell
    - Recognition terms for items we DON'T sell (so bot can understand requests)

    Args:
        limit: Maximum number of keyterms to return

    Returns:
        list: Top priority menu items and recognition terms
    """
    priority_items = []

    # Start with STT recognition terms (items we DON'T sell but need to recognize)
    priority_items.extend(STT_RECOGNITION_TERMS)

    # Add commonly confused menu items we DO sell
    menu_items = [
        "Chicken Tikka Masala",
        "Butter Chicken",
        "Chicken Tikka Pasanda",
        "Lamb Tikka",
        "Chicken Tikka",
        "Garlic Naan",
        "Pilau Rice",
        "Onion Bhaji",
        "Tandoori Chicken",
        "Chicken Tikka Biryani",
        "Saag Ponnir",
        "Saag Aloo",
        "Keema Naan",
        "Peshwari Naan",
        "Madras",
        "Vindaloo",
        "Korma",
        "Balti",
    ]
    priority_items.extend(menu_items)

    # Fill remaining slots with chef specialities if we have room
    for item_name in MENU["chef_specialities"].keys():
        if item_name not in priority_items and len(priority_items) < limit:
            priority_items.append(item_name)

    return priority_items[:limit]
