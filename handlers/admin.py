from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from state import user_data, user_ids
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "5033904813"))  # fallback ID

def register_admin_commands(app):
    app.add_handler(CommandHandler("statistiche", statistiche))
    app.add_handler(CommandHandler("utenti", utenti))


async def statistiche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accesso negato.")
        return

    msg = "📦 Stato attuale dei box:\n"
    for uid, data in user_data.items():
        netto = data["fiches_won"] - data["fiches_lost"]
        msg += f"\n👤 Utente {uid}:\n"
        msg += f"- Giocate: {data['turns']}\n"
        msg += f"- Vincite: {data['fiches_won']} – Perdite: {data['fiches_lost']} – Netto: {netto:+}\n"
        msg += f"- Chances attive: {', '.join(data['active_chances']) if data['active_chances'] else 'Nessuna'}\n"

    await update.message.reply_text(msg)


async def utenti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accesso negato.")
        return

    await update.message.reply_text(f"👥 Utenti unici totali: {len(user_ids)}")
