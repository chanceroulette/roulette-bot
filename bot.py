import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from datetime import datetime
from collections import defaultdict

# Carica il token dal file .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Costanti
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"

# Stato utenti
user_data = defaultdict(lambda: {
    "sessione_attiva": False,
    "first15": [],
    "modalita_inserimento": False,
    "chances_attive": [],
    "boxes": defaultdict(list),
    "fiches_vinte": 0,
    "fiches_perse": 0,
    "giocate_totali": 0,
    "inizio_sessione": None,
    "is_admin": False
})

# Comandi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto in Chance Roulette!\nScrivi /menu per iniziare oppure usa i comandi manuali.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/report", "/storico", "/annulla_ultima"],
        ["/id", "/help"]
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append(["/admin"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Comando non valido.")
        return
    await update.message.reply_text("Accesso area admin confermato.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]
    durata = "N/A"
    if data["inizio_sessione"]:
        durata = str(datetime.now() - data["inizio_sessione"]).split('.')[0]

    await update.message.reply_text(
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {data['giocate_totali']}\n"
        f"Vinte: {data['fiches_vinte']} | Perse: {data['fiches_perse']}\n"
        f"Saldo: {data['fiches_vinte'] - data['fiches_perse']} fiche\n"
        f"Tempo di gioco: {durata}\n"
        f"Chances attive: {', '.join(data['chances_attive']) if data['chances_attive'] else 'Nessuna'}"
    )

async def numero_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]
    if not data["modalita_inserimento"]:
        await update.message.reply_text("Attiva prima la modalità inserimento con /modalita_inserimento.")
        return

    try:
        numero = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido.")
        return

    await update.message.reply_text(f"Numero inserito: {numero}")

# Avvio applicazione
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
    asyncio.run(main())