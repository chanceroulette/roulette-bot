import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
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

CHANCE_ORDER = ["Manque", "Pari", "Rosso", "Nero", "Dispari", "Passe"]

def suggest_chances(numbers):
    count = {chance: 0 for chance in CHANCE_ORDER}
    for n in numbers:
        for chance, values in CHANCES.items():
            if n in values:
                count[chance] += 1
    sorted_by_least = sorted(count.items(), key=lambda x: x[1])
    selected = [c[0] for c in sorted_by_least[:6]]
    ordered_selection = [ch for ch in CHANCE_ORDER if ch in selected]
    return ordered_selection[:max(2, len(ordered_selection))]

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "boxes": {},
        "history": [],
        "active_chances": [],
        "turns": 0,
        "fiches_won": 0,
        "fiches_lost": 0,
        "input_sequence": []
    }

    keyboard = []
    for row in range(0, 37, 6):
        keyboard.append([KeyboardButton(str(i)) for i in range(row, min(row+6, 37))])
    keyboard.append([KeyboardButton("✅ Analizza")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🎯 Inserisci i primi 15–20 numeri usciti, uno alla volta.\nQuando hai finito, premi ✅ Analizza.",
        reply_markup=reply_markup
    )

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        await update.message.reply_text("Usa /start per iniziare.")
        return

    if text == "✅ Analizza":
        sequence = user_data[user_id]["input_sequence"]
        if len(sequence) < 10:
            await update.message.reply_text("Devi inserire almeno 10 numeri prima di analizzare.")
            return

        suggestion = suggest_chances(sequence)
        user_data[user_id]["active_chances"] = suggestion
        user_data[user_id]["boxes"] = {ch: init_box() for ch in suggestion}
        user_data[user_id]["input_sequence"] = []
        suggerite = ", ".join(suggestion)

        await update.message.reply_text(
            f"📊 Analisi completata su {len(sequence)} numeri.\n"
            f"Chances suggerite: {suggerite}\n\nPuoi iniziare ora!",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text("Clicca i numeri tramite i bottoni per giocare:", reply_markup=roulette_keyboard())
        return

    if text.isdigit() and 0 <= int(text) <= 36:
        user_data[user_id]["input_sequence"].append(int(text))
        await update.message.reply_text(f"✅ Inserito: {text} ({len(user_data[user_id]['input_sequence'])} numeri finora)")
    else:
        await update.message.reply_text("Inserisci solo numeri da 0 a 36 o premi ✅ Analizza.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data or not user_data[user_id]["active_chances"]:
        await query.edit_message_text("Usa prima il comando /start e inserisci i numeri iniziali.")
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
            stato = format_box(box) if box else "svuotato"
            result += f"✅ {ch}: vinto {puntata} fiches — nuovo box: {stato}\n"
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

    result += "\n\n🔜 Prossima puntata:"
    for ch in user_data[user_id]["active_chances"]:
        box = user_data[user_id]["boxes"][ch]
        if not box:
            box = init_box()
        prossima = box[0] + box[-1] if len(box) >= 2 else box[0] * 2
        result += f"\n- {ch}: {prossima} fiches"

    await query.edit_message_text(result, reply_markup=roulette_keyboard())

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "boxes": {},
        "history": [],
        "active_chances": [],
        "turns": 0,
        "fiches_won": 0,
        "fiches_lost": 0,
        "input_sequence": []
    }
    await update.message.reply_text("🔄 Sistema resettato.\nUsa /start per reiniziare.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_input))
    app.run_polling()

if __name__ == "__main__":
    main()
