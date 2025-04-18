import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

CHANCES = ["Rosso", "Nero", "Pari", "Dispari", "Manque", "Passe"]
rosso = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
nero = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

# Stato globale
BOXES = {}
ACTIVE_CHANCES = []
FIRST15 = []
FICHES_VINTE = 0
FICHES_PERSE = 0
MODALITA_INSERIMENTO = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_win(chance, number):
    if number == 0: return False
    if chance == "Rosso": return number in rosso
    if chance == "Nero": return number in nero
    if chance == "Pari": return number % 2 == 0
    if chance == "Dispari": return number % 2 != 0
    if chance == "Manque": return 1 <= number <= 18
    if chance == "Passe": return 19 <= number <= 36
    return False

def get_keyboard():
    layout = []
    row = []
    for i in range(1, 37):
        row.append(KeyboardButton(str(i)))
        if len(row) == 5:
            layout.append(row)
            row = []
    if row:
        layout.append(row)
    layout.append([KeyboardButton("0")])
    return ReplyKeyboardMarkup(layout, resize_keyboard=True, one_time_keyboard=False)

def suggest_chances(numbers):
    counts = {chance: 0 for chance in CHANCES}
    for n in numbers:
        for chance in CHANCES:
            if is_win(chance, n):
                counts[chance] += 1
    sorted_chances = sorted(counts.items(), key=lambda x: x[1])
    return [c[0] for c in sorted_chances[:3]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIRST15, ACTIVE_CHANCES, BOXES, MODALITA_INSERIMENTO, FICHES_PERSE, FICHES_VINTE
    FIRST15.clear()
    ACTIVE_CHANCES.clear()
    BOXES.clear()
    MODALITA_INSERIMENTO = False
    FICHES_PERSE = 0
    FICHES_VINTE = 0
    await update.message.reply_text(
        "Benvenuto! Ecco le 6 chances disponibili:\n"
        "- Rosso\n- Nero\n- Pari\n- Dispari\n- Manque\n- Passe\n\n"
        "Tocca i primi 15 numeri usciti sulla roulette per inizializzare la strategia.",
        reply_markup=get_keyboard()
    )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIRST15, MODALITA_INSERIMENTO

    text = update.message.text.strip()
    if not text.isdigit():
        return

    number = int(text)
    if not MODALITA_INSERIMENTO:
        FIRST15.append(number)
        if len(FIRST15) < 15:
            await update.message.reply_text(f"Hai inserito {len(FIRST15)}/15 numeri.")
        elif len(FIRST15) == 15:
            await update.message.reply_text("Analizzo le ultime 15 estrazioni...")
            suggerite = suggest_chances(FIRST15)
            keyboard = [
                [InlineKeyboardButton(c, callback_data=f"attiva_{c}")] for c in CHANCES
            ]
            keyboard.append([InlineKeyboardButton("✅ Conferma", callback_data="conferma_chances")])
            context.user_data["scelte"] = []
            await update.message.reply_text(
                f"Ti consiglio di attivare: {', '.join(suggerite)}\nSeleziona le chances che vuoi attivare:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        await inserisci_giocata(update, context, number)

async def seleziona_chances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_CHANCES, BOXES, MODALITA_INSERIMENTO
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("attiva_"):
        chance = data.replace("attiva_", "")
        scelte = context.user_data.get("scelte", [])
        if chance in scelte:
            scelte.remove(chance)
        else:
            scelte.append(chance)
        context.user_data["scelte"] = scelte
        await query.edit_message_text(
            f"Hai selezionato: {', '.join(scelte)}\nPremi ✅ Conferma per iniziare.",
            reply_markup=query.message.reply_markup
        )
    elif data == "conferma_chances":
        ACTIVE_CHANCES = context.user_data.get("scelte", [])
        for ch in ACTIVE_CHANCES:
            BOXES[ch] = [1, 1, 1, 1]
        MODALITA_INSERIMENTO = True
        await query.edit_message_text("Modalità inserimento attiva. Inizia a toccare i numeri.")
        await query.message.reply_text("Tastiera attivata.", reply_markup=get_keyboard())

async def inserisci_giocata(update: Update, context: ContextTypes.DEFAULT_TYPE, numero: int):
    global BOXES, FICHES_PERSE, FICHES_VINTE
    messaggio = f"Numero inserito: {numero}\n"
    fiches_giro_vinte = 0
    fiches_giro_perse = 0

    for chance in ACTIVE_CHANCES:
        box = BOXES[chance]
        puntata = box[0] + box[-1] if len(box) >= 2 else box[0]*2
        if is_win(chance, numero):
            fiches_giro_vinte += puntata
            messaggio += f"✅ {chance}: VINTO – {puntata} fiche\n"
            try:
                box.pop(-1)
                box.pop(0)
            except IndexError:
                box.clear()
        else:
            fiches_giro_perse += puntata
            box.append(puntata)
            messaggio += f"❌ {chance}: PERSO – {puntata} fiche\n"

    FICHES_VINTE += fiches_giro_vinte
    FICHES_PERSE += fiches_giro_perse
    saldo = FICHES_VINTE - FICHES_PERSE
    messaggio += f"\n🎯 Giro: vinte {fiches_giro_vinte}, perse {fiches_giro_perse} – saldo totale: {saldo} fiches"
    await update.message.reply_text(messaggio)

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(seleziona_chances))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    app.run_polling()

if __name__ == "__main__":
    main()