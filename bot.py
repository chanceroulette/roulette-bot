import logging
import os
import asyncio
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler, ConversationHandler
)
from strategy import (
    StrategyManager, get_chances_from_numbers,
    build_session_report, should_suggest_change
)
from keyboards import main_menu_keyboard, roulette_keyboard, build_chances_keyboard
from dotenv import load_dotenv

# Carica variabili da .env o da Render dashboard
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 5033904813

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza strategia
strategy_manager = StrategyManager()

# Stati della conversazione
INSERISCI_NUMERI, INSERISCI_15_NUMERI, SELEZIONA_CHANCES = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        context.user_data["is_admin"] = True
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu comandi:", reply_markup=main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la strategia dei box alla roulette.\n"
        "Inserisci i numeri estratti uno alla volta e ricevi i report aggiornati.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "© 2025 Fabio Felice Cudia"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Il tuo ID Telegram è: {user_id}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        context.user_data["is_admin"] = True
        await update.message.reply_text("Accesso admin autorizzato.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("Accesso negato.")

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["numeri"] = []
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.", reply_markup=roulette_keyboard())
    return INSERISCI_15_NUMERI

async def handle_primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numero = int(update.message.text)
    context.user_data["numeri"].append(numero)
    n = len(context.user_data["numeri"])
    if n < 15:
        await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({n}/15):")
        return INSERISCI_15_NUMERI
    else:
        strategy_manager.reset()
        numeri = context.user_data["numeri"]
        strategy_manager.primi_15 = numeri
        context.user_data["scelte"] = get_chances_from_numbers(numeri)
        await update.message.reply_text(
            f"Tutti i 15 numeri iniziali registrati: {numeri}\n"
            f"Chances consigliate: {', '.join(context.user_data['scelte'])}",
            reply_markup=build_chances_keyboard()
        )
        return SELEZIONA_CHANCES

async def seleziona_chances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chance = update.message.text
    scelte = context.user_data.get("scelte", [])
    if chance not in scelte:
        scelte.append(chance)
    context.user_data["chances_attive"] = scelte
    await update.message.reply_text("Da ora in poi inserisci i nuovi numeri per seguire la strategia.", reply_markup=roulette_keyboard())
    return INSERISCI_NUMERI

async def inserisci(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("chances_attive", [])
    context.user_data.setdefault("storico", [])
    numero = int(update.message.text)
    context.user_data["storico"].append(numero)

    report = strategy_manager.genera_report(numero, context.user_data["chances_attive"])
    suggerimento = should_suggest_change(context.user_data["storico"], context.user_data["chances_attive"])

    messaggio = f"NUMERO USCITO: {numero}\n{report}"
    if suggerimento:
        messaggio += f"\n\nSuggerimento: {suggerimento}"
    await update.message.reply_text(messaggio)

    return INSERISCI_NUMERI

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    strategy_manager.annulla_ultimo()
    await update.message.reply_text("Ultimo numero annullato.")

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storico = strategy_manager.storico
    await update.message.reply_text(f"Numeri registrati: {storico}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("primi15", primi15)],
        states={
            INSERISCI_15_NUMERI: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_primi15)],
            SELEZIONA_CHANCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleziona_chances)],
            INSERISCI_NUMERI: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci)]
        },
        fallbacks=[CommandHandler("menu", menu)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()