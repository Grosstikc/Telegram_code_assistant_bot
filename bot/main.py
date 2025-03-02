import os
import asyncio
# Remove nest_asyncio for production if possible:
# import nest_asyncio
# nest_asyncio.apply()

from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

async def main():
    """Main entry point for the bot."""
    load_dotenv()  # Load environment variables

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found in .env file")

    # Initialize the database (creates tables and sets up the connection pool)
    await init_db()

    # Build the Telegram bot application (using long polling)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register your handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    # Optional: delay startup to help clear any lingering polling sessions
    await asyncio.sleep(3)

    # Start polling; note we do not pass a post_shutdown parameter.
    await application.run_polling()

    # After run_polling() exits, gracefully close the DB pool
    pool = await get_db_pool()
    await pool.close()  # Ensure close() is awaited if it is a coroutine
    logger.info("Database connection pool closed.")

if __name__ == "__main__":
    # Instead of asyncio.run(), use the loop directly to avoid issues with loop closure.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
