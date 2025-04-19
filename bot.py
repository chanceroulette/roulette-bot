import os
import logging
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813

# Logging
logging.basicConfig(level=logging.INFO)

# Chance mappate
chances = {
    "Rosso": [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
    "Nero": [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
    "Pari": list(range(2, 37, 2)),
    "Dispari": list(range(1, 36, 2)),
    "Manque": list(range(1, 19)),
    "Passe": list(range(19, 37))
}

keyboard = [[str(i) for i in range(j, j+6)] for j in range(1, 37, 6)]
keyboard.append(["0", "Annulla", "Menu"])
reply_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Stato utenti
utenti = {}

def init_user(user_id):
    utenti[user_id] = {
        "numeri": [],
        "primi15": [],
        "attive": [],
        "fase_analisi": True,
        "admin": user_id == ADMIN_ID
    }

def suggerisci_chances(numeri):
    counter = {ch: 0 for ch in chances}
    for n in numeri:
        for ch, val in chances.items():
            if n in val:
                counter[ch] += 1
    suggerite = sorted(counter.items(), key=lambda x: x[1])
    return [ch[0] for ch in suggerite[:3]]  # meno frequenti

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in utenti:
        init_user(user_id)
    await update.message.reply_text("Benvenuto in Chance Roulette!\nScrivi /menu per iniziare.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in utenti:
        init_user(user_id)
    buttons = [
        ["/report", "/storico", "/annulla"],
        ["/primi15", "/help", "/id"]
    ]
    if user_id == ADMIN_ID:
        buttons.append(["/admin"])
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Inserisci i numeri usciti e il bot ti guiderà nel gioco.\nDopo i primi 15 numeri, riceverai i suggerimenti.")

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        utenti[user_id]["admin"] = True
        await update.message.reply_text("Accesso admin attivato.")
    else:
        await update.message.reply_text("Comando non disponibile.")

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)
    utenti[user_id]["primi15"] = []
    utenti[user_id]["fase_analisi"] = True
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.", reply_markup=reply_keyboard)

async def numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text
    if user_id not in utenti:
        init_user(user_id)
    stato = utenti[user_id]

    if msg.lower() == "annulla":
        if stato["numeri"]:
            stato["numeri"].pop()
            await update.message.reply_text("Ultimo numero annullato.")
        return
    if msg.lower() == "menu":
        await menu(update, context)
        return
    if not msg.isdigit():
        await update.message.reply_text("Per favore inserisci un numero valido.")
        return
    numero = int(msg)
    if not 0 <= numero <= 36:
        await update.message.reply_text("Numero fuori range (0-36).")
        return

    if stato["fase_analisi"]:
        stato["primi15"].append(numero)
        if len(stato["primi15"]) < 15:
            await update.message.reply_text(f"{len(stato['primi15'])}/15 registrato. Inserisci il prossimo numero.")
        else:
            stato["fase_analisi"] = False
            suggerite = suggerisci_chances(stato["primi15"])
            stato["suggerite"] = suggerite
            buttons = [[InlineKeyboardButton(ch, callback_data=f"attiva_{ch}")] for ch in suggerite]
            await update.message.reply_text(
                "Chances consigliate (meno uscite finora):",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    else:
        stato["numeri"].append(numero)
        attive = stato.get("attive", [])
        risposte = []
        for ch in attive:
            if numero in chances[ch]:
                risposte.append(f"{ch}: VINTO")
            else:
                risposte.append(f"{ch}: PERSO")
        await update.message.reply_text(f"Numero uscito: {numero}\n" + "\n".join(risposte), reply_markup=reply_keyboard)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data

    if data.startswith("attiva_"):
        chance = data.replace("attiva_", "")
        if user_id not in utenti:
            init_user(user_id)
        utenti[user_id]["attive"].append(chance)
        await query.edit_message_text(f"Chance attivata: {chance}\nPuoi ora inserire i numeri normalmente.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stato = utenti.get(user_id, {})
    chances_attive = stato.get("attive", [])
    saldo = 0  # futuro: calcolo preciso
    await update.message.reply_text(
        f"REPORT\nNumeri: {len(stato.get('numeri', []))}\nChances attive: {', '.join(chances_attive)}\nSaldo stimato: {saldo} fiche"
    )

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numeri = utenti.get(user_id, {}).get("numeri", [])
    if numeri:
        await update.message.reply_text("Numeri usciti:\n" + ", ".join(map(str, numeri)))
    else:
        await update.message.reply_text("Nessun numero registrato.")

# Setup bot
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("id", id_command))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("storico", storico))
app.add_handler(CommandHandler("primi15", primi15))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, numero))

if __name__ == "__main__":
    app.run_polling()