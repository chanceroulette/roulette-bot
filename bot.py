import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
import os

# TOKEN da variabile ambiente
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Logging
logging.basicConfig(level=logging.INFO)

# Costanti
ADMIN_ID = 5033904813
MAX_NUMERI_INIZIALI = 15

# Dati utente
user_data = {}

# Classificazioni roulette
ROSSI = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
NERI = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
PARI = {i for i in range(1, 37) if i % 2 == 0}
DISPARI = {i for i in range(1, 37) if i % 2 != 0}
MANQUE = {i for i in range(1, 19)}
PASSE = {i for i in range(19, 37)}

# Funzioni di utilità
def get_keyboard_numerica():
    keys = [[str(i) for i in range(row, row+6)] for row in range(1, 37, 6)]
    keys.append(["0", "Annulla", "Menu"])
    return ReplyKeyboardMarkup(keys, resize_keyboard=True)

def reset_user(user_id):
    user_data[user_id] = {
        "numeri_iniziali": [],
        "sessione": [],
        "start_time": datetime.now(),
        "saldo": 0,
        "vinte": 0,
        "perse": 0
    }

def analizza_chances(numeri):
    counts = {"rosso": 0, "nero": 0, "pari": 0, "dispari": 0, "manque": 0, "passe": 0}
    for n in numeri:
        if n in ROSSI:
            counts["rosso"] += 1
        elif n in NERI:
            counts["nero"] += 1
        if n in PARI:
            counts["pari"] += 1
        else:
            counts["dispari"] += 1
        if n in MANQUE:
            counts["manque"] += 1
        else:
            counts["passe"] += 1
    suggerite = sorted(counts, key=counts.get, reverse=True)[:3]
    return suggerite

# Comandi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reset_user(user_id)
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        f"Copyright © {datetime.now().year} Fabio Felice Cudia"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/report", "/storico", "/annulla_ultima"],
        ["/id", "/help"]
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append(["/admin"])
    await update.message.reply_text("Menu comandi:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a tracciare la strategia dei box alla roulette.\n"
        "Inserisci i numeri estratti tramite tastiera e analizza il tuo saldo, performance e report.\n"
        "Per contatti: info@trilium-bg.com\n"
        f"© {datetime.now().year} Fabio Felice Cudia"
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id, {})
    giocate = len(data.get("sessione", []))
    vinte = data.get("vinte", 0)
    perse = data.get("perse", 0)
    saldo = data.get("saldo", 0)
    tempo = datetime.now() - data.get("start_time", datetime.now())
    minuti, secondi = divmod(tempo.seconds, 60)
    await update.message.reply_text(
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {giocate}\n"
        f"Vinte: {vinte} | Perse: {perse}\n"
        f"Saldo: {saldo:+} fiche\n"
        f"Tempo di gioco: {minuti} min {secondi} sec"
    )

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numeri = user_data.get(user_id, {}).get("sessione", [])
    if numeri:
        await update.message.reply_text(f"Numeri registrati: {', '.join(map(str, numeri))}")
    else:
        await update.message.reply_text("Nessun numero registrato.")

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_data.get(user_id, {}).get("sessione"):
        rimosso = user_data[user_id]["sessione"].pop()
        await update.message.reply_text(f"Ultimo numero rimosso: {rimosso}")
    else:
        await update.message.reply_text("Nessun numero da rimuovere.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Accesso admin autorizzato.")
    else:
        await update.message.reply_text("Comando non valido.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        reset_user(user_id)

    msg = update.message.text.strip()
    if not msg.isdigit():
        return

    numero = int(msg)
    data = user_data[user_id]

    if len(data["numeri_iniziali"]) < MAX_NUMERI_INIZIALI:
        data["numeri_iniziali"].append(numero)
        if len(data["numeri_iniziali"]) < MAX_NUMERI_INIZIALI:
            await update.message.reply_text(f"Hai inserito {len(data['numeri_iniziali'])}/{MAX_NUMERI_INIZIALI} numeri.")
        else:
            chances = analizza_chances(data["numeri_iniziali"])
            await update.message.reply_text(
                f"Hai inserito i primi {MAX_NUMERI_INIZIALI} numeri.\n"
                f"Chances suggerite: {', '.join(chances)}"
            )
        return

    data["sessione"].append(numero)
    output = f"NUMERO USCITO: {numero}\n"

    # Simulazione esiti su 3 chances fisse: Rosso, Pari, Passe
    puntate = {"rosso": 3, "pari": 3, "passe": 3}
    saldo_giro = 0

    if numero in ROSSI:
        esito = -puntate["rosso"]
        output += f"Rosso: puntate {puntate['rosso']} fiche → esito: {esito}\n"
        saldo_giro += esito
        data["perse"] += 1
    else:
        esito = +puntate["rosso"]
        output += f"Rosso: puntate {puntate['rosso']} fiche → esito: {esito}\n"
        saldo_giro += esito
        data["vinte"] += 1

    if numero in PARI:
        esito = +puntate["pari"]
        output += f"Pari: puntate {puntate['pari']} fiche → esito: {esito}\n"
        saldo_giro += esito
        data["vinte"] += 1
    else:
        esito = -puntate["pari"]
        output += f"Pari: puntate {puntate['pari']} fiche → esito: {esito}\n"
        saldo_giro += esito
        data["perse"] += 1

    if numero in PASSE:
        esito = +puntate["passe"]
        output += f"Passe: puntate {puntate['passe']} fiche → esito: {esito}\n"
        saldo_giro += esito
        data["vinte"] += 1
    else:
        esito = -puntate["passe"]
        output += f"Passe: puntate {puntate['passe']} fiche → esito: {esito}\n"
        saldo_giro += esito
        data["perse"] += 1

    data["saldo"] += saldo_giro
    output += f"\nSaldo totale: {data['saldo']} fiche"

    await update.message.reply_text(output)

# Main
if __name__ == "__main__":
    import asyncio

    async def main():
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("menu", menu))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("report", report))
        app.add_handler(CommandHandler("storico", storico))
        app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
        app.add_handler(CommandHandler("id", id_command))
        app.add_handler(CommandHandler("admin", admin))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await app.run_polling()

    asyncio.run(main())