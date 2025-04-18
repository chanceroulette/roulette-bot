import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

CHANCES = ["Rosso", "Nero", "Pari", "Dispari", "Manque", "Passe"]
BOXES = {chance: [1, 1, 1, 1] for chance in CHANCES}
LAST_NUMBERS = []
ACTIVE_CHANCES = CHANCES.copy()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto nel tuo BOT Roulette Box!\n\n"
        "Digita /menu per visualizzare tutti i comandi disponibili."
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**COMANDI DISPONIBILI:**\n\n"
        "/start – Avvia il bot\n"
        "/menu – Mostra questo menù\n"
        "/inserisci <numero> – Inserisci l'ultimo numero uscito (es: /inserisci 27)\n"
        "/ultimi15 <numeri> – Inserisci le ultime 15 estrazioni per ricevere un consiglio su quali chances attivare (es: /ultimi15 3 5 17 12 ...)\n"
        "/attiva <chances> – Attiva solo alcune chances (es: /attiva Rosso Pari Passe)\n"
        "/box – Mostra i box attualmente attivi\n"
        "/reset – Reimposta tutti i box a [1,1,1,1] e riattiva tutte le chances\n"
    )

async def inserisci(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Inserisci l'ultimo numero uscito (es: /inserisci 27)")
        return
    try:
        numero = int(context.args[0])
        if numero < 0 or numero > 36:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido tra 0 e 36.")
        return

    LAST_NUMBERS.append(numero)
    messaggio = f"Numero inserito: {numero}\n\n"
    for chance in ACTIVE_CHANCES:
        box = BOXES[chance]
        if not box:
            BOXES[chance] = [1, 1, 1, 1]
            box = BOXES[chance]
        puntata = box[0] + box[-1] if len(box) >= 2 else box[0] * 2
        if is_win(chance, numero):
            messaggio += f"✅ {chance}: VINTO – Punta {puntata} fiche (prima + ultima casella) → rimuovi\n"
            try:
                box.pop(-1)
                box.pop(0)
            except IndexError:
                box.clear()
        else:
            messaggio += f"❌ {chance}: PERSO – Punta {puntata} fiche (prima + ultima casella) → aggiungi in fondo\n"
            box.append(puntata)

    await update.message.reply_text(messaggio)

async def box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = "Box attivi:\n"
    for chance in ACTIVE_CHANCES:
        testo += f"{chance}: {BOXES[chance]}\n"
    await update.message.reply_text(testo)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for chance in CHANCES:
        BOXES[chance] = [1, 1, 1, 1]
    global ACTIVE_CHANCES
    ACTIVE_CHANCES = CHANCES.copy()
    await update.message.reply_text("Tutti i box sono stati reimpostati a [1,1,1,1] e tutte le chances sono attive.")

async def ultimi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 15:
        await update.message.reply_text("Inserisci esattamente 15 numeri separati da spazio (es: /ultimi15 3 5 17 12 ...)")
        return
    try:
        numeri = [int(n) for n in context.args]
    except ValueError:
        await update.message.reply_text("Assicurati che tutti i valori siano numeri interi.")
        return

    frequenze = {chance: 0 for chance in CHANCES}
    for n in numeri:
        for chance in CHANCES:
            if is_win(chance, n):
                frequenze[chance] += 1

    sorted_chances = sorted(frequenze.items(), key=lambda x: x[1])
    suggerite = [c for c, f in sorted_chances[:3]]

    suggerimento = "Sulla base delle ultime 15 estrazioni, ti consiglio di attivare:\n"
    for c in suggerite:
        suggerimento += f"– {c} ({frequenze[c]} volte)\n"
    suggerimento += "\nPer attivarle, usa:\n/attiva " + " ".join(suggerite)

    await update.message.reply_text(suggerimento)

async def attiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ACTIVE_CHANCES
    scelte = [s.capitalize() for s in context.args if s.capitalize() in CHANCES]
    if not scelte:
        await update.message.reply_text("Devi indicare almeno una chance valida (es: /attiva Rosso Pari Passe)")
        return
    ACTIVE_CHANCES = scelte
    await update.message.reply_text(f"Chances attive ora: {', '.join(ACTIVE_CHANCES)}")

def main():
    import os
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("inserisci", inserisci))
    app.add_handler(CommandHandler("box", box))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("ultimi15", ultimi15))
    app.add_handler(CommandHandler("attiva", attiva))
    app.run_polling()

if __name__ == "__main__":
    main()