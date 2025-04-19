import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackContext
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = "5033904813"
ADMIN_PASSWORD = "@@Zaq12wsx@@25"

user_sessions = {}
admin_authenticated = {}

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# CHANCES DEFINITION
chances_map = {
    "Rosso": [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
    "Nero": [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
    "Pari": list(range(2, 37, 2)),
    "Dispari": list(range(1, 36, 2)),
    "Manque": list(range(1, 19)),
    "Passe": list(range(19, 37))
}

keyboard = [[str(i) for i in range(j, j+6)] for j in range(1, 37, 6)]
keyboard.append(["0", "Annulla", "Menu"])

def create_new_session():
    return {
        "numeri": [],
        "chances": {},
        "giocate": 0,
        "vinte": 0,
        "perse": 0,
        "saldo": 0,
        "iniziata": False,
        "start_time": None,
        "inserimento_15": False,
        "inseriti_15": []
    }

def get_suggerite(numeri):
    statistiche = {chance: 0 for chance in chances_map}
    for n in numeri:
        for nome, gruppo in chances_map.items():
            if n in gruppo:
                statistiche[nome] += 1
    return sorted(statistiche.items(), key=lambda x: x[1])[:3]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_sessions:
        user_sessions[user_id] = create_new_session()
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([
        ["/report", "/storico", "/annulla_ultima"],
        ["/id", "/help", "/admin"],
        ["/primi15"]
    ], resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la strategia dei box sulla roulette europea.\n"
        "Inserisci i numeri usciti e riceverai le indicazioni sulle chances da attivare.\n"
        "Email supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = user_sessions.setdefault(user_id, create_new_session())
    session["inseriti_15"] = []
    session["inserimento_15"] = True
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.")

async def handle_number(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    session = user_sessions.setdefault(user_id, create_new_session())
    msg = update.message.text

    if session["inserimento_15"]:
        if not msg.isdigit():
            return
        numero = int(msg)
        session["inseriti_15"].append(numero)
        count = len(session["inseriti_15"])
        if count < 15:
            await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({count}/15):")
        else:
            await update.message.reply_text(f"Tutti i 15 numeri iniziali registrati: {session['inseriti_15']}")
            suggerite = get_suggerite(session["inseriti_15"])
            testo = "Chances da attivare (meno frequenti finora):\n"
            testo += "\n".join([f"{ch}: {num} volte" for ch, num in suggerite])
            session["chances_attive"] = [ch for ch, _ in suggerite]
            session["inserimento_15"] = False
            session["numeri"] = session["inseriti_15"].copy()
            await update.message.reply_text(testo)
    elif msg.lower() == "annulla":
        if session["numeri"]:
            session["numeri"].pop()
            await update.message.reply_text("Ultimo numero annullato.")
    elif msg.isdigit():
        numero = int(msg)
        session["numeri"].append(numero)
        session["giocate"] += 1
        dettagli = []
        totale = 0
        for ch in session.get("chances_attive", []):
            puntata = 3
            risultato = puntata if numero in chances_map[ch] else -puntata
            totale += risultato
            dettagli.append(f"{ch}: puntate {puntata} fiche → esito: {risultato:+}")
            if risultato > 0:
                session["vinte"] += 1
            else:
                session["perse"] += 1
        session["saldo"] += totale
        testo = f"NUMERO USCITO: {numero}\n" + "\n".join(dettagli)
        testo += f"\nSaldo totale: {session['saldo']} fiche"
        await update.message.reply_text(testo)

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    numeri = user_sessions.get(user_id, {}).get("numeri", [])
    if numeri:
        await update.message.reply_text("Numeri usciti:\n" + ", ".join(map(str, numeri)))
    else:
        await update.message.reply_text("Nessun numero registrato.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = user_sessions.get(user_id, create_new_session())
    testo = (
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {session['giocate']}\n"
        f"Vinte: {session['vinte']} | Perse: {session['perse']}\n"
        f"Saldo: {session['saldo']} fiche\n"
        f"Chances attive: {', '.join(session.get('chances_attive', []))}"
    )
    await update.message.reply_text(testo)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Comando non disponibile.")
        return
    await update.message.reply_text("Inserisci la password:")
    admin_authenticated[user_id] = False

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id == ADMIN_ID and not admin_authenticated.get(user_id):
        if update.message.text == ADMIN_PASSWORD:
            admin_authenticated[user_id] = True
            await update.message.reply_text("Accesso amministratore attivato.")
        else:
            await update.message.reply_text("Password errata.")

# Setup
app = ApplicationBuilder().token(TOKEN).build()

# Comandi
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("id", id))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("storico", storico))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("primi15", primi15))
app.add_handler(CommandHandler("annulla_ultima", storico))

# Messaggi
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

if __name__ == "__main__":
    app.run_polling()