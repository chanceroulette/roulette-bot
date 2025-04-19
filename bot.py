import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

from strategy import (
    suggerisci_chances,
    build_session_report,
    calcola_esito,
)
from keyboards import (
    menu_keyboard,
    number_keyboard,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813

user_data = {}

HELP_TEXT = (
    "Questo bot ti aiuta a seguire la strategia dei box sulla roulette europea.\n\n"
    "Comandi:\n"
    "/menu – Mostra i comandi\n"
    "/primi15 – Inserisci 15 numeri iniziali per le statistiche\n"
    "/modalita_inserimento – Avvia inserimento numeri\n"
    "/report – Vedi lo stato attuale\n"
    "/storico – Visualizza i numeri usciti\n"
    "/annulla_ultima – Annulla ultima estrazione\n"
    "/id – Il tuo ID Telegram\n"
    "/admin – Solo per l'amministratore"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_data:
        user_data[uid] = {
            "session": [],
            "numeri_iniziali": [],
            "chances_attive": [],
            "box": {},
            "saldo": 0,
            "games": 0,
            "wins": 0,
            "losses": 0,
            "inserimento_iniziale": False,
            "modalita_inserimento": False,
        }
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\nScrivi /menu per iniziare oppure /help per i comandi.",
        reply_markup=menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, reply_markup=menu_keyboard())

async def mostra_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu comandi:", reply_markup=menu_keyboard())

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    seq = user_data[uid]["session"]
    if seq:
        testo = "Numeri usciti: " + ", ".join(str(n) for n in seq)
    else:
        testo = "Nessun numero registrato."
    await update.message.reply_text(testo, reply_markup=menu_keyboard())

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if user_data[uid]["session"]:
        last = user_data[uid]["session"].pop()
        await update.message.reply_text(f"Annullata estrazione: {last}", reply_markup=menu_keyboard())
    else:
        await update.message.reply_text("Nessuna estrazione da annullare.", reply_markup=menu_keyboard())

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    testo = build_session_report(user_data[uid])
    await update.message.reply_text(testo, reply_markup=menu_keyboard())

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    d = user_data[uid]
    d["numeri_iniziali"] = []
    d["inserimento_iniziale"] = True
    d["modalita_inserimento"] = False
    await update.message.reply_text(
        "Inserisci i primi 15 numeri uno alla volta.",
        reply_markup=number_keyboard(),
    )

async def modalita_inserimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    d = user_data[uid]
    if not d["chances_attive"]:
        await update.message.reply_text("Devi prima usare /primi15 per generare le chances consigliate.")
        return
    d["modalita_inserimento"] = True
    d["inserimento_iniziale"] = False
    await update.message.reply_text("Modalità inserimento attiva.", reply_markup=number_keyboard())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        msg = f"⚙️ Pannello Admin attivo.\nUtenti: {len(user_data)}"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Non sei autorizzato.", reply_markup=menu_keyboard())

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text
    if not testo.isdigit():
        return
    n = int(testo)
    uid = update.effective_user.id
    d = user_data[uid]

    if d["inserimento_iniziale"]:
        d["numeri_iniziali"].append(n)
        cnt = len(d["numeri_iniziali"])
        if cnt < 15:
            await update.message.reply_text(f"Numero {n} registrato. Inserisci il prossimo ({cnt+1}/15):", reply_markup=number_keyboard())
        else:
            chance = suggerisci_chances(d["numeri_iniziali"])
            d["chances_attive"] = chance
            for ch in chance:
                d["box"][ch] = [1, 1, 1, 1]
            await update.message.reply_text(
                f"Statistiche completate. Chances consigliate: {', '.join(chance)}\nOra usa /modalita_inserimento",
                reply_markup=menu_keyboard(),
            )
            d["inserimento_iniziale"] = False
        return

    if d["modalita_inserimento"]:
        d["session"].append(n)
        d["games"] += 1
        risultato = calcola_esito(n, d)
        await update.message.reply_text(risultato, reply_markup=menu_keyboard())
    else:
        await update.message.reply_text("Attiva /modalita_inserimento prima di inserire numeri.", reply_markup=menu_keyboard())

# MAIN
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", mostra_id))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("primi15", primi15))
    app.add_handler(CommandHandler("modalita_inserimento", modalita_inserimento))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\d{1,2}$"), handle_number))

    print("Bot avviato")
    asyncio.run(app.run_polling())