from telegram import ReplyKeyboardMarkup

def main_menu_keyboard(is_admin: bool = False):
    buttons = [
        ["/set_bankroll", "/primi15", "/modalita_inserimento"],
        ["/report", "/storic o", "/annulla_ultima"],
        ["/help", "/id", "/end_session"]
    ]
    if is_admin:
        buttons.append(["/admin"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def number_keyboard():
    nums = [str(i) for i in range(0,37)]
    kb = [nums[i:i+6] for i in range(0, 36, 6)]
    kb.append(["Annulla", "Menu"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)