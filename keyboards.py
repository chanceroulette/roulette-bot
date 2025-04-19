from telegram import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard(is_admin: bool = False):
    buttons = [
        [KeyboardButton("/set_bankroll"), KeyboardButton("/primi15"), KeyboardButton("/modalita_inserimento")],
        [KeyboardButton("/report"), KeyboardButton("/storico"), KeyboardButton("/annulla_ultima")],
        [KeyboardButton("/help"), KeyboardButton("/id"), KeyboardButton("/end_session")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("/admin")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def number_keyboard():
    nums = [str(i) for i in range(0, 37)]
    kb = [nums[i:i+6] for i in range(0, 36, 6)]
    kb.append(["Annulla", "Menu"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def chances_keyboard():
    rows = [
        ["Rosso", "Nero", "Pari"],
        ["Dispari", "Manque", "Passe"],
        ["Conferma", "Menu"]
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)