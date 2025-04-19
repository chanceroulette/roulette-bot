# keyboards.py

from telegram import ReplyKeyboardMarkup

def menu_keyboard():
    return ReplyKeyboardMarkup([
        ["/help", "/menu", "/id"],
        ["/storico", "/report", "/annulla_ultima"],
        ["/primi15", "/modalita_inserimento", "/admin"],
    ], resize_keyboard=True)

def number_keyboard():
    numeri = list(map(str, range(0, 37)))
    tastiera = []

    for i in range(0, 36, 6):
        tastiera.append(numeri[i:i+6])

    tastiera.append(["0", "Annulla", "Menu"])
    return ReplyKeyboardMarkup(tastiera, resize_keyboard=True)