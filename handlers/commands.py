from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from keyboards import build_keyboard
from state import init_user


def register_commands(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)
    await update.message.reply_text(
        "🎯 Inserisci i primi 15–20 numeri usciti, uno alla volta.\nQuando hai finito, premi ✅ Analizza.",
        reply_markup=build_keyboard()
    )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Comandi disponibili:\n"
        "/start – Inizia nuova sessione\n"
        "/reset – Azzera tutto\n"
        "/menu – Mostra i comandi\n"
        "/help – Info sul bot\n"
        "/statistiche – (solo admin)\n"
        "/utenti – (solo admin)",
        reply_markup=build_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎰 Benvenuto in Chance Roulette!\n\n"
        "Questo bot ti aiuta a seguire una strategia matematica sulla roulette basata sulle chances semplici (Rosso/Nero, Pari/Dispari...). "
        "Inserisci i primi 15–20 numeri per analizzare quali chances sono più favorevoli. Poi scegli quali attivare e gioca con gestione automatica dei box."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
