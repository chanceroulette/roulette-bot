import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813

CHANCES = {
    "Rosso": {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36},
    "Nero": {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35},
    "Pari": {n for n in range(1, 37) if n % 2 == 0},
    "Dispari": {n for n in range(1, 37) if n % 2 != 0},
    "Manque": set(range(1, 19)),
    "Passe": set(range(19, 37)),
}
CHANCE_ORDER = ["Manque", "Pari", "Rosso", "Nero", "Dispari", "Passe"]
user_data = {}
user_ids = set()

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

def build_keyboard():
    keyboard = []
    for row in range(0, 37, 6):
        keyboard.append([KeyboardButton(str(i)) for i in range(row, min(row + 6, 37))])
    keyboard.append([KeyboardButton("⏪ Annulla ultima"), KeyboardButton("✅ Analizza")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def build_chance_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton(ch)] for ch in CHANCE_ORDER
    ] + [[KeyboardButton("✅ Conferma")]], resize_keyboard=True)

def get_win(chance, number):
    return number in CHANCES[chance]

def format_box(box):
    return " | ".join(str(int(x)) for x in box)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_ids.add(user_id)
    user_data[user_id] = {
        "boxes": {},
        "history": [],
        "active_chances": [],
        "suggested_chances": [],
        "turns": 0,
        "fiches_won": 0,
        "fiches_lost": 0,
        "input_sequence": [],
        "is_ready": False,
        "pending_selection": False
    }
    await update.message.reply_text(
        "🎯 Inserisci i primi 15–20 numeri usciti, uno alla volta.\nQuando hai finito, premi ✅ Analizza.",
        reply_markup=build_keyboard()
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Comandi disponibili:\n"
        "/start – Inizia nuova sessione\n"
        "/reset – Azzera tutto\n"
        "/menu – Mostra i comandi\n"
        "/help – Info sul bot\n"
        "/statistiche – (solo admin)\n"
        "/utenti – (solo admin)",
        reply_markup=build_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎰 Benvenuto in Chance Roulette!\n\n"
        "Questo bot ti aiuta a seguire una strategia matematica sulla roulette basata sulle chances semplici (Rosso/Nero, Pari/Dispari...). "
        "Inserisci i primi 15–20 numeri per analizzare quali chances sono più favorevoli. Poi scegli quali attivare e gioca con gestione automatica dei box."
    )
    async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_ids.add(user_id)
    text = update.message.text.strip()

    if user_id not in user_data:
        await update.message.reply_text("Usa /start per iniziare.")
        return

    state = user_data[user_id]

    if state["pending_selection"] and text in CHANCE_ORDER:
        if text not in state["active_chances"]:
            state["active_chances"].append(text)
            await update.message.reply_text(f"✅ Aggiunta: {text}", reply_markup=build_chance_keyboard())
        else:
            state["active_chances"].remove(text)
            await update.message.reply_text(f"❌ Rimossa: {text}", reply_markup=build_chance_keyboard())
        return

    if state["pending_selection"] and text == "✅ Conferma":
        if len(state["active_chances"]) < 2:
            await update.message.reply_text("⚠️ Devi selezionare almeno 2 chances.")
            return
        state["boxes"] = {ch: init_box() for ch in state["active_chances"]}
        state["pending_selection"] = False
        state["is_ready"] = True
        await update.message.reply_text("✅ Chances confermate! Ora puoi iniziare a giocare.", reply_markup=build_keyboard())
        return

    if text == "✅ Analizza":
        seq = state["input_sequence"]
        if len(seq) < 10:
            await update.message.reply_text("⚠️ Inserisci almeno 10 numeri prima di analizzare.")
            return
        suggested = suggest_chances(seq)
        state["suggested_chances"] = suggested
        state["active_chances"] = []
        state["input_sequence"] = []
        state["history"] = []
        state["turns"] = 0
        state["fiches_won"] = 0
        state["fiches_lost"] = 0
        state["pending_selection"] = True
        await update.message.reply_text(
            f"📊 Analisi completata. Chances consigliate: {', '.join(suggested)}.\n"
            "🔘 Seleziona le chances che vuoi usare. Premi ✅ Conferma quando sei pronto.",
            reply_markup=build_chance_keyboard()
        )
        return

    if text == "⏪ Annulla ultima":
        if not state["is_ready"]:
            await update.message.reply_text("⚠️ Non hai ancora iniziato a giocare.", reply_markup=build_keyboard())
            return
        if state["history"]:
            last = state["history"].pop()
            state["boxes"] = {k: v.copy() for k, v in last["backup"].items()}
            state["turns"] -= 1
            state["fiches_won"] -= last["won"]
            state["fiches_lost"] -= last["lost"]
            await update.message.reply_text("✅ Ultima giocata annullata.", reply_markup=build_keyboard())
        else:
            await update.message.reply_text("⚠️ Nessuna giocata da annullare.", reply_markup=build_keyboard())
        return

    if not text.isdigit() or not (0 <= int(text) <= 36):
        await update.message.reply_text("Inserisci un numero valido (0–36), oppure usa i pulsanti.")
        return

    number = int(text)

    if not state["is_ready"]:
        state["input_sequence"].append(number)
        await update.message.reply_text(f"✅ Inserito: {number} ({len(state['input_sequence'])} numeri finora)", reply_markup=build_keyboard())
        return

    if not state["active_chances"]:
        await update.message.reply_text("⚠️ Prima devi selezionare le chances e confermare.", reply_markup=build_keyboard())
        return

    backup = {ch: state["boxes"][ch].copy() for ch in state["active_chances"]}
    turn_won = turn_lost = 0
    result = f"Hai selezionato il numero {number}\n\n"

    for ch in state["active_chances"]:
        box = state["boxes"][ch]
        if not box:
            box = init_box()
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

    state["turns"] += 1
    state["fiches_won"] += turn_won
    state["fiches_lost"] += turn_lost
    state["history"].append({
        "number": number,
        "backup": backup,
        "won": turn_won,
        "lost": turn_lost
    })

    netto = state["fiches_won"] - state["fiches_lost"]
    result += f"\n🎯 Giocata n. {state['turns']}"
    result += f"\n💰 Vincite totali: {state['fiches_won']} fiches"
    result += f"\n❌ Perdite totali: {state['fiches_lost']} fiches"
    result += f"\n📊 Risultato netto: {netto:+} fiches"
    result += "\n\n🔜 Prossima puntata:"
    for ch in state["active_chances"]:
        box = state["boxes"][ch]
        if not box:
            box = init_box()
        prossima = box[0] + box[-1] if len(box) >= 2 else box[0] * 2
        result += f"\n- {ch}: {prossima} fiches"

    await update.message.reply_text(result, reply_markup=build_keyboard())

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def statistiche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accesso negato.")
        return
    msg = "📦 Stato attuale dei box:\n"
    for uid, data in user_data.items():
        netto = data["fiches_won"] - data["fiches_lost"]
        msg += f"\n👤 Utente {uid}:\n"
        msg += f"- Giocate: {data['turns']}\n"
        msg += f"- Vincite: {data['fiches_won']} – Perdite: {data['fiches_lost']} – Netto: {netto:+}\n"
        msg += f"- Chances attive: {', '.join(data['active_chances']) if data['active_chances'] else 'Nessuna'}\n"
    await update.message.reply_text(msg)

async def utenti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Accesso negato.")
        return
    await update.message.reply_text(f"👥 Utenti unici totali: {len(user_ids)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("statistiche", statistiche))
    app.add_handler(CommandHandler("utenti", utenti))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_input))
    app.run_polling()

if __name__ == "__main__":
    main()
