import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from strategy import StrategyManager
from keyboards import main_menu_keyboard, number_keyboard

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stati
SET_BANKROLL, PRIMI15, INSERT_NUMBER = range(3)

# Carica token da variabile d’ambiente
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN non impostata")

# Il tuo ID Telegram (amministratore)
ADMIN_ID = 5033904813

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Reset sessione e mostra menu."""
    ctx.user_data.clear()
    await update.message.reply_text(
        "Benvenuto in Chance Roulette Bot! 📊\n"
        "Imposta il bankroll con /set_bankroll o usa il menu qui sotto.",
        reply_markup=main_menu_keyboard(False)
    )

async def set_bankroll(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Inserisci il tuo bankroll iniziale (numero intero):")
    return SET_BANKROLL

async def bankroll_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        return await update.message.reply_text("Per favore inserisci un numero intero valido.")
    ib = int(text)
    ctx.user_data["initial_bankroll"] = ib
    ctx.user_data["current_bankroll"] = ib
    await update.message.reply_text(
        f"Bankroll iniziale impostato a {ib} fiches.\n"
        "Ora usa /primi15 per inserire i primi 15 numeri.",
        reply_markup=main_menu_keyboard(False)
    )
    return ConversationHandler.END

async def primi15_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "initial_bankroll" not in ctx.user_data:
        return await update.message.reply_text("Devi prima impostare il bankroll con /set_bankroll")
    ctx.user_data["first15"] = []
    await update.message.reply_text(
        "Inserisci i primi 15 numeri iniziali UNO ALLA VOLTA:",
        reply_markup=number_keyboard()
    )
    return PRIMI15

async def primi15_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    num = update.message.text.strip()
    if not num.isdigit() or not (0 <= int(num) <= 36):
        return await update.message.reply_text("Numero non valido. Scegli tra 0 e 36.")
    lst = ctx.user_data["first15"]
    lst.append(int(num))
    if len(lst) < 15:
        return await update.message.reply_text(f"Registrato {num}. Ora {len(lst)}/15:", reply_markup=number_keyboard())
    # completati 15
    sm = StrategyManager(lst)
    ctx.user_data["strategy"] = sm
    consigliate = sm.suggested_chances()
    await update.message.reply_text(
        f"Tutti i 15 numeri registrati.\n"
        f"Chances consigliate: {', '.join(consigliate)}\n\n"
        "Ora avvia /modalita_inserimento per registrare le estrazioni.",
        reply_markup=main_menu_keyboard(False)
    )
    return ConversationHandler.END

async def modalita_inserimento(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "strategy" not in ctx.user_data:
        return await update.message.reply_text("Devi prima completare /primi15")
    await update.message.reply_text("Modalità inserimento attiva. Tocca un numero:", reply_markup=number_keyboard())
    return INSERT_NUMBER

async def numero_uscito(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    num = int(update.message.text)
    sm: StrategyManager = ctx.user_data["strategy"]
    outcome, bets = sm.play(num)
    ctx.user_data["current_bankroll"] += outcome

    text = [f"NUMERO USCITO: {num}"]
    for ch, (bet, res) in bets.items():
        sign = "+" if res >= 0 else ""
        text.append(f"{ch}: puntate {bet} → esito: {sign}{res}")
    text.append(f"\nSaldo corrente: {ctx.user_data['current_bankroll']} fiche")

    await update.message.reply_text("\n".join(text), reply_markup=number_keyboard())
    return INSERT_NUMBER

async def report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ib = ctx.user_data.get("initial_bankroll", 0)
    cb = ctx.user_data.get("current_bankroll", 0)
    sm: StrategyManager = ctx.user_data.get("strategy")
    plays, wins, losses = (0,0,0)
    if sm:
        plays = sm.total_plays()
        wins, losses = sm.wins_losses()
    await update.message.reply_text(
        f"🏁 REPORT SESSIONE 🏁\n"
        f"Bankroll iniziale: {ib}\n"
        f"Bankroll attuale: {cb}\n"
        f"Giocate totali: {plays}\n"
        f"Vinte: {wins} | Perse: {losses}",
        reply_markup=main_menu_keyboard(False)
    )

async def end_session(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await report(update, ctx)
    ctx.user_data.clear()
    await update.message.reply_text("Sessione terminata. /start per ricominciare.", reply_markup=main_menu_keyboard(False))

async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    is_admin = update.effective_user.id == ADMIN_ID
    await update.message.reply_text(
        f"⚙️ Pannello Admin ⚙️\nUtenti totali: {len(ctx.application.chat_data)}",
        reply_markup=main_menu_keyboard(is_admin)
    )

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("set_bankroll", set_bankroll),
            CommandHandler("primi15", primi15_start),
        ],
        states={
            SET_BANKROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bankroll_received)],
            PRIMI15: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi15_receive)],
            INSERT_NUMBER: [MessageHandler(filters.Regex(r"^[0-9]{1,2}$"), numero_uscito)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("modalita_inserimento", modalita_inserimento))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("end_session", end_session))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("id", lambda u,c: u.message.reply_text(f"Il tuo ID è {u.effective_user.id}")))

    app.run_polling()

if __name__ == "__main__":
    main()