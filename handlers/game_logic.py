from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from keyboards import build_keyboard, build_chance_keyboard
from utils import suggest_chances, init_box, format_box, get_win
from state import user_data, user_ids


def register_game_logic(app):
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_input))


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_ids.add(user_id)
    text = update.message.text.strip()

    if user_id not in user_data:
        await update.message.reply_text("Usa /start per iniziare.")
        return

    state = user_data[user_id]

    # Scelta manuale delle chances dopo l'analisi
    if state["pending_selection"] and text in ["Manque", "Pari", "Rosso", "Nero", "Dispari", "Passe"]:
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
        if len(state["input_sequence"]) < 10:
            await update.message.reply_text("⚠️ Inserisci almeno 10 numeri prima di analizzare.")
            return
        suggested = suggest_chances(state["input_sequence"])
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
            await update.message.reply_text("⚠️ Non hai ancora iniziato a giocare.")
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
            if box: box.pop(-1)
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
