import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, ConversationHandler
)
from keyboards import get_main_keyboard, get_number_keyboard, get_chances_keyboard
from strategy import suggerisci_chances, valuta_estrazione

# Carica variabili ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813

# Stato conversazione
INSERIMENTO_NUMERI, SELEZIONE_CHANCES = range(2)

# Dati utente temporanei
sessioni = {}

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
        "Questo bot ti aiuta a seguire la strategia dei box nella roulette europea.\n"
        "Comandi:\n"
        "/menu – Mostra il menu\n"
        "/primi15 – Inserisci i primi 15 numeri\n"
        "/storico – Visualizza lo storico\n"
        "/report – Report attuale\n"
        "/annulla_ultima – Annulla ultimo numero\n"
        "/id – Il tuo ID Telegram"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu comandi:", reply_markup=get_main_keyboard())

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessioni[user_id] = {
        "numeri": [],
        "chances_attive": [],
        "saldo": 0
    }
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.", reply_markup=get_number_keyboard())
    return INSERIMENTO_NUMERI

async def gestisci_numero_iniziale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numero = int(update.message.text)
    user_id = update.effective_user.id
    sessione = sessioni[user_id]

    if len(sessione["numeri"]) < 14:
        sessione["numeri"].append(numero)
        await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({len(sessione['numeri'])+1}/15):")
        return INSERIMENTO_NUMERI
    else:
        sessione["numeri"].append(numero)
        consigliate = suggerisci_chances(sessione["numeri"])
        sessione["chances_consigliate"] = consigliate
        await update.message.reply_text(
            f"Tutti i 15 numeri iniziali registrati: {sessione['numeri']}\n"
            f"Chances consigliate: {', '.join(consigliate)}\n\n"
            "Seleziona quali attivare:", 
            reply_markup=get_chances_keyboard(consigliate)
        )
        return SELEZIONE_CHANCES

async def seleziona_chances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    scelta = update.message.text
    sessione = sessioni[user_id]

    if scelta == "Conferma":
        await update.message.reply_text("Da ora in poi inserisci i nuovi numeri per seguire la strategia.", reply_markup=get_number_keyboard())
        return ConversationHandler.END

    if scelta in sessione.get("chances_consigliate", []):
        attive = sessione["chances_attive"]
        if scelta in attive:
            attive.remove(scelta)
        else:
            attive.append(scelta)
        await update.message.reply_text(f"Chances attive: {', '.join(attive)}", reply_markup=get_chances_keyboard(sessione["chances_consigliate"]))
    return SELEZIONE_CHANCES

async def inserisci_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numero = int(update.message.text)
    user_id = update.effective_user.id

    if user_id not in sessioni:
        await update.message.reply_text("Devi prima usare /primi15 per iniziare.")
        return

    sessione = sessioni[user_id]
    sessione["numeri"].append(numero)

    esito, saldo, analisi = valuta_estrazione(numero, sessione["chances_attive"], sessione["saldo"])
    sessione["saldo"] = saldo

    testo = f"NUMERO USCITO: {numero}\n"
    for riga in analisi:
        testo += riga + "\n"
    testo += f"\nSaldo totale: {saldo} fiche"

    await update.message.reply_text(testo, reply_markup=get_number_keyboard())

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessione = sessioni.get(user_id)
    if not sessione:
        await update.message.reply_text("Nessuna sessione attiva.")
        return
    await update.message.reply_text(
        f"Chances attive: {', '.join(sessione['chances_attive'])}\n"
        f"Numeri giocati: {len(sessione['numeri'])}\n"
        f"Saldo totale: {sessione['saldo']} fiche"
    )

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessione = sessioni.get(user_id)
    if not sessione:
        await update.message.reply_text("Nessuno storico disponibile.")
        return
    await update.message.reply_text(f"Numeri usciti: {sessione['numeri']}")

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in sessioni or not sessioni[user_id]["numeri"]:
        await update.message.reply_text("Nessun numero da annullare.")
        return
    ultimo = sessioni[user_id]["numeri"].pop()
    await update.message.reply_text(f"Ultimo numero annullato: {ultimo}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("primi15", primi15)],
        states={
            INSERIMENTO_NUMERI: [MessageHandler(filters.Regex(r'^\d+$'), gestisci_numero_iniziale)],
            SELEZIONE_CHANCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleziona_chances)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex(r'^\d+$'), inserisci_numero))

    print("Bot avviato...")
    app.run_polling()