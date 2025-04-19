import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 5033904813

SET_BANKROLL, INSERISCI_NUMERI, SELEZIONA_CHANCES = range(3)

user_data = {}
CHANCES = {
    'rosso': [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
    'nero': [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
    'pari': [x for x in range(1, 37) if x % 2 == 0],
    'dispari': [x for x in range(1, 37) if x % 2 != 0],
    'manque': list(range(1, 19)),
    'passe': list(range(19, 37))
}

number_keyboard = ReplyKeyboardMarkup(
    [[str(n) for n in range(i, i+6)] for i in range(0, 36, 6)] + [["36"], ["Annulla"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        'bankroll': 0,
        'numeri': [],
        'attive': [],
        'suggerite': [],
        'box': {chance: [1, 1, 1, 1] for chance in CHANCES.keys()},
        'saldo': 0,
        'storico': []
    }
    await update.message.reply_text(
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Inserisci ora il tuo bankroll iniziale (numero di fiches disponibili).\n\n"
        "Nota: non si tratta del valore nominale in euro o valuta, ma del numero effettivo di fiches con cui inizi la sessione."
    )
    return SET_BANKROLL

async def set_bankroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        bankroll = int(update.message.text)
        user_data[user_id]['bankroll'] = bankroll
        await update.message.reply_text(
            f"Bankroll impostato a {bankroll} fiches.\n\n"
            "Ora inserisci da 15 a 20 numeri estratti (dal più recente al più vecchio), uno alla volta.",
            reply_markup=number_keyboard
        )
        return INSERISCI_NUMERI
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido.")
        return SET_BANKROLL

async def inserisci_numeri(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if text.lower() == "annulla":
        await update.message.reply_text("Inserimento annullato.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    try:
        numero = int(text)
        if 0 <= numero <= 36:
            user_data[user_id]['numeri'].append(numero)
            count = len(user_data[user_id]['numeri'])
            await update.message.reply_text(f"Registrato {numero} ({count}/20)", reply_markup=number_keyboard)
            if 15 <= count <= 20:
                await update.message.reply_text("Hai inserito almeno 15 numeri. Quando sei pronto, digita /start_analisi.")
            if count >= 20:
                await update.message.reply_text("Hai inserito il massimo di 20 numeri. Ora usa /start_analisi.")
            return INSERISCI_NUMERI
        else:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido tra 0 e 36.")
        return INSERISCI_NUMERI

async def start_analisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numeri = user_data[user_id]['numeri']
    if len(numeri) < 15:
        await update.message.reply_text("Devi inserire almeno 15 numeri.")
        return
    frequenze = {
        chance: sum(1 for n in numeri if n in CHANCES[chance]) for chance in CHANCES
    }
    max_freq = max(frequenze.values())
    suggerite = [c for c, v in frequenze.items() if v == max_freq]
    user_data[user_id]['suggerite'] = suggerite
    user_data[user_id]['attive'] = []

    buttons = [[InlineKeyboardButton(text=chance, callback_data=chance)] for chance in CHANCES.keys()] + [
        [InlineKeyboardButton("✅ Conferma", callback_data="conferma")]
    ]

    await update.message.reply_text(
        f"Chances consigliate: {', '.join(suggerite)}\nSeleziona ora quali vuoi attivare:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELEZIONA_CHANCES

async def seleziona_chances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "conferma":
        scelte = user_data[user_id]['attive']
        await query.edit_message_text(f"Chances attivate: {', '.join(scelte)}\nOra usa /gioca <numero> per iniziare la sessione di gioco.")
        return ConversationHandler.END

    if data in CHANCES:
        if data in user_data[user_id]['attive']:
            user_data[user_id]['attive'].remove(data)
        else:
            user_data[user_id]['attive'].append(data)

        buttons = [[InlineKeyboardButton(text=chance, callback_data=chance)] for chance in CHANCES.keys()] + [
            [InlineKeyboardButton("✅ Conferma", callback_data="conferma")]
        ]

        await query.edit_message_text(
            f"Chances consigliate: {', '.join(user_data[user_id]['suggerite'])}\nChances selezionate: {', '.join(user_data[user_id]['attive'])}\nSeleziona o conferma:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    return SELEZIONA_CHANCES

async def gioca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]['attive']:
        await update.message.reply_text("Devi prima avviare una sessione con /start e selezionare le chances.")
        return

    try:
        numero = int(context.args[0])
        if not 0 <= numero <= 36:
            raise ValueError
    except:
        await update.message.reply_text("Usa il comando così: /gioca 17")
        return

    risultato = f"🎯 Numero estratto: {numero}\n"
    saldo = 0

    for chance in user_data[user_id]['attive']:
        box = user_data[user_id]['box'][chance]
        if not box:
            box = [1, 1, 1, 1]
        puntata = box[0] if len(box) == 1 else box[0] + box[-1]
        user_data[user_id]['bankroll'] -= puntata

        if numero in CHANCES[chance]:
            risultato += f"✅ {chance.upper()}: +{puntata}\n"
            saldo += puntata
            if len(box) > 1:
                box = box[1:-1]
            else:
                box = []
        else:
            risultato += f"❌ {chance.upper()}: -{puntata}\n"
            box.append(puntata)

        if not box:
            box = [1, 1, 1, 1]
        user_data[user_id]['box'][chance] = box

    user_data[user_id]['saldo'] += saldo
    user_data[user_id]['bankroll'] += saldo
    user_data[user_id]['storico'].append(numero)

    risultato += f"\n💰 Bankroll attuale: {user_data[user_id]['bankroll']}\n📈 Saldo totale: {user_data[user_id]['saldo']}"
    await update.message.reply_text(risultato)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia\n\n"
        "Comandi utili:\n/start - inizializza sessione\n/start_analisi - dopo aver inserito i numeri\n/gioca <numero> - gioca un nuovo numero\n/help - mostra questo messaggio"
    )

async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo Telegram ID è: {update.effective_user.id}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Accesso amministratore riconosciuto.")
    else:
        await update.message.reply_text("Non sei autorizzato.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SET_BANKROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_bankroll)],
            INSERISCI_NUMERI: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_numeri)],
            SELEZIONA_CHANCES: [CallbackQueryHandler(seleziona_chances)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start_analisi", start_analisi))
    app.add_handler(CommandHandler("gioca", gioca))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("admin", admin))

    app.run_polling()
