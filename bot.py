import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from datetime import datetime
import os

TOKEN = "INSERISCI_IL_TUO_TOKEN"
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"

# Variabili globali per ogni utente
UTENTI = {}

# Stati conversazione
INSERIMENTO, ADMIN_LOGIN = range(2)

# Colori e categorie roulette
CHANCES = {
    'Rosso': [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
    'Nero': [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
    'Pari': [x for x in range(1, 37) if x % 2 == 0],
    'Dispari': [x for x in range(1, 37) if x % 2 != 0],
    'Manque': list(range(1, 19)),
    'Passe': list(range(19, 37))
}

# Inizializza un nuovo utente
def init_user(user_id):
    UTENTI[user_id] = {
        "attive": [],
        "box": {},
        "storico": [],
        "vinte": 0,
        "perse": 0,
        "saldo": 0,
        "limite": 500,
        "minimo_fiche": 5,
        "stop_win": None,
        "stop_loss": None,
        "inizio": datetime.now(),
        "admin": False
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in UTENTI:
        init_user(user_id)
    await update.message.reply_text("Benvenuto in Chance Roulette! Scrivi /menu per iniziare.")

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Questo bot ti aiuta a seguire la strategia dei box. Per assistenza scrivi a info@trilium-bg.com")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/report", "/storico", "/annulla_ultima"], ["/id", "/help"]]
    if update.effective_user.id == ADMIN_ID or UTENTI[update.effective_user.id]["admin"]:
        keyboard.append(["/admin"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = UTENTI[update.effective_user.id]
    tempo = datetime.now() - user["inizio"]
    minuti, secondi = divmod(tempo.total_seconds(), 60)
    chances_attive = ', '.join(user["attive"])
    await update.message.reply_text(
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {len(user['storico'])}\n"
        f"Vinte: {user['vinte']} | Perse: {user['perse']}\n"
        f"Saldo: {user['saldo']} fiches\n"
        f"Tempo di gioco: {int(minuti)} min {int(secondi)} sec\n"
        f"Chances attive: {chances_attive}"
    )

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = UTENTI[update.effective_user.id]
    if not user["storico"]:
        await update.message.reply_text("Nessun numero registrato.")
    else:
        await update.message.reply_text("Numeri usciti:\n" + ', '.join(map(str, user["storico"][-15:])))

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = UTENTI[update.effective_user.id]
    if user["storico"]:
        annullato = user["storico"].pop()
        await update.message.reply_text(f"Ultimo numero annullato: {annullato}")
    else:
        await update.message.reply_text("Nessun numero da annullare.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID and not UTENTI[update.effective_user.id]["admin"]:
        await update.message.reply_text("Comando non valido.")
        return ConversationHandler.END
    await update.message.reply_text("Inserisci la password di accesso:")
    return ADMIN_LOGIN

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == ADMIN_PASSWORD:
        UTENTI[update.effective_user.id]["admin"] = True
        await update.message.reply_text("Accesso admin effettuato.")
    else:
        await update.message.reply_text("Password errata.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin)],
        states={ADMIN_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)]},
        fallbacks=[],
    )
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()