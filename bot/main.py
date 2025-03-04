import os
from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv
import asyncio

def main():
    load_dotenv()  # Load environment variables

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found in .env file")

    # Initialize the database using an event loop
    asyncio.run(init_db())
    logger.info("Database initialized successfully.")

    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    # Run polling in synchronous mode; run_polling() will manage its own event loop.
    try:
        application.run_polling()
    finally:
        # After polling stops, gracefully close the DB pool.
        # Use asyncio.run() to execute async code.
        asyncio.run(close_db_pool())

def close_db_pool():
    async def _close():
        pool = await get_db_pool()
        await pool.close()
        logger.info("Database connection pool closed.")
    return _close()

if __name__ == "__main__":
    main()
