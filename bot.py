import os
import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Usa il token dalla variabile d’ambiente
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ID Telegram di Fabio (admin)
ADMIN_ID = 5033904813

admin_sessions = set()
user_data_dir = "dati_utenti"
os.makedirs(user_data_dir, exist_ok=True)

# /START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\nScrivi /menu per iniziare."
    )

# /HELP
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n\n"
        "Questo bot ti aiuta a seguire la strategia dei box sulle chances semplici della roulette europea.\n\n"
        "Comandi disponibili:\n"
        "/menu – Mostra i comandi principali\n"
        "/report – Visualizza il report della sessione\n"
        "/storico – Mostra gli ultimi numeri\n"
        "/annulla_ultima – Annulla l’ultima giocata\n"
        "/id – Mostra il tuo ID Telegram\n\n"
        "Supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

# /ID
async def mostra_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Il tuo ID Telegram è: {user_id}")

# /ADMIN (solo per te)
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    admin_sessions.add(user_id)
    await update.message.reply_text(
        "Accesso amministratore effettuato.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Utenti attivi", callback_data="admin_utenti")],
            [InlineKeyboardButton("Logout", callback_data="admin_logout")]
        ])
    )

# CALLBACK ADMIN
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != ADMIN_ID or user_id not in admin_sessions:
        await query.edit_message_text("Non sei autorizzato.")
        return

    if query.data == "admin_utenti":
        utenti = os.listdir(user_data_dir)
        messaggio = f"Utenti registrati: {len(utenti)}\n\n" + "\n".join(u[:-5] for u in utenti)
        await query.edit_message_text(messaggio)

    elif query.data == "admin_logout":
        admin_sessions.discard(user_id)
        await query.edit_message_text("Logout effettuato.")

# /MENU
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/report – Report attuale\n"
        "/annulla_ultima – Annulla ultima\n"
        "/storico – Mostra numeri usciti\n"
        "/help – Aiuto\n"
        "/id – Il tuo ID Telegram"
    )

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("id", mostra_id))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_callback))

    app.run_polling()

if __name__ == "__main__":
    main()