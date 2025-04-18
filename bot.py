import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Costanti
CHANCES = ["Rosso", "Nero", "Pari", "Dispari", "Manque", "Passe"]
BOXES = {chance: [1, 1, 1, 1] for chance in CHANCES}
LAST_NUMBERS = []

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Calcolo vincita
def is_win(chance, number):
    if number == 0:
        return False
    if chance == "Rosso":
        return number in {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    if chance == "Nero":
        return number in {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
    if chance == "Pari":
        return number % 2 == 0
    if chance == "Dispari":
        return number % 2 != 0
    if chance == "Manque":
        return 1 <= number <= 18
    if chance == "Passe":
        return 19 <= number <= 36
    return False

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto nel tuo BOT Roulette Box!\nUsa /inserisci <numero> per cominciare.")

# Comando /inserisci
async def inserisci(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Inserisci un numero: /inserisci 17")
        return
    try:
        numero = int(context.args[0])
        if numero < 0 or numero > 36:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido da 0 a 36.")
        return

    LAST_NUMBERS.append(numero)
    messaggio = f"Numero inserito: {numero}\n\n"
    for chance in CHANCES:
        box = BOXES[chance]
        if not box:
            BOXES[chance] = [1,1,1,1]
            box = BOXES[chance]
        puntata = box[0] + box[-1] if len(box) >= 2 else box[0] * 2
        if is_win(chance, numero):
            messaggio += f"✅ {chance}: VINTO - Punta {puntata} fiche → rimuovi prima e ultima casella.\n"
            if len(box) >= 2:
                box.pop(0)
                box.pop(-1)
            else:
                box.clear()
        else:
            messaggio += f"❌ {chance}: PERSO - Punta {puntata} fiche → aggiungi in fondo.\n"
            box.append(puntata)
    await update.message.reply_text(messaggio)

# Comando /box
async def box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = "Situazione attuale dei box:\n"
    for chance, box in BOXES.items():
        testo += f"{chance}: {box}\n"
    await update.message.reply_text(testo)

# Comando /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for chance in CHANCES:
        BOXES[chance] = [1, 1, 1, 1]
    await update.message.reply_text("Tutti i box sono stati resettati.")

# Avvio applicazione
def main():
    import os
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("inserisci", inserisci))
    app.add_handler(CommandHandler("box", box))
    app.add_handler(CommandHandler("reset", reset))
    app.run_polling()

if __name__ == "__main__":
    main()
