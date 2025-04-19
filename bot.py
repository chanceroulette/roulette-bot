import os
import logging
from copy import deepcopy
from collections import Counter
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# ——— Config ———
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN non trovata in env")

ADMIN_ID = 5033904813
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ——— Conversation States ———
SET_BANKROLL, PRIMI15, INSERT_SPIN = range(3)

# ——— StrategyManager ———
CHANCE_POOLS = {
    "Rosso": {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "Nero": set(range(0,37)) - {0} - {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "Pari": {n for n in range(1,37) if n%2==0},
    "Dispari": {n for n in range(1,37) if n%2==1},
    "Manque": set(range(1,19)),
    "Passe": set(range(19,37)),
}

class StrategyManager:
    def __init__(self, bankroll: int, first15: list[int]):
        self.initial_bankroll = bankroll
        self.current_bankroll = bankroll
        self.first15 = first15.copy()
        self.boxes = {ch: [1] for ch in CHANCE_POOLS}
        self.active = []
        self.total_profit = 0
        self._plays = 0
        self._wins = 0
        self._losses = 0

    def suggested_chances(self) -> list[str]:
        stats = {ch:0 for ch in CHANCE_POOLS}
        for n in self.first15:
            for ch,pool in CHANCE_POOLS.items():
                if n in pool:
                    stats[ch] += 1
        # prendo 3 chance meno frequenti (più “perdenti”)
        sorted_ch = sorted(stats.items(), key=lambda x: x[1])
        self.active = [ch for ch,_ in sorted_ch[:3]]
        return self.active

    def play(self, number: int) -> tuple[int, dict]:
        bets = {}
        outcomes = {}
        profit = 0
        for ch in self.active:
            pool = CHANCE_POOLS[ch]
            box = self.boxes[ch]
            bet = box[0] + (box[-1] if len(box)>1 else 0)
            win = number in pool
            res = bet if win else -bet
            bets[ch] = bet
            outcomes[ch] = res
            profit += res
            self.total_profit += res
            if win:
                self._wins += 1
                if len(box)>1:
                    new_box = box[1:-1]
                    self.boxes[ch] = new_box if new_box else [1]
                else:
                    self.boxes[ch] = [1]
            else:
                self._losses += 1
                box.append(bet)
                self.boxes[ch] = box
        self._plays += 1
        self.current_bankroll += profit
        return profit, bets, outcomes

    def total_plays(self): return self._plays
    def wins_losses(self): return self._wins, self._losses

# ——— Keyboards ———
def main_menu(is_admin=False):
    buttons = [
        ["/set_bankroll", "/primi15", "/modalita_inserimento"],
        ["/report", "/storico", "/annulla_ultima"],
        ["/help", "/id", "/end_session"]
    ]
    if is_admin:
        buttons.append(["/admin"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def number_kb():
    nums = [str(i) for i in range(0,37)]
    kb = [nums[i:i+6] for i in range(0,37,6)]
    kb.append(["Annulla", "Menu", "Termina sessione"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)

# ——— Handlers ———

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n"
        "Imposta bankroll: /set_bankroll\n"
        "oppure usa il menu.",
        reply_markup=main_menu(update.effective_user.id==ADMIN_ID)
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandi:\n"
        "/set_bankroll – imposta capitale iniziale\n"
        "/primi15 – inserisci 15 uscite iniziali\n"
        "/modalita_inserimento – inizia spin\n"
        "/report – report parziale\n"
        "/storico – lista numeri usciti\n"
        "/annulla_ultima – togli ultimo numero\n"
        "/end_session – termina e resetta\n"
        "/id – mostra ID\n"
        "/admin – pannello admin",
        reply_markup=main_menu(update.effective_user.id==ADMIN_ID)
    )

async def id_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def set_bankroll(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Inserisci bankroll iniziale (intero):", reply_markup=main_menu(update.effective_user.id==ADMIN_ID))
    return SET_BANKROLL

async def bankroll_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        return await update.message.reply_text("Numero non valido, riprova:")
    ib = int(txt)
    ctx.user_data["initial_bankroll"] = ib
    ctx.user_data["current_bankroll"] = ib
    await update.message.reply_text(f"Bankroll: {ib} fiches. Ora /primi15", reply_markup=main_menu(update.effective_user.id==ADMIN_ID))
    return ConversationHandler.END

async def primi15_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "initial_bankroll" not in ctx.user_data:
        return await update.message.reply_text("Prima /set_bankroll")
    ctx.user_data["first15"] = []
    await update.message.reply_text("Inserisci 15 numeri UNO ALLA VOLTA:", reply_markup=number_kb())
    return PRIMI15

async def primi15_receive(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    num = update.message.text.strip()
    if not num.isdigit() or not (0<=int(num)<=36):
        return await update.message.reply_text("Solo numeri 0–36.")
    lst = ctx.user_data["first15"]
    lst.append(int(num))
    if len(lst) < 15:
        return await update.message.reply_text(f"{len(lst)}/15 registrato.", reply_markup=number_kb())
    # finiti 15
    sm = StrategyManager(ctx.user_data["initial_bankroll"], lst)
    ctx.user_data["strategy"] = sm
    cons = sm.suggested_chances()
    await update.message.reply_text(
        f"15 numeri: {lst}\nChances: {cons}\nOra /modalita_inserimento",
        reply_markup=main_menu(update.effective_user.id==ADMIN_ID)
    )
    return ConversationHandler.END

async def modalita_inserimento(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "strategy" not in ctx.user_data:
        return await update.message.reply_text("Prima /primi15")
    await update.message.reply_text("Inserisci spin (0–36):", reply_markup=number_kb())
    return INSERT_SPIN

async def spin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    num = int(update.message.text)
    sm: StrategyManager = ctx.user_data["strategy"]
    profit, bets, outcomes = sm.play(num)
    ctx.user_data["current_bankroll"] += profit
    lines = [f"📊 Numero uscito: {num}\n"]
    for ch in sm.active:
        b = bets[ch]; o = outcomes[ch]
        sym = "✅" if o>0 else "❌"
        lines.append(f"{sym} {ch}: puntate {b} → {o:+}")
    lines.append(f"\n💰 Giro: {profit:+}   Totale: {sm.total_profit:+}")
    lines.append("\n🔲 Stato box:")
    for ch in sm.active:
        lines.append(f"  – {ch}: {sm.boxes[ch]}")
    lines.append(f"\n🎯 Bankroll: {ctx.user_data['current_bankroll']} fiche")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=number_kb())
    return INSERT_SPIN

async def report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ib = ctx.user_data.get("initial_bankroll",0)
    cb = ctx.user_data.get("current_bankroll",0)
    sm: StrategyManager = ctx.user_data.get("strategy")
    plays,wins,losses = (0,0,0)
    if sm:
        plays = sm.total_plays(); wins,losses=sm.wins_losses()
    txt = (f"🏁 REPORT\nBankroll init: {ib}\nBankroll now: {cb}\n"
           f"Giocate: {plays}\nVinte: {wins} | Perse: {losses}")
    await update.message.reply_text(txt, reply_markup=main_menu(update.effective_user.id==ADMIN_ID))

async def storico(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sm: StrategyManager = ctx.user_data.get("strategy")
    hist = sm.first15 if sm and len(sm.first15)<=15 else []
    hist = hist + (ctx.user_data.get("strategy").history and [h[0] for h in ctx.user_data["strategy"].history])
    await update.message.reply_text(f"Uscite: {hist}", reply_markup=main_menu(update.effective_user.id==ADMIN_ID))

async def annulla_ultima(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sm: StrategyManager = ctx.user_data.get("strategy")
    if sm and sm.history:
        sm.history.pop()
        await update.message.reply_text("Ultima estrazione annullata.", reply_markup=main_menu(update.effective_user.id==ADMIN_ID))
    else:
        await update.message.reply_text("Niente da annullare.", reply_markup=main_menu(update.effective_user.id==ADMIN_ID))

async def end_session(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await report(update, ctx)
    ctx.user_data.clear()
    await update.message.reply_text("Sessione terminata. /start per ricominciare.", reply_markup=main_menu(False))

async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id==ADMIN_ID:
        await update.message.reply_text(f"⚙️ Admin attivo.", reply_markup=main_menu(True))
    else:
        await update.message.reply_text("Non autorizzato.", reply_markup=main_menu(False))

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("set_bankroll", set_bankroll), CommandHandler("primi15", primi15_start)],
        states={
            SET_BANKROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bankroll_received)],
            PRIMI15: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi15_receive)],
            INSERT_SPIN: [MessageHandler(filters.Regex(r"^[0-9]{1,2}$"), spin)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("modalita_inserimento", modalita_inserimento))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("annulla_ultima", annulla_ultima))
    app.add_handler(CommandHandler("end_session", end_session))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", id_cmd))

    app.run_polling()

if __name__ == "__main__":
    main()