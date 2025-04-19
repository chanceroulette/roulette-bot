import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime

load_dotenv()

# Configurazione
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"
UTENTI = {}
SESSIONI = {}
FIRST15 = {}
MAX_GIOCATE_FREE = 15

# Logging
logging.basicConfig(level=logging.INFO)

# Strategia
CHANCES = {
    "Rosso": [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
    "Pari": [i for i in range(2, 37, 2)],
    "Passe": [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
}

def get_active_chances():
    return list(CHANCES.keys())

def get_puntata(box):
    if len(box) == 1:
        return box[0]
    return box[0] + box[-1]

def aggiorna_box(esito, numero, chance, box):
    vincente = numero in CHANCES[chance]
    puntata = get_puntata(box)
    if vincente:
        if len(box) > 1:
            box.pop(0)
            box.pop(-1)
        else:
            box.clear()
    else:
        box.append(puntata)
    if not box:
        box.extend([1, 1, 1, 1])
    return puntata, puntata if vincente else -puntata

def get_report(sessione):
    fiches = sessione.get("fiches", {})
    perse = sessione.get("perse", {})
    tot = sessione.get("totale", 0)
    vinte = sessione.get("vinte", 0)
    perse_count = sessione.get("perse_count", 0)
    giocate = sessione.get("giocate", 0)
    start = sessione.get("start")
    duration = datetime.now() - start if start else 0
    chances_attive = list(fiches.keys())
    return f"""REPORT SESSIONE

Giocate totali: {giocate}
Vinte: {vinte} | Perse: {perse_count}
Saldo: {tot:+} fiche
Tempo di gioco: {duration.seconds//60} min {duration.seconds%60} sec
Chances attive: {', '.join(chances_attive)}"""

# Comandi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utente = update.effective_user.id
    if utente not in SESSIONI:
        SESSIONI[utente] = {
            "fiches": {c: [1, 1, 1, 1] for c in get_active_chances()},
            "perse": {},
            "vinte": 0,
            "perse_count": 0,
            "totale": 0,
            "giocate": 0,
            "start": datetime.now(),
        }
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/report", "/storico", "/annulla_ultima"], ["/id", "/help"]]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append(["/admin"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la strategia dei box su chances semplici.\n"
        "Ogni volta che esce un numero, selezionalo per aggiornare i tuoi box.\n"
        "Puoi usare i comandi /report, /storico, /id, /annulla_ultima.\n\n"
        "Email supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Comando non valido.")
        return
    await update.message.reply_text("Accesso pannello amministratore eseguito.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utente = update.effective_user.id
    if utente not in SESSIONI:
        await update.message.reply_text("Nessuna sessione attiva.")
        return
    report_text = get_report(SESSIONI[utente])
    await update.message.reply_text(report_text)

async def numero_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utente = update.effective_user.id
    if utente not in SESSIONI:
        return
    numero = update.message.text.strip()
    if not numero.isdigit():
        return
    numero = int(numero)
    sessione = SESSIONI[utente]
    fiches = sessione["fiches"]
    totale = 0
    dettagli = []

    for chance, box in fiches.items():
        puntata, esito = aggiorna_box(numero in CHANCES[chance], numero, chance, box)
        totale += esito
        dettagli.append(f"{chance}: puntate {puntata} fiche → esito: {esito:+}")

    sessione["totale"] += totale
    sessione["giocate"] += 1
    if totale >= 0:
        sessione["vinte"] += 1
    else:
        sessione["perse_count"] += 1

    await update.message.reply_text(
        f"NUMERO USCITO: {numero}\n\n" + "\n".join(dettagli) + f"\n\nSaldo totale: {sessione['totale']} fiche"
    )

# Avvio Bot
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, numero_handler))

    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())