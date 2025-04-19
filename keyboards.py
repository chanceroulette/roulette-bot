from telegram import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    """
    Tastiera principale con i comandi disponibili.
    /report           – Report attuale
    /storico          – Mostra numeri usciti
    /annulla_ultima   – Annulla ultima giocata
    /id               – Mostra il tuo ID Telegram
    /help             – Aiuto / contatti
    /admin            – (nascosto agli altri) pannello admin
    /primi15          – Inserimento prime 15 estrazioni
    """
    buttons = [
        [KeyboardButton("/report"), KeyboardButton("/storico"), KeyboardButton("/annulla_ultima")],
        [KeyboardButton("/id"), KeyboardButton("/help"), KeyboardButton("/admin")],
        [KeyboardButton("/primi15")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def number_keyboard():
    """
    Tastiera numerica per inserire l'estrazione (0–36) + Annulla / Menu.
    Genera dinamicamente le righe da 0 a 36, 6 per riga.
    """
    # tutti i numeri da 0 a 36 come stringhe
    nums = [str(i) for i in range(0, 37)]
    # suddividi in blocchi di 6
    keyboard = [nums[i:i+6] for i in range(0, len(nums), 6)]
    # aggiungi riga di controllo
    keyboard.append(["Annulla", "Menu"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def chances_keyboard():
    """
    Tastiera per selezionare quali chances attivare:
    Rosso, Nero, Pari, Dispari, Manque, Passe.
    """
    rows = [
        ["Rosso", "Nero", "Pari"],
        ["Dispari", "Manque", "Passe"],
        ["Conferma", "Menu"]
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

def admin_keyboard():
    """
    Pannello admin (visibile solo dopo login con ID+password).
    """
    buttons = [
        [KeyboardButton("Mostra utenti attivi"), KeyboardButton("Esporta dati")],
        [KeyboardButton("Logout admin"), KeyboardButton("Menu")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

def yes_no_keyboard():
    """
    Tastiera Sì/No generica.
    """
    buttons = [["Sì", "No"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)