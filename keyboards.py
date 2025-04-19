from telegram import ReplyKeyboardMarkup

def genera_tastiera_numerica():
    numeri = [str(i) for i in range(0, 37)]
    tastiera = [numeri[i:i+6] for i in range(0, 36, 6)]
    tastiera.append(["Annulla", "Menu"])
    return ReplyKeyboardMarkup(tastiera, resize_keyboard=True)