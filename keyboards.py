from telegram import ReplyKeyboardMarkup

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["/primi15", "/report", "/storico"],
            ["/annulla_ultima", "/menu", "/help"]
        ],
        resize_keyboard=True
    )

def roulette_keyboard():
    tastiera = []
    numeri = list(range(1, 37))
    for i in range(0, 36, 6):
        tastiera.append([str(n) for n in numeri[i:i+6]])
    tastiera.append(["0"])
    return ReplyKeyboardMarkup(tastiera, resize_keyboard=True)

def build_chances_keyboard(chances=None):
    tutte = ["rosso", "nero", "pari", "dispari", "manque", "passe"]
    if chances:
        righe = [[c.capitalize()] for c in chances]
    else:
        righe = [[c.capitalize()] for c in tutte]
    righe.append(["Conferma"])
    return ReplyKeyboardMarkup(righe, resize_keyboard=True)