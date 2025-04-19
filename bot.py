import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

from strategy import StrategiaRoulette
from keyboards import genera_tastiera_numerica

# Carica variabili d’ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Configurazioni
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"
UTENTI = {}

# Inizializza utente
def init_user(user_id):
    if user_id not in UTENTI:
        UTENTI[user_id] = {
            "storico": [],
            "vinte": 0,
            "perse": 0,
            "saldo": 0,
            "inizio": datetime.now(),
            "admin": False
        }

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)
    await update.message.reply_text("Benvenuto in Chance Roulette!\nScrivi /menu per iniziare.")

# /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)

    keyboard = [["/modalita_inserimento"], ["/report", "/storico", "/annulla_ultima"], ["/id", "/help"]]
    if user_id == ADMIN_ID or UTENTI[user_id]["admin"]:
        keyboard.append(["/admin"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

# /id
async def mostra_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la tua strategia alla roulette europea.\n\n"
        "Scrivi /menu per iniziare.\n"
        "Supporto: info@trilium-bg.com\n"
        "© 2025 Fabio Felice Cudia"
    )

# /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    strategia = UTENTI[user_id].get("strategia")
    if not strategia:
        await update.message.reply_text("Non hai ancora iniziato una sessione.")
        return

    durata = datetime.now() - UTENTI[user_id]["inizio"]
    minuti, secondi = divmod(durata.total_seconds(), 60)
    await update.message.reply_text(
        f"REPORT SESSIONE\n"
        f"Giocate: {len(UTENTI[user_id]['storico'])}\n"
        f"Vinte: {strategia.vinte} | Perse: {strategia.perse}\n"
        f"Saldo: {strategia.saldo} fiche\n"
        f"Tempo: {int(minuti)}m {int(secondi)}s"
    )

# /storico
async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = UTENTI[update.effective_user.id]
    if not user["storico"]:
        await update.message.reply_text("Nessun numero registrato.")
    else:
        numeri = ", ".join(map(str, user["storico"]))
        await update.message.reply_text(f"Numeri inseriti:\n{numeri}")

# /annulla_ultima
async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = UTENTI[update.effective_user.id]
    if user["storico"]:
        annullato = user["storico"].pop()
        await update.message.reply_text(f"Ultimo numero annullato: {annullato}")
    else:
        await update.message.reply_text("Nessun numero da annullare.")

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    context.user_data["attesa_password_admin"] = True
    await update.message.reply_text("Inserisci la password admin:")

# Password admin
async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get("attesa_password_admin"):
        if update.message.text.strip() == ADMIN_PASSWORD:
            UTENTI[user_id]["admin"] = True
            context.user_data["attesa_password_admin"] = False
            await update.message.reply_text(
                "Accesso admin effettuato.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Utenti registrati", callback_data="admin_utenti")],
                    [InlineKeyboardButton("Logout", callback_data="admin_logout")]
                ])
            )
        else:
            await update.message.reply_text("Password errata.")
            context.user_data["attesa_password_admin"] = False

# Callback admin
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != ADMIN_ID or not UTENTI[user_id]["admin"]:
        await query.edit_message_text("Non sei autorizzato.")
        return

    if query.data == "admin_utenti":
        msg = f"Utenti registrati: {len(UTENTI)}\n\n"
        msg += "\n".join(str(uid) for uid in UTENTI.keys())
        await query.edit_message_text(msg)

    elif query.data == "admin_logout":
        UTENTI[user_id]["admin"] = False
        await query.edit_message_text("Logout effettuato.")

# /modalita_inserimento
async def modalita_inserimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)

    if "strategia" not in UTENTI[user_id]:
        UTENTI[user_id]["strategia"] = StrategiaRoulette()
        UTENTI[user_id]["strategia"].attiva_chances(["Rosso", "Pari", "Passe"])

    await update.message.reply_text(
        "Modalità inserimento attiva.\nTocca un numero della roulette:",
        reply_markup=genera_tastiera_numerica()
    )

# Gestione numero inserito
async def gestisci_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    testo = update.message.text

    if not testo.isdigit():
        await update.message.reply_text("Inserisci solo numeri tra 0 e 36.")
        return

    numero = int(testo)
    if numero < 0 or numero > 36:
        await update.message.reply_text("Numero non valido.")
        return

    strategia = UTENTI[user_id]["strategia"]
    UTENTI[user_id]["storico"].append(numero)

    puntate = strategia.calcola_puntate()
    risultati = strategia.aggiorna_esito(numero)

    msg = f"NUMERO USCITO: {numero}\n\n"
    for chance, fiche in puntate.items():
        risultato = risultati[chance]
        msg += f"{chance}: puntate {fiche} fiche → esito: {risultato}\n"

    msg += f"\nSaldo totale: {strategia.saldo} fiche\n"
    await update.message.reply_text(msg, reply_markup=genera_tastiera_numerica())

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("id", mostra_id))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CommandHandler("modalita_inserimento", modalita_inserimento))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.Regex("^[0-9]{1,2}$"), gestisci_numero))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_password))

    app.run_polling()

if __name__ == "__main__":
    main()