import os
from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import setup_handlers
from bot.database import init_db
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

def main():
    """Main entry point for the bot."""
    load_dotenv()  # Load environment variables

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found in .env file")

    # Initialize the database
    init_db()

    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Set up all handlers
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)

    # Run the bot
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
