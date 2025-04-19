import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813

# === CONFIGURAZIONE ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === DATI STRATEGIA ===
user_data = {}
CHANCES = ["rosso", "nero", "pari", "dispari", "manque", "passe"]
CHANCE_POOL = {
    "rosso": {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "nero": {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35},
    "pari": {n for n in range(1, 37) if n % 2 == 0},
    "dispari": {n for n in range(1, 37) if n % 2 == 1},
    "manque": set(range(1, 19)),
    "passe": set(range(19, 37)),
}

# === FUNZIONI LOGICA STRATEGIA ===
def crea_box():
    return [1, 1, 1, 1]

def calcola_puntata(box):
    if len(box) == 1:
        return box[0]
    return box[0] + box[-1]

def aggiorna_box(box, win, puntata):
    if win:
        if len(box) == 1:
            box = []
        else:
            box = box[1:-1]
    else:
        box.append(puntata)
    if not box:
        box = crea_box()
    return box

def suggerisci_chances(numeri):
    counts = {ch: 0 for ch in CHANCES}
    for n in numeri:
        for ch, vals in CHANCE_POOL.items():
            if n in vals:
                counts[ch] += 1
    return sorted(counts, key=counts.get)[:3]

# === HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data[uid] = {
        "bankroll": 0,
        "history": [],
        "first15": [],
        "boxes": {},
        "chances": [],
        "total_profit": 0
    }
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Usa /bankroll per impostare le fiches e /primi15 per avviare la strategia.\n"
        "Per supporto: info@trilium-bg.com"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Questo bot segue la tua strategia di roulette.\n"
        "1. /bankroll → Imposta fiches iniziali\n"
        "2. /primi15 → Inserisci almeno 15 numeri\n"
        "3. /modalita_inserimento → Inserisci i numeri e ricevi il report\n"
        "Usa /report per vedere l’andamento.\n\n"
        "Supporto: info@trilium-bg.com"
    )

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def bankroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Inserisci il bankroll iniziale (numero di fiches):")
    return 1

async def set_bankroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        user_data[uid]["bankroll"] = int(update.message.text)
        await update.message.reply_text("Bankroll impostato. Ora inserisci almeno 15 numeri con /primi15.")
        return ConversationHandler.END
    except:
        await update.message.reply_text("Inserisci un numero valido.")
        return 1

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Inserisci i numeri della roulette uno alla volta. Minimo 15. Quando hai finito, invia 'Fine'")
    return 2

async def raccogli_numeri(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message.text.strip()
    if msg.lower() == "fine":
        numeri = user_data[uid]["first15"]
        if len(numeri) < 15:
            return await update.message.reply_text("Inserisci almeno 15 numeri.")
        consigliate = suggerisci_chances(numeri)
        user_data[uid]["chances"] = consigliate
        user_data[uid]["boxes"] = {ch: crea_box() for ch in consigliate}
        await update.message.reply_text(f"Chances suggerite: {', '.join(consigliate)}. Usa /modalita_inserimento per continuare.")
        return ConversationHandler.END
    try:
        numero = int(msg)
        if 0 <= numero <= 36:
            user_data[uid]["first15"].append(numero)
            await update.message.reply_text(f"{len(user_data[uid]['first15'])} numeri inseriti.")
        else:
            await update.message.reply_text("Numero fuori range.")
    except:
        await update.message.reply_text("Numero non valido.")
    return 2

async def modalita_inserimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Modalità inserimento attiva. Invia un numero tra 0 e 36, oppure 'Stop' per terminare.")
    return 3

async def inserisci_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message.text.strip()
    if msg.lower() == "stop":
        await update.message.reply_text("Sessione terminata.")
        return ConversationHandler.END
    try:
        numero = int(msg)
        if not (0 <= numero <= 36):
            return await update.message.reply_text("Numero fuori range.")
        user_data[uid]["history"].append(numero)
        boxes = user_data[uid]["boxes"]
        chances = user_data[uid]["chances"]
        report = [f"Numero uscito: {numero}"]
        profitto = 0
        for ch in chances:
            box = boxes[ch]
            bet = calcola_puntata(box)
            vinta = numero in CHANCE_POOL[ch]
            box = aggiorna_box(box, vinta, bet)
            boxes[ch] = box
            risultato = bet if vinta else -bet
            profitto += risultato
            report.append(f"{ch.capitalize()}: puntata {bet} → {'+%d' % risultato if risultato > 0 else risultato}")
        user_data[uid]["total_profit"] += profitto
        user_data[uid]["bankroll"] += profitto
        report.append(f"Profitto giro: {profitto:+}")
        report.append(f"Totale: {user_data[uid]['total_profit']} | Bankroll: {user_data[uid]['bankroll']}")
        await update.message.reply_text("\n".join(report))
    except:
        await update.message.reply_text("Errore nell'inserimento.")
    return 3

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    d = user_data[uid]
    await update.message.reply_text(
        f"Bankroll iniziale: {d['bankroll']}\n"
        f"Profitto totale: {d['total_profit']}\n"
        f"Numeri giocati: {d['history']}"
    )

# === CONVERSAZIONI ===
app = ApplicationBuilder().token(TOKEN).build()
conv_bankroll = ConversationHandler(
    entry_points=[CommandHandler("bankroll", bankroll)],
    states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_bankroll)]},
    fallbacks=[]
)
conv_primi15 = ConversationHandler(
    entry_points=[CommandHandler("primi15", primi15)],
    states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, raccogli_numeri)]},
    fallbacks=[]
)
conv_inserimento = ConversationHandler(
    entry_points=[CommandHandler("modalita_inserimento", modalita_inserimento)],
    states={3: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_numero)]},
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("id", id_cmd))
app.add_handler(CommandHandler("report", report))
app.add_handler(conv_bankroll)
app.add_handler(conv_primi15)
app.add_handler(conv_inserimento)

if __name__ == "__main__":
    app.run_polling()