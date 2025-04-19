import os
import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = "INSERISCI_IL_TUO_TOKEN"
ADMIN_ID = None  # ← Quando mi dai il tuo ID, lo mettiamo qui

admin_sessions = set()
user_data_dir = "dati_utenti"
os.makedirs(user_data_dir, exist_ok=True)

# FUNZIONE /START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Scrivi /menu per vedere le opzioni disponibili."
    )

# FUNZIONE /HELP
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n\n"
        "Questo bot ti aiuta a tracciare e gestire una strategia sulla roulette europea.\n"
        "Comandi utili:\n"
        "/menu - Mostra opzioni\n"
        "/report - Report sessione\n"
        "/storico - Numeri inseriti\n"
        "/annulla_ultima - Annulla ultima giocata\n"
        "/id - Il tuo ID Telegram\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia – Tutti i diritti riservati."
    )

# FUNZIONE /ID
async def mostra_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Il tuo ID Telegram è: {user_id}")

# COMANDO NASCOSTO /ADMIN
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_ID is None or user_id != ADMIN_ID:
        await update.message.reply_text("Comando non disponibile.")
        return
    await update.message.reply_text("Inserisci la password amministratore:")
    context.user_data["attesa_password_admin"] = True

# VERIFICA PASSWORD ADMIN
async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get("attesa_password_admin"):
        if update.message.text.strip() == "@@Zaq12wsx@@25":
            admin_sessions.add(user_id)
            context.user_data["attesa_password_admin"] = False
            await update.message.reply_text(
                "Accesso admin effettuato.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Utenti attivi", callback_data="admin_utenti")],
                    [InlineKeyboardButton("Logout", callback_data="admin_logout")]
                ])
            )
        else:
            await update.message.reply_text("Password errata.")
            context.user_data["attesa_password_admin"] = False

# CALLBACK PULSANTI ADMIN
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in admin_sessions:
        await query.edit_message_text("Non sei autorizzato.")
        return

    if query.data == "admin_utenti":
        utenti = os.listdir(user_data_dir)
        messaggio = f"Utenti registrati: {len(utenti)}\n\n" + "\n".join(u[:-5] for u in utenti)
        await query.edit_message_text(messaggio)

    elif query.data == "admin_logout":
        admin_sessions.discard(user_id)
        await query.edit_message_text("Logout effettuato.")

# MENU /MENU
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/report - Report attuale\n"
        "/annulla_ultima - Annulla ultima\n"
        "/storico - Mostra numeri usciti\n"
        "/help - Aiuto\n"
        "/id - Il tuo ID Telegram"
    )

# IMPOSTAZIONE PRINCIPALE
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("id", mostra_id))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_password))

    app.run_polling()

if __name__ == "__main__":
    main()