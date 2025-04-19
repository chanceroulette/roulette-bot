import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

CHANCES = {
    "Rosso": {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36},
    "Nero": {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35},
    "Pari": {n for n in range(1, 37) if n % 2 == 0},
    "Dispari": {n for n in range(1, 37) if n % 2 != 0},
    "Manque": set(range(1, 19)),
    "Passe": set(range(19, 37)),
}

def init_box():
    return [1, 1, 1, 1]

user_data = {}

def roulette_keyboard():
    keyboard = []
    for row in range(0, 37, 6):
        keyboard.append([
            InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(row, min(row+6, 37))
        ])
    keyboard.append([InlineKeyboardButton("⏪ Annulla ultima", callback_data="undo")])
    return InlineKeyboardMarkup(keyboard)

def get_win(chance, number):
    return number in CHANCES[chance]

def format_box(box):
    return " | ".join(str(int(x)) for x in box)

def suggest_chances(numbers):
    count = {chance: 0 for chance in CHANCES}
    for n in numbers:
        for chance, values in CHANCES.items():
            if n in values:
                count[chance] += 1
    sorted_chances = sorted(count.items(), key=lambda x: x[1])
    suggestions = [c[0] for c in sorted_chances[:6]]
    return suggestions[:max(2, min(6, len(suggestions)))]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "boxes": {},
        "history": [],
        "active_chances": ["Rosso", "Pari", "Passe"],
        "turns": 0,
        "fiches_won": 0,
        "fiches_lost": 0
    }
    for ch in user_data[user_id]["active_chances"]:
        user_data[user_id]["boxes"][ch] = init_box()
    await update.message.reply_text("Benvenuto in Chance Roulette!", reply_markup=roulette_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data:
        await query.edit_message_text("Per favore avvia il bot con /start")
        return

    data = query.data
    if data == "undo":
        if user_data[user_id]["history"]:
            last = user_data[user_id]["history"].pop()
            user_data[user_id]["boxes"] = last["backup"]
            user_data[user_id]["turns"] -= 1
            user_data[user_id]["fiches_won"] -= last["won"]
            user_data[user_id]["fiches_lost"] -= last["lost"]
            await query.edit_message_text("✅ Ultima operazione annullata.")
        else:
            await query.edit_message_text("⚠️ Nessuna operazione da annullare.")
        return

    number = int(data)
    backup = {ch: user_data[user_id]["boxes"][ch].copy() for ch in user_data[user_id]["active_chances"]}
    turn_won = 0
    turn_lost = 0
    result = f"Hai selezionato il numero {number}\n\n"

    for ch in user_data[user_id]["active_chances"]:
        box = user_data[user_id]["boxes"][ch]
        if not box:
            box.extend(init_box())
        puntata = box[0] + box[-1] if len(box) >= 2 else box[0] * 2
        if get_win(ch, number):
            box.pop(0)
            if box:
                box.pop(-1)
            result += f"✅ {ch}: vinto {puntata} fiches — nuovo box: {format_box(box) or 'svuotato'}\n"
            turn_won += puntata
        else:
            box.append(puntata)
            result += f"❌ {ch}: perso {puntata} fiches — nuovo box: {format_box(box)}\n"
            turn_lost += puntata

    user_data[user_id]["turns"] += 1
    user_data[user_id]["fiches_won"] += turn_won
    user_data[user_id]["fiches_lost"] += turn_lost
    user_data[user_id]["history"].append({
        "number": number,
        "backup": backup,
        "won": turn_won,
        "lost": turn_lost
    })

    netto = user_data[user_id]["fiches_won"] - user_data[user_id]["fiches_lost"]
    result += f"\n🎯 Giocata n. {user_data[user_id]['turns']}"
    result += f"\n💰 Vincite totali: {user_data[user_id]['fiches_won']} fiches"
    result += f"\n❌ Perdite totali: {user_data[user_id]['fiches_lost']} fiches"
    result += f"\n📊 Risultato netto: {netto:+} fiches"

    await query.edit_message_text(result, reply_markup=roulette_keyboard())

async def storico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args or not all(arg.isdigit() and 0 <= int(arg) <= 36 for arg in context.args):
        await update.message.reply_text("Usa il comando così: /storico 5 12 18 24 ... (max 20 numeri)")
        return
    sequence = [int(n) for n in context.args][-20:]
    suggestion = suggest_chances(sequence)
    user_data[user_id]["active_chances"] = suggestion
    user_data[user_id]["boxes"] = {ch: init_box() for ch in suggestion}
    user_data[user_id]["history"].clear()
    user_data[user_id]["turns"] = 0
    user_data[user_id]["fiches_won"] = 0
    user_data[user_id]["fiches_lost"] = 0
    suggerite = ', '.join(suggestion)
    msg = "📊 Analisi completata su {} numeri.\nChances suggerite: {}".format(len(sequence), suggerite)
    await update.message.reply_text(msg, reply_markup=roulette_keyboard())

async def box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        await update.message.reply_text("Usa prima /start")
        return
    msg = "📦 Stato attuale dei box:\n"
    for ch in user_data[user_id]["active_chances"]:
        box = user_data[user_id]["boxes"][ch]
        msg += "{}: {}\n".format(ch, format_box(box) if box else "svuotato")
    await update.message.reply_text(msg, reply_markup=roulette_keyboard())

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "boxes": {},
        "history": [],
        "active_chances": ["Rosso", "Pari", "Passe"],
        "turns": 0,
        "fiches_won": 0,
        "fiches_lost": 0
    }
    for ch in user_data[user_id]["active_chances"]:
        user_data[user_id]["boxes"][ch] = init_box()
    await update.message.reply_text("🔄 Sistema resettato.", reply_markup=roulette_keyboard())

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("box", box))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
