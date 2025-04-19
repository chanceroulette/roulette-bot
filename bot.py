import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)
from dotenv import load_dotenv
import os
import time

# Carica le variabili d'ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"

# Setup logging
logging.basicConfig(level=logging.INFO)

# Stati conversazione
INSERISCI_PRIMI15 = range(1)

# Stato utente
user_data = {}

def get_user_state(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "start_time": time.time(),
            "numeri_usciti": [],
            "saldo": 0,
            "vinte": 0,
            "perse": 0,
            "box": {},
            "primi15": [],
            "inserendo_primi15": False
        }
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/report", "/storico", "/annulla_ultima"],
        ["/id", "/help", "/admin"],
        ["/primi15"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    durata = int(time.time() - state["start_time"])
    minuti = durata // 60
    secondi = durata % 60
    await update.message.reply_text(
        f"Giocate totali: {state['vinte'] + state['perse']}\n"
        f"Vinte: {state['vinte']} | Perse: {state['perse']}\n"
        f"Saldo: {state['saldo']} fiches\n"
        f"Tempo di gioco: {minuti} min {secondi} sec\n"
        f"Chances attive: {', '.join(state['box'].keys()) if state['box'] else 'nessuna'}"
    )

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    if not state["numeri_usciti"]:
        await update.message.reply_text("Nessun numero registrato.")
    else:
        numeri = ', '.join(map(str, state["numeri_usciti"]))
        await update.message.reply_text(f"Numeri usciti: {numeri}")

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    if state["numeri_usciti"]:
        annullato = state["numeri_usciti"].pop()
        await update.message.reply_text(f"Numero {annullato} annullato.")
    else:
        await update.message.reply_text("Nessun numero da annullare.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la strategia dei box alla roulette.\n"
        "Usa /menu per accedere ai comandi.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Inserisci la password per accedere all'area admin:")
        return 1
    else:
        await update.message.reply_text("Comando non valido.")
        return ConversationHandler.END

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_PASSWORD:
        await update.message.reply_text("Accesso admin consentito. Comandi disponibili:\n - /utenti")
    else:
        await update.message.reply_text("Password errata.")
    return ConversationHandler.END

async def primi15_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    state["primi15"] = []
    state["inserendo_primi15"] = True
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.")
    return INSERISCI_PRIMI15

async def primi15_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    try:
        numero = int(update.message.text)
        if not 0 <= numero <= 36:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Per favore, inserisci un numero da 0 a 36.")
        return INSERISCI_PRIMI15

    state["primi15"].append(numero)
    if len(state["primi15"]) < 15:
        await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({len(state['primi15'])}/15):")
        return INSERISCI_PRIMI15
    else:
        state["inserendo_primi15"] = False
        await update.message.reply_text(f"Tutti i 15 numeri iniziali registrati: {state['primi15']}")
        return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("admin", admin)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)]},
        fallbacks=[]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("primi15", primi15_start)],
        states={INSERISCI_PRIMI15: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi15_add)]},
        fallbacks=[]
    ))

    app.run_polling()