from telegram import ReplyKeyboardMarkup, KeyboardButton

CHANCE_ORDER = ["Manque", "Pari", "Rosso", "Nero", "Dispari", "Passe"]

def build_keyboard():
    keyboard = []
    for row in range(0, 37, 6):
        keyboard.append([KeyboardButton(str(i)) for i in range(row, min(row + 6, 37))])
    keyboard.append([KeyboardButton("⏪ Annulla ultima"), KeyboardButton("✅ Analizza")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def build_chance_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(ch)] for ch in CHANCE_ORDER] + [[KeyboardButton("✅ Conferma")]],
        resize_keyboard=True
    )
