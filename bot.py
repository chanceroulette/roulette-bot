import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Colori roulette
rosso = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
nero = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

# Configurazione
CHANCES = ["Rosso", "Nero", "Pari", "Dispari", "Manque", "Passe"]
BOXES = {chance: [1,1,1,1] for chance in CHANCES}
ACTIVE_CHANCES = CHANCES.copy()
LAST_NUMBERS = []
FICHES_VINTE = 0
FICHES_PERSE = 0
STOP_LOSS = None
STOP_WIN = None
TETTO_MAX = 9999
VALORE_FICHE = 1
MODALITA_INSERIMENTO = False
HISTORY_BOXES = []

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Funzione vincita
def is_win(chance, number):
    if number == 0:
        return False
    if chance == "Rosso": return number in rosso
    if chance == "Nero": return number in nero
    if chance == "Pari": return number % 2 == 0
    if chance == "Dispari": return number % 2 != 0
    if chance == "Manque": return 1 <= number <= 18
    if chance == "Passe": return 19 <= number <= 36
    return False

# Tastiera colorata roulette
def get_keyboard():
    layout = []
    row = []
    for i in range(1, 37):
        color = "🔴" if i in rosso else "⚫"
        row.append(KeyboardButton(f"{color} {i}"))
        if len(row) == 12:
            layout.append(row)
            row = []
    layout.append([KeyboardButton("🟢 0")])
    return ReplyKeyboardMarkup(layout, resize_keyboard=True, one_time_keyboard=False)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto! Scrivi /modalita_inserimento per attivare la tastiera.", reply_markup=get_keyboard())

# /modalita_inserimento
async def modalita_inserimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODALITA_INSERIMENTO
    MODALITA_INSERIMENTO = True
    await update.message.reply_text("Modalità inserimento attiva. Tocca i numeri per registrarli.", reply_markup=get_keyboard())

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODALITA_INSERIMENTO
    MODALITA_INSERIMENTO = False
    await update.message.reply_text("Modalità inserimento disattivata.")

# Messaggi numerici
async def inserisci_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FICHES_PERSE, FICHES_VINTE, LAST_NUMBERS, BOXES, HISTORY_BOXES

    if not MODALITA_INSERIMENTO:
        return

    testo = update.message.text.strip().replace("🔴", "").replace("⚫", "").replace("🟢", "").strip()
    if not testo.isdigit():
        return
    numero = int(testo)
    LAST_NUMBERS.append(numero)
    HISTORY_BOXES.append({k: v.copy() for k, v in BOXES.items()})

    messaggio = f"Numero inserito: {numero}\n"
    fiches_giro_vinte = 0
    fiches_giro_perse = 0

    for chance in ACTIVE_CHANCES:
        box = BOXES[chance]
        if not box:
            BOXES[chance] = [1,1,1,1]
            box = BOXES[chance]
        puntata = box[0] + box[-1] if len(box) >= 2 else box[0]*2

        if puntata > TETTO_MAX:
            messaggio += f"⚠️ {chance}: richiesta {puntata} fiche – supera limite {TETTO_MAX}. Salto.\n"
            continue

        if is_win(chance, numero):
            fiches_giro_vinte += puntata
            messaggio += f"✅ {chance}: VINTO – {puntata} fiche → rimuovo estremi\n"
            try:
                box.pop(-1)
                box.pop(0)
            except IndexError:
                box.clear()
        else:
            fiches_giro_perse += puntata
            box.append(puntata)
            messaggio += f"❌ {chance}: PERSO – {puntata} fiche → aggiunto in fondo\n"

    FICHES_VINTE += fiches_giro_vinte
    FICHES_PERSE += fiches_giro_perse
    saldo = FICHES_VINTE - FICHES_PERSE
    messaggio += f"\n🎯 Giro: vinte {fiches_giro_vinte}, perse {fiches_giro_perse} – saldo totale: {saldo} fiches\n"

    if STOP_LOSS and FICHES_PERSE >= STOP_LOSS:
        MODALITA_INSERIMENTO = False
        messaggio += "\n❌ STOP LOSS raggiunto. Sessione bloccata."

    if STOP_WIN and FICHES_VINTE >= STOP_WIN:
        MODALITA_INSERIMENTO = False
        messaggio += "\n✅ STOP WIN raggiunto. Sessione bloccata."

    await update.message.reply_text(messaggio)

# Avvio bot
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("modalita_inserimento", modalita_inserimento))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), inserisci_numero))
    app.run_polling()

if __name__ == "__main__":
    main()