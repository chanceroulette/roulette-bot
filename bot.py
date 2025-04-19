# Entry point: bot.py
from telegram.ext import ApplicationBuilder
from handlers.commands import register_commands
from handlers.admin import register_admin_commands
from handlers.game_logic import register_game_logic
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Registra i gruppi di handler
    register_commands(app)
    register_admin_commands(app)
    register_game_logic(app)

    # Avvio del bot
    app.run_polling()


if __name__ == "__main__":
    main()
