import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
import os

# Configura il logging
logging.basicConfig(level=logging.INFO)

# Carica il token dalla variabile d'ambiente
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = "5033904813"
ADMIN_PASSWORD = "@@Zaq12wsx@@25"

# Stati utente
user_data = {}

# Definizione delle chances semplici
chances = {
    "rosso": {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "nero": {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35},
    "pari": {n for n in range(1, 37) if n % 2 == 0},
    "dispari": {n for n in range(1, 37) if n % 2 != 0},
    "manque": {n for n in range(1, 19)},
    "passe": {n for n in range(19, 37)}
}

# Strategia per ogni utente
def reset_session(user_id):
    user_data[user_id] = {
        "boxes": {chance: [1, 1, 1, 1] for chance in chances},
        "storico": [],
        "giocate": [],
        "saldo": 0,
        "inizio": datetime.now(),
        "primi_15": [],
        "modalita_primi_15": False,
        "admin": False
    }

# Tastiera con numeri roulette
def get_keyboard():
    buttons = [[KeyboardButton(str(i)) for i in range(j, j+6)] for j in range(1, 37, 6)]
    buttons.append([KeyboardButton("0"), KeyboardButton("Annulla"), KeyboardButton("Menu")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Calcola esiti di una giocata
def calcola_esito(user_id, numero):
    messaggio = f"NUMERO USCITO: {numero}\n"
    totale = 0
    for chance, numeri in chances.items():
        box = user_data[user_id]["boxes"][chance]
        puntata = box[0] + box[-1] if len(box) > 1 else box[0]
        if numero in numeri:
            messaggio += f"{chance.capitalize()}: puntate {puntata} fiche → esito: +{puntata}\n"
            totale += puntata
            box = box[1:-1] if len(box) > 1 else []
        else:
            messaggio += f"{chance.capitalize()}: puntate {puntata} fiche → esito: -{puntata}\n"
            totale -= puntata
            box.append(puntata)
        if not box:
            box = [1, 1, 1, 1]
        user_data[user_id]["boxes"][chance] = box
    user_data[user_id]["saldo"] += totale
    messaggio += f"\nSaldo totale: {user_data[user_id]['saldo']} fiche"
    return messaggio

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        reset_session(user_id)
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Scrivi /menu per iniziare oppure usa i comandi manuali.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

# Comando /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu comandi:", reply_markup=ReplyKeyboardMarkup([
        ["/report", "/storico", "/annulla_ultima"],
        ["/id", "/help", "/admin"],
        ["/primi15"]
    ], resize_keyboard=True))

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot ti aiuta a seguire la strategia dei box sulla roulette europea.\n"
        "Puoi inserire i numeri e ricevere suggerimenti per ogni chance attiva.\n"
        "Ogni utente ha la propria sessione separata.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia"
    )

# Comando /id
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Il tuo ID Telegram è: {user_id}")

# Comando /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) == ADMIN_ID:
        await update.message.reply_text("Inserisci la password di amministrazione:")
        context.user_data["awaiting_password"] = True
    else:
        await update.message.reply_text("Comando non valido.")

# Password per login admin
async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get("awaiting_password"):
        if update.message.text == ADMIN_PASSWORD:
            user_data[user_id]["admin"] = True
            await update.message.reply_text("Accesso amministratore riuscito.")
        else:
            await update.message.reply_text("Password errata.")
        context.user_data["awaiting_password"] = False

# Comando /report
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessione = user_data[user_id]
    vinte = sum(1 for g in sessione["giocate"] if g["esito"] > 0)
    perse = sum(1 for g in sessione["giocate"] if g["esito"] < 0)
    tempo = datetime.now() - sessione["inizio"]
    active_chances = [c for c, b in sessione["boxes"].items() if b]
    await update.message.reply_text(
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {len(sessione['giocate'])}\n"
        f"Vinte: {vinte} | Perse: {perse}\n"
        f"Saldo: {sessione['saldo']} fiche\n"
        f"Tempo di gioco: {tempo.seconds // 60} min {tempo.seconds % 60} sec\n"
        f"Chances attive: {', '.join(active_chances)}"
    )

# Comando /storico
async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storico = user_data[user_id]["storico"]
    await update.message.reply_text("Numeri usciti: " + ", ".join(map(str, storico)) if storico else "Nessun numero registrato.")

# Comando /annulla_ultima
async def annulla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_data[user_id]["storico"]:
        user_data[user_id]["storico"].pop()
        await update.message.reply_text("Ultimo numero annullato.")
    else:
        await update.message.reply_text("Nessun numero da annullare.")

# Comando /primi15
async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["primi_15"] = []
    user_data[user_id]["modalita_primi_15"] = True
    await update.message.reply_text("Inserisci i 15 numeri iniziali uno alla volta.", reply_markup=get_keyboard())

# Messaggi (inserimento numeri)
async def inserisci_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    testo = update.message.text

    if testo.lower() in ["menu"]:
        await menu(update, context)
        return
    if testo.lower() == "annulla":
        await annulla(update, context)
        return

    if not testo.isdigit():
        await update.message.reply_text("Inserisci un numero valido.")
        return

    numero = int(testo)
    if numero < 0 or numero > 36:
        await update.message.reply_text("Numero fuori intervallo.")
        return

    if user_id not in user_data:
        reset_session(user_id)

    sessione = user_data[user_id]

    # Se siamo nella fase di inserimento dei 15 iniziali
    if sessione["modalita_primi_15"]:
        sessione["primi_15"].append(numero)
        if len(sessione["primi_15"]) < 15:
            await update.message.reply_text(f"Numero {numero} registrato. Inserisci il prossimo ({len(sessione['primi_15'])+1}/15):", reply_markup=get_keyboard())
        else:
            sessione["modalita_primi_15"] = False
            stat = {k: sum(1 for n in sessione["primi_15"] if n in v) for k, v in chances.items()}
            suggerite = sorted(stat.items(), key=lambda x: x[1], reverse=True)[:3]
            consigliate = [s[0] for s in suggerite]
            await update.message.reply_text(
                f"Tutti i 15 numeri iniziali registrati: {sessione['primi_15']}\n"
                f"Chances consigliate: {', '.join(consigliate)}\n\n"
                f"Da ora in poi inserisci i nuovi numeri per seguire la strategia.",
                reply_markup=get_keyboard()
            )
    else:
        sessione["storico"].append(numero)
        esito = calcola_esito(user_id, numero)
        sessione["giocate"].append({"numero": numero, "esito": sessione["saldo"]})
        await update.message.reply_text(esito, reply_markup=get_keyboard())

# MAIN
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla))
    app.add_handler(CommandHandler("primi15", primi15))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_numero))
    app.add_handler(MessageHandler(filters.TEXT, password_handler))
    print("Bot avviato...")
    app.run_polling()