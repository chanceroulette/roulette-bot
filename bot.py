import os, logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, MessageHandler, filters
)
from strategy import StrategyManager
from keyboards import main_menu_keyboard, roulette_keyboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN").strip()
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x}

strat = StrategyManager()

async def start(u, c):
    text = (
        "Benvenuto in Chance Roulette!\n"
        "Scrivi /menu per iniziare.\n\n"
        "Per supporto: info@trilium-bg.com\n"
        "©2025 Fabio Felice Cudia"
    )
    await u.message.reply_text(text, reply_markup=main_menu_keyboard())

async def menu(u, c):
    await u.message.reply_text("Menu comandi:", reply_markup=main_menu_keyboard())

async def primi15(u, c):
    uid = u.effective_user.id
    strat.reset_session(uid)
    await u.message.reply_text(
        "Inserisci i primi 15 numeri:", reply_markup=roulette_keyboard()
    )

async def modalita_inserimento(u, c):
    uid = u.effective_user.id
    if not strat.has_initial(uid):
        return await u.message.reply_text("Fai prima /primi15", reply_markup=main_menu_keyboard())
    strat.start_session(uid)
    await u.message.reply_text(
        "Modalità inserimento attiva. Tocca i numeri:",
        reply_markup=roulette_keyboard()
    )

async def collect(u, c):
    uid = u.effective_user.id
    txt = u.message.text
    if not txt.isdigit(): return
    n = int(txt)
    if not strat.in_session(uid):
        cnt = strat.add_initial_number(uid, n)
        if cnt < 15:
            await u.message.reply_text(f"Registrato {n}. Ora {cnt}/15.", reply_markup=roulette_keyboard())
        else:
            cons = strat.analyze_initial(uid)
            await u.message.reply_text(
                "Statistiche pronte. Chances consigliate: " + ", ".join(cons) +
                "\nUsa /modalita_inserimento", reply_markup=main_menu_keyboard()
            )
    else:
        rpt = strat.process_number(uid, n)
        await u.message.reply_text(rpt, reply_markup=roulette_keyboard())

async def report(u, c):
    uid = u.effective_user.id
    await u.message.reply_text(strat.build_session_report(uid), reply_markup=main_menu_keyboard())

async def annulla(u, c):
    uid = u.effective_user.id
    await u.message.reply_text(strat.undo_last(uid), reply_markup=roulette_keyboard())

async def storico(u, c):
    uid = u.effective_user.id
    h = strat.history[uid]
    await u.message.reply_text("Numeri usciti: " + ", ".join(map(str,h)), reply_markup=main_menu_keyboard())

async def id_cmd(u, c):
    await u.message.reply_text(f"Il tuo ID Telegram è: {u.effective_user.id}", reply_markup=main_menu_keyboard())

async def help_cmd(u, c):
    text = "/start /menu /primi15 /modalita_inserimento\n/storico /annulla_ultima /report /help /id /admin"
    await u.message.reply_text(text, reply_markup=main_menu_keyboard())

async def admin(u, c):
    uid = u.effective_user.id
    if uid not in ADMIN_IDS: return
    await u.message.reply_text("🔒 Pannello admin", reply_markup=main_menu_keyboard())

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot.delete_webhook(drop_pending_updates=True)

    # comandi
    for cmd, fn in [
        ("start", start), ("menu", menu),
        ("primi15", primi15), ("modalita_inserimento", modalita_inserimento),
        ("report", report), ("annulla_ultima", annulla),
        ("storico", storico), ("id", id_cmd),
        ("help", help_cmd), ("admin", admin),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    # un solo handler per tutti i numeri
    app.add_handler(MessageHandler(filters.Regex(r'^\d+$'), collect))

    app.run_polling()

if __name__ == "__main__":
    main()
