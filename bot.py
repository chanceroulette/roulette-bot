import logging
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

# === CONFIG ===
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# === LOGGING ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# === STATES ===
PRIMI15 = range(1)

# === SESSION ===
session_data = {}
admin_authenticated = set()

# === MENU ===
keyboard = [
    ["/report", "/storico", "/annulla_ultima"],
    ["/id", "/help", "/admin"],
    ["/primi15"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === UTILITY ===
def get_user_data(user_id):
    if user_id not in session_data:
        session_data[user_id] = {
            "numeri_usciti": [],
            "chances_attive": [],
            "giocate": 0,
            "vinte": 0,
            "perse": 0,
            "saldo": 0,
            "start_time": None,
        }
    return session_data[user_id]

# === COMANDI BASE ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la strategia delle chances semplici alla roulette europea.\n"
        "- Inserisci i numeri con /primi15 per ottenere le chances consigliate\n"
        "- Traccia le giocate con /modalita_inserimento\n"
        "- Visualizza report con /report\n"
        "Contatto: info@trilium-bg.com"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

# === ADMIN ===
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if user_id in admin_authenticated:
            await update.message.reply_text("Benvenuto nella sezione amministrativa.")
        else:
            await update.message.reply_text("Inserisci la password per accedere:")
            return 1
    else:
        await update.message.reply_text("Comando non valido.")
    return ConversationHandler.END

async def admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text == ADMIN_PASSWORD:
        admin_authenticated.add(user_id)
        await update.message.reply_text("Accesso admin confermato.")
    else:
        await update.message.reply_text("Password errata.")
    return ConversationHandler.END

# === PRIMI 15 ===
async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data["primi15"] = []
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.")
    return PRIMI15

async def handle_primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        numero = int(update.message.text)
        if numero < 0 or numero > 36:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido tra 0 e 36.")
        return PRIMI15

    context.user_data["primi15"].append(numero)
    if len(context.user_data["primi15"]) < 15:
        await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({len(context.user_data['primi15']) + 1}/15):")
        return PRIMI15
    else:
        await update.message.reply_text(f"Tutti i 15 numeri iniziali registrati: {context.user_data['primi15']}")
        # Qui puoi calcolare la statistica e suggerire le chances consigliate
        await update.message.reply_text("Chances consigliate: (prossimamente)")
        return ConversationHandler.END

# === REPORT ===
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    await update.message.reply_text(
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {data['giocate']}\n"
        f"Vinte: {data['vinte']} | Perse: {data['perse']}\n"
        f"Saldo: {data['saldo']} fiche\n"
        f"Chances attive: {', '.join(data['chances_attive']) if data['chances_attive'] else 'Nessuna'}"
    )

# === MAIN ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Handler comandi base
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("primi15", primi15))

    # Admin
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password)]},
        fallbacks=[],
    )
    app.add_handler(admin_conv)

    # Primi15 input
    primi15_conv = ConversationHandler(
        entry_points=[CommandHandler("primi15", primi15)],
        states={PRIMI15: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_primi15)]},
        fallbacks=[],
    )
    app.add_handler(primi15_conv)

    print("Bot in esecuzione...")
    app.run_polling()