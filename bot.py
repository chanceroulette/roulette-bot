import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 5033904813

# Stati della conversazione
SET_BANKROLL, INSERISCI_PRIMI_15, SELEZIONA_CHANCES, INSERISCI_NUMERI = range(4)

# Dizionari per gestire gli utenti
user_data = {}

# CHANCES
CHANCES = {
    'rosso': [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
    'nero': [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
    'pari': [x for x in range(1, 37) if x % 2 == 0],
    'dispari': [x for x in range(1, 37) if x % 2 != 0],
    'manque': list(range(1, 19)),
    'passe': list(range(19, 37))
}

# Tastiera numerica da 0 a 36
number_keyboard = ReplyKeyboardMarkup(
    [[str(n) for n in range(i, i+6)] for i in range(0, 37, 6)] + [["Annulla"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data[user_id] = {
        'bankroll': 0,
        'numeri': [],
        'attive': [],
        'storico': [],
        'box': {chance: [1, 1, 1, 1] for chance in CHANCES.keys()},
        'saldo': 0
    }
    await update.message.reply_text(
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Inserisci ora il tuo bankroll iniziale (numero di fiches disponibili).\n\n"
        "Nota: non si tratta del valore nominale in euro o valuta, ma del numero effettivo di fiches con cui inizi la sessione."
    )
    return SET_BANKROLL

async def set_bankroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    try:
        bankroll = int(update.message.text)
        user_data[user_id]['bankroll'] = bankroll
        await update.message.reply_text(
            f"Bankroll iniziale impostato a {bankroll} fiches.\nOra usa /primi15 per inserire i primi 15 numeri."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Per favore inserisci un numero valido di fiches.")
        return SET_BANKROLL

async def primi15(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data[user_id]['numeri'] = []
    await update.message.reply_text("Inserisci i primi 15 numeri iniziali UNO ALLA VOLTA:", reply_markup=number_keyboard)
    return INSERISCI_PRIMI_15

async def ricevi_primi15(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    try:
        numero = int(update.message.text)
        if numero < 0 or numero > 36:
            raise ValueError
        user_data[user_id]['numeri'].append(numero)
        if len(user_data[user_id]['numeri']) == 15:
            numeri = user_data[user_id]['numeri']
            frequenze = {
                chance: sum(1 for n in numeri if n in CHANCES[chance]) for chance in CHANCES
            }
            consigliate = [k for k, v in frequenze.items() if v == max(frequenze.values())]
            user_data[user_id]['attive'] = consigliate
            await update.message.reply_text(
                f"Statistiche completate. Chances consigliate: {', '.join(consigliate)}\n"
                "Ora usa /modalita_inserimento",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"Registrato {numero}. Ora {len(user_data[user_id]['numeri'])}/15:",
                reply_markup=number_keyboard
            )
            return INSERISCI_PRIMI_15
    except ValueError:
        await update.message.reply_text("Inserisci un numero tra 0 e 36.", reply_markup=number_keyboard)
        return INSERISCI_PRIMI_15

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia\n\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Puoi usare i seguenti comandi per iniziare: /menu /primi15 /modalita_inserimento"
    )

# Avvio
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={SET_BANKROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_bankroll)]},
        fallbacks=[]
    )
    primi15_conv = ConversationHandler(
        entry_points=[CommandHandler("primi15", primi15)],
        states={INSERISCI_PRIMI_15: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_primi15)]},
        fallbacks=[]
    )

    app.add_handler(conv)
    app.add_handler(primi15_conv)
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()
