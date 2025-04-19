import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813
ADMIN_PASSWORD = "@@Zaq12wsx@@25"

logging.basicConfig(level=logging.INFO)

INSERISCI_NUMERO, INSERISCI_PRIMI15 = range(2)

user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            "box": {
                "rosso": [1, 1, 1, 1],
                "pari": [1, 1, 1, 1],
                "passe": [1, 1, 1, 1]
            },
            "attive": {"rosso": False, "pari": False, "passe": False},
            "storico": [],
            "saldo": 0,
            "inizio_sessione": None,
            "primi15": [],
            "inserendo": False,
            "inserendo_primi15": False,
            "admin_authenticated": False
        }
    return user_states[user_id]

def reset_box():
    return [1, 1, 1, 1]

def colore(numero):
    if numero == 0:
        return "verde"
    rossi = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    return "rosso" if numero in rossi else "nero"

def pari(numero):
    return numero != 0 and numero % 2 == 0

def passe(numero):
    return 19 <= numero <= 36

def calcola_puntata(box):
    return box[0] + box[-1]

def aggiorna_box(box, vincita, puntata):
    if vincita:
        if len(box) > 2:
            return box[1:-1]
        else:
            return reset_box()
    else:
        box.append(puntata)
        return box

def estrai_statistiche(usciti):
    return {
        "rosso": sum(1 for n in usciti if colore(n) == "rosso"),
        "nero": sum(1 for n in usciti if colore(n) == "nero"),
        "pari": sum(1 for n in usciti if pari(n)),
        "dispari": sum(1 for n in usciti if n != 0 and not pari(n)),
        "passe": sum(1 for n in usciti if passe(n)),
        "manque": sum(1 for n in usciti if 1 <= n <= 18),
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/report – Report attuale\n"
        "/annulla_ultima – Annulla ultima\n"
        "/storico – Mostra numeri usciti\n"
        "/help – Aiuto\n"
        "/id – Il tuo ID Telegram"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Il tuo ID Telegram è: {user_id}")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    if user_id == ADMIN_ID or state["admin_authenticated"]:
        await update.message.reply_text("Accesso all’area admin effettuato.")
    else:
        await update.message.reply_text("Inserisci la password per accedere:")
        return INSERISCI_NUMERO

async def inserisci_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if text == ADMIN_PASSWORD:
        user_states[user_id]["admin_authenticated"] = True
        await update.message.reply_text("Password corretta. Accesso admin attivo.")
    else:
        await update.message.reply_text("Password errata. Riprova con /admin")
    return ConversationHandler.END

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_user_state(update.effective_user.id)
    await update.message.reply_text(f"Numeri usciti: {state['storico']}")

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_user_state(update.effective_user.id)
    if state["storico"]:
        ultimo = state["storico"].pop()
        await update.message.reply_text(f"Ultimo numero annullato: {ultimo}")
    else:
        await update.message.reply_text("Nessun numero da annullare.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_user_state(update.effective_user.id)
    durata = 0
    if state["inizio_sessione"]:
        durata = (datetime.now() - state["inizio_sessione"]).seconds
    msg = (
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {len(state['storico'])}\n"
        f"Vinte: TBD | Perse: TBD\n"
        f"Saldo: {state['saldo']} fiche\n"
        f"Tempo di gioco: {durata // 60} min {durata % 60} sec\n"
        f"Chances attive: {', '.join([k for k, v in state['attive'].items() if v])}"
    )
    await update.message.reply_text(msg)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/report", "/storico", "/annulla_ultima"],
        ["/id", "/help", "/admin"],
        ["/primi15"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Menu comandi:", reply_markup=reply_markup)

# === Inserimento 15 numeri ===

async def primi15_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    state["primi15"] = []
    state["inserendo_primi15"] = True

    keyboard = [[str(i) for i in range(j, j + 6)] for j in range(1, 37, 6)]
    keyboard.append(["0", "Annulla"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta:", reply_markup=reply_markup)
    return INSERISCI_PRIMI15

async def primi15_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    text = update.message.text

    if text.lower() == "annulla":
        state["inserendo_primi15"] = False
        await update.message.reply_text("Inserimento interrotto.")
        return ConversationHandler.END

    try:
        numero = int(text)
        if not 0 <= numero <= 36:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Per favore, inserisci un numero da 0 a 36.")
        return INSERISCI_PRIMI15

    state["primi15"].append(numero)
    if len(state["primi15"]) < 15:
        await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({len(state['primi15'])}/15):")
        return INSERISCI_PRIMI15
    else:
        state["inserendo_primi15"] = False
        await update.message.reply_text(f"Tutti i 15 numeri iniziali registrati: {state['primi15']}")
        return ConversationHandler.END

# === MAIN ===

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CommandHandler("menu", menu))

    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_command)],
        states={INSERISCI_NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_password)]},
        fallbacks=[]
    )
    app.add_handler(admin_conv)

    primi15_conv = ConversationHandler(
        entry_points=[CommandHandler("primi15", primi15_start)],
        states={INSERISCI_PRIMI15: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi15_add)]},
        fallbacks=[]
    )
    app.add_handler(primi15_conv)

    app.run_polling()