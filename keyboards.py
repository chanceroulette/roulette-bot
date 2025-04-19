from telegram import ReplyKeyboardMarkup

def roulette_keyboard():
    nums = [str(i) for i in range(37)]
    rows = [nums[i:i+6] for i in range(0, 36, 6)]
    rows.append([nums[36]])
    rows.append(["Annulla", "Termina sessione", "Menu"])
    return ReplyKeyboardMarkup(rows, one_time_keyboard=True, resize_keyboard=True)

def main_menu_keyboard():
    buttons = [
        ["primi15", "modalita_inserimento"],
        ["storico", "annulla_ultima"],
        ["report", "help"],
        ["id", "admin"],
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
