
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Chance selezionate (puoi modificarle)
ACTIVE_CHANCES = ["Rosso", "Pari", "Passe"]

# Definizione dei numeri per ogni chance
RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
EVEN = {n for n in range(1, 37) if n % 2 == 0}
ODD = {n for n in range(1, 37) if n % 2 != 0}
MANQUE = set(range(1, 19))
PASSE = set(range(19, 37))

# Stato dei box per ogni utente
user_boxes = {}

# Inizializzazione di un box standard
def init_box():
    return [1, 1, 1, 1]

def get_win(chance, number):
    if chance == "Rosso":
        return number in RED
    elif chance == "Nero":
        return number in BLACK
    elif chance == "Pari":
        return number in EVEN
    elif chance == "Dispari":
        return number in ODD
    elif chance == "Manque":
        return number in MANQUE
    elif chance == "Passe":
        return number in PASSE
    return False

def box_to_str(box):
    return " | ".join(str(int(c)) for c in box)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_boxes[user_id] = {chance: init_box() for chance in ACTIVE_CHANCES}
    await update.message.reply_text("Benvenuto! Inserisci un numero cliccando sui bottoni qui sotto.")
    await send_keyboard(update, context)

async def send_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for row in range(0, 37, 6):
        keyboard.append([
            InlineKeyboardButton(str(i), callback_data=str(i))
            for i in range(row, min(row + 6, 37))
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Scegli un numero:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    number = int(query.data)
    user_id = query.from_user.id

    if user_id not in user_boxes:
        user_boxes[user_id] = {chance: init_box() for chance in ACTIVE_CHANCES}

    boxes = user_boxes[user_id]
    result = f"Hai selezionato il numero {number}\n\n"

    for chance, box in boxes.items():
        if not box:
            box.extend(init_box())

        bet = box[0] + box[-1] if len(box) >= 2 else box[0] * 2
        win = get_win(chance, number)

        if win:
            if len(box) >= 2:
                box.pop(0)
                box.pop(-1)
            else:
                box.clear()
            result += f"✅ {chance}: vinto {bet} fiches — nuovo box: {box_to_str(box) or 'svuotato'}\n"
        else:
            box.append(bet)
            result += f"❌ {chance}: perso {bet} fiches — nuovo box: {box_to_str(box)}\n"

    await query.edit_message_text(text=result)
    await send_keyboard(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
