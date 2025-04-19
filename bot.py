from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import os

# Stati della conversazione
SET_BANKROLL, = range(1)

# Messaggio iniziale
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Benvenuto in Chance Roulette!\n\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Inserisci ora il tuo bankroll iniziale (numero di fiches disponibili).\n"
        "\nNota: non si tratta del valore nominale in euro o valuta, ma del numero effettivo di fiches con cui inizi la sessione."
    )
    return SET_BANKROLL

# Ricezione del bankroll
async def set_bankroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        bankroll = int(update.message.text)
        context.user_data['bankroll'] = bankroll
        await update.message.reply_text(
            f"Bankroll iniziale impostato a {bankroll} fiches.\n"
            "Ora usa /primi15 per inserire i primi 15 numeri."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Per favore inserisci un numero valido di fiches.")
        return SET_BANKROLL

# Comando /help con le informazioni complete
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Per supporto: info@trilium-bg.com\n"
        "Copyright © 2025 Fabio Felice Cudia\n\n"
        "Questo bot ti aiuta a tracciare la tua strategia alla roulette europea.\n"
        "Puoi usare i seguenti comandi per iniziare: /menu /primi15 /modalita_inserimento e altri."
    )

# Avvio applicazione
if __name__ == '__main__':
    from telegram.ext import Defaults
    from dotenv import load_dotenv

    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    application = ApplicationBuilder().token(TOKEN).defaults(Defaults()).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SET_BANKROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_bankroll)]
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()
