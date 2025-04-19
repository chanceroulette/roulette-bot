import os
import json
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

from flask import Flask
import threading

CHANCES = ["Rosso", "Nero", "Pari", "Dispari", "Manque", "Passe"]
rosso = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
nero = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

USER_DATA_DIR = "dati_utenti"
os.makedirs(USER_DATA_DIR, exist_ok=True)

def user_file(user_id): return os.path.join(USER_DATA_DIR, f"{user_id}.json")

def save_user_data(user_id, data):
    with open(user_file(user_id), "w") as f:
        json.dump(data, f)

def load_user_data(user_id):
    path = user_file(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {
        "boxes": {},
        "chances": [],
        "history": [],
        "fiches_vinte": 0,
        "fiches_perse": 0,
        "giocate": 0,
        "inserimento": False,
        "inizio": time.time(),
        "last_state": None,
        "is_pro": False
    }

def is_win(chance, number):
    if number == 0: return False
    if chance == "Rosso": return number in rosso
    if chance == "Nero": return number in nero
    if chance == "Pari": return number % 2 == 0
    if chance == "Dispari": return number % 2 != 0
    if chance == "Manque": return 1 <= number <= 18
    if chance == "Passe": return 19 <= number <= 36
    return False

def get_keyboard():
    layout = []
    row = []
    for i in range(1, 37):
        row.append(KeyboardButton(str(i)))
        if len(row) == 6:
            layout.append(row)
            row = []
    if row: layout.append(row)
    layout.append([KeyboardButton("0"), KeyboardButton("Menu")])
    return ReplyKeyboardMarkup(layout, resize_keyboard=True)

def suggest_chances(numbers):
    counts = {c: 0 for c in CHANCES}
    for n in numbers:
        for c in CHANCES:
            if is_win(c, n): counts[c] += 1
    return sorted(counts, key=counts.get)[:3]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_user_data(user_id)

    data["boxes"] = {}
    data["chances"] = []
    data["history"] = []
    data["fiches_vinte"] = 0
    data["fiches_perse"] = 0
    data["giocate"] = 0
    data["inserimento"] = False
    data["inizio"] = time.time()

    save_user_data(user_id, data)

    await update.message.reply_text(
        "Benvenuto! Inserisci i primi 15 numeri usciti per inizializzare il sistema.",
        reply_markup=get_keyboard()
    )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_user_data(user_id)
    text = update.message.text.strip()

    if text.lower() == "menu":
        await update.message.reply_text(
            "/report - Report attuale\n/annulla_ultima - Annulla ultima\n/storico - Mostra numeri usciti"
        )
        return

    if not text.isdigit():
        return

    number = int(text)
    if not data["inserimento"]:
        data["history"].append(number)
        if len(data["history"]) == 15:
            suggerite = suggest_chances(data["history"])
            context.user_data["scelte"] = []
            buttons = [[InlineKeyboardButton(c, callback_data=f"attiva_{c}")] for c in CHANCES]
            buttons.append([InlineKeyboardButton("✅ Conferma", callback_data="conferma_chances")])
            await update.message.reply_text(
                f"Ti consiglio: {', '.join(suggerite)}\nSeleziona le chances:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await update.message.reply_text(f"Numeri inseriti: {len(data['history'])}/15")
        save_user_data(user_id, data)
        return

    if not data.get("is_pro") and data["giocate"] >= 15:
        await update.message.reply_text("Hai raggiunto il limite di 15 giocate. Passa alla versione PRO.")
        return

    data["last_state"] = json.dumps(data)

    msg = f"Numero inserito: {number}\n"
    fiches_vinte = 0
    fiches_perse = 0
    prossime = []

    for chance in data["chances"]:
        box = data["boxes"].get(chance, [1, 1, 1, 1])
        puntata = box[0] if len(box) == 1 else box[0] + box[-1]
        if is_win(chance, number):
            fiches_vinte += puntata
            msg += f"{chance}: VINTO {puntata}\n"
            if len(box) >= 2:
                box.pop()
                box.pop(0)
            else:
                box.clear()
        else:
            fiches_perse += puntata
            box.append(puntata)
            msg += f"{chance}: PERSO {puntata}\n"
        if not box:
            box = [1, 1, 1, 1]
        data["boxes"][chance] = box
        p = box[0] if len(box) == 1 else box[0] + box[-1]
        prossime.append(f"{chance}: {p}")

    data["fiches_vinte"] += fiches_vinte
    data["fiches_perse"] += fiches_perse
    data["giocate"] += 1
    save_user_data(user_id, data)

    saldo = data["fiches_vinte"] - data["fiches_perse"]
    msg += f"\nGiro: +{fiches_vinte} / -{fiches_perse} fiche"
    msg += f"\nTotale: +{data['fiches_vinte']} / -{data['fiches_perse']} → saldo: {saldo:+}"
    msg += f"\nGiocate totali: {data['giocate']}"
    msg += "\n\nProssima puntata:\n" + "\n".join(prossime)

    await update.message.reply_text(msg)

async def seleziona_chances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_user_data(user_id)
    await query.answer()
    d = query.data
    if d.startswith("attiva_"):
        c = d.replace("attiva_", "")
        if c in context.user_data["scelte"]:
            context.user_data["scelte"].remove(c)
        else:
            context.user_data["scelte"].append(c)
        await query.edit_message_text(
            f"Selezionate: {', '.join(context.user_data['scelte'])}",
            reply_markup=query.message.reply_markup
        )
    elif d == "conferma_chances":
        data["chances"] = context.user_data["scelte"]
        data["boxes"] = {c: [1, 1, 1, 1] for c in data["chances"]}
        data["inserimento"] = True
        save_user_data(user_id, data)
        await query.edit_message_text("Chances attivate. Inserisci i numeri.")
        await query.message.reply_text("Modalità attiva.", reply_markup=get_keyboard())

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_user_data(user_id)
    durata = int(time.time() - data["inizio"])
    minuti = durata // 60
    secondi = durata % 60
    saldo = data["fiches_vinte"] - data["fiches_perse"]
    await update.message.reply_text(
        f"REPORT SESSIONE\n\n"
        f"Giocate totali: {data['giocate']}\n"
        f"Vinte: {data['fiches_vinte']} | Perse: {data['fiches_perse']}\n"
        f"Saldo: {saldo:+} fiche\n"
        f"Tempo di gioco: {minuti} min {secondi} sec\n"
        f"Chances attive: {', '.join(data['chances'])}"
    )

async def annulla_ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    path = user_file(user_id)
    data = load_user_data(user_id)
    if not data["last_state"]:
        await update.message.reply_text("Non puoi annullare ora.")
        return
    with open(path, "w") as f:
        f.write(data["last_state"])
    await update.message.reply_text("Ultima giocata annullata.")

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_user_data(user_id)
    numeri = data.get("history", [])
    if not numeri:
        await update.message.reply_text("Nessun numero registrato.")
    else:
        await update.message.reply_text("Numeri inseriti:\n" + ", ".join(str(n) for n in numeri))

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CallbackQueryHandler(seleziona_chances))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    app.run_polling()

# --- WEB SERVER PER RENDER + UPTIMEROBOT ---
web_app = Flask(__name__)
@web_app.route('/')
def ping(): return 'Bot attivo'

def run_web():
    web_app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web).start()

if __name__ == "__main__":
    main()