import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 5033904813

CHANCES = ["Rosso", "Nero", "Pari", "Dispari", "Manque", "Passe"]
CHANCE_POOLS = {
    "Rosso": {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "Nero": set(range(1, 37)) - {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "Pari": {n for n in range(1, 37) if n % 2 == 0},
    "Dispari": {n for n in range(1, 37) if n % 2 == 1},
    "Manque": set(range(1, 19)),
    "Passe": set(range(19, 37)),
}

SET_BANKROLL, PRIMI15, SELEZIONA_CHANCES, INSERT_SPIN = range(4)
logging.basicConfig(level=logging.INFO)

class StrategyManager:
    def __init__(self, bankroll, first15):
        self.initial_bankroll = bankroll
        self.current_bankroll = bankroll
        self.first15 = first15.copy()
        self.history = []
        self.total_profit = 0
        self.active = []
        self.boxes = {}

    def suggerisci_chances(self):
        stats = {ch: 0 for ch in CHANCES}
        for n in self.first15:
            for ch, pool in CHANCE_POOLS.items():
                if n in pool:
                    stats[ch] += 1
        meno_frequenti = sorted(stats.items(), key=lambda x: x[1])[:3]
        return [ch for ch, _ in meno_frequenti]

    def inizializza_box(self, scelte):
        self.active = scelte
        for ch in scelte:
            self.boxes[ch] = [1, 1, 1, 1]

    def play(self, numero):
        self.history.append(numero)
        giro = {}
        profit = 0
        for ch in self.active:
            box = self.boxes.get(ch, [1, 1, 1, 1])
            bet = box[0] + (box[-1] if len(box) > 1 else 0)
            win = numero in CHANCE_POOLS[ch]
            risultato = bet if win else -bet
            profit += risultato
            giro[ch] = (bet, risultato)
            if win:
                box = box[1:-1] if len(box) > 1 else []
            else:
                box.append(bet)
            self.boxes[ch] = box if box else [1, 1, 1, 1]
        self.total_profit += profit
        self.current_bankroll += profit
        return profit, giro

def menu_keyboard(is_admin=False):
    base = [
        ["/set_bankroll", "/primi15"],
        ["/modalita_inserimento", "/report"],
        ["/storico", "/end_session"]
    ]
    if is_admin:
        base.append(["/admin"])
    return ReplyKeyboardMarkup(base, resize_keyboard=True)

def chances_keyboard(selected):
    buttons = []
    for i in range(0, len(CHANCES), 2):
        row = []
        for ch in CHANCES[i:i+2]:
            label = f"{'✅' if ch in selected else ''}{ch}"
            row.append(label)
        buttons.append(row)
    buttons.append(["Conferma"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def number_keyboard():
    keys = [str(i) for i in range(37)]
    rows = [keys[i:i+6] for i in range(0, len(keys), 6)]
    return ReplyKeyboardMarkup(rows + [["Termina"]], resize_keyboard=True)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Benvenuto in Chance Roulette!", reply_markup=menu_keyboard(update.effective_user.id == ADMIN_ID))

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot per la strategia con le chances alla roulette. Supporto: info@trilium-bg.com")

async def id_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo ID Telegram è: {update.effective_user.id}")

async def set_bankroll(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Inserisci il bankroll iniziale:")
    return SET_BANKROLL

async def bankroll_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit(): return await update.message.reply_text("Devi inserire un numero.")
    ctx.user_data["bankroll"] = int(txt)
    await update.message.reply_text("Bankroll impostato. Ora inserisci i 15 numeri con /primi15.")
    return ConversationHandler.END

async def primi15(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["first15"] = []
    await update.message.reply_text("Inserisci i 15 numeri uno alla volta.", reply_markup=number_keyboard())
    return PRIMI15

async def primi15_ricevuto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    num = update.message.text.strip()
    if not num.isdigit() or not 0 <= int(num) <= 36:
        return await update.message.reply_text("Numero non valido.")
    ctx.user_data["first15"].append(int(num))
    if len(ctx.user_data["first15"]) < 15:
        return await update.message.reply_text(f"{len(ctx.user_data['first15'])}/15 inseriti.")
    # analisi
    sm = StrategyManager(ctx.user_data["bankroll"], ctx.user_data["first15"])
    consigliate = sm.suggerisci_chances()
    ctx.user_data["strategy"] = sm
    ctx.user_data["selezionate"] = set(consigliate)
    await update.message.reply_text(
        f"Chances consigliate: {', '.join(consigliate)}\nSeleziona le tue chances:",
        reply_markup=chances_keyboard(ctx.user_data["selezionate"])
    )
    return SELEZIONA_CHANCES

async def selezione_chances(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scelta = update.message.text.replace("✅", "").strip()
    if scelta == "Conferma":
        selezionate = list(ctx.user_data["selezionate"])
        ctx.user_data["strategy"].inizializza_box(selezionate)
        await update.message.reply_text("Strategia avviata. Inserisci i numeri.", reply_markup=number_keyboard())
        return INSERT_SPIN
    if scelta not in CHANCES:
        return await update.message.reply_text("Selezione non valida.")
    selez = ctx.user_data["selezionate"]
    selez.remove(scelta) if scelta in selez else selez.add(scelta)
    return await update.message.reply_text("Chances aggiornate:", reply_markup=chances_keyboard(selez))

async def inserisci_spin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "Termina":
        return await end_session(update, ctx)
    if not txt.isdigit() or not 0 <= int(txt) <= 36:
        return await update.message.reply_text("Numero non valido.")
    numero = int(txt)
    sm = ctx.user_data["strategy"]
    profit, giro = sm.play(numero)
    output = [f"Numero uscito: {numero}"]
    for ch, (bet, res) in giro.items():
        output.append(f"{ch}: {bet} → {res:+}")
    output.append(f"Profitto giro: {profit:+}")
    output.append(f"Totale: {sm.total_profit:+} | Bankroll: {sm.current_bankroll}")
    await update.message.reply_text("\n".join(output), reply_markup=number_keyboard())
    return INSERT_SPIN

async def report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sm: StrategyManager = ctx.user_data.get("strategy")
    if not sm: return await update.message.reply_text("Nessuna sessione attiva.")
    await update.message.reply_text(
        f"Bankroll iniziale: {sm.initial_bankroll}\nAttuale: {sm.current_bankroll}\nProfitto: {sm.total_profit}"
    )

async def storico(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sm: StrategyManager = ctx.user_data.get("strategy")
    hist = sm.history if sm else []
    await update.message.reply_text(f"Numeri giocati: {hist}")

async def end_session(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await report(update, ctx)
    ctx.user_data.clear()
    await update.message.reply_text("Sessione terminata. /start per ricominciare.")
    return ConversationHandler.END

async def admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Accesso Admin OK.")
    else:
        await update.message.reply_text("Non autorizzato.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("set_bankroll", set_bankroll),
            CommandHandler("primi15", primi15)
        ],
        states={
            SET_BANKROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bankroll_received)],
            PRIMI15: [MessageHandler(filters.TEXT & ~filters.COMMAND, primi15_ricevuto)],
            SELEZIONA_CHANCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, selezione_chances)],
            INSERT_SPIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_spin)],
        },
        fallbacks=[],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("storico", storico))
    app.add_handler(CommandHandler("end_session", end_session))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(conv)

    app.run_polling()

if __name__ == "__main__":
    main()