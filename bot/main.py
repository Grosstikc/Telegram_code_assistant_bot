import os
import asyncio
import nest_asyncio
nest_asyncio.apply()  # Remove this if not needed in production

from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

# Define a shutdown callback for the DB pool
async def shutdown_db_pool(app):
    pool = await get_db_pool()
    await pool.close()  # Await close() if it's a coroutine
    logger.info("Database connection pool closed.")

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

    # Set up handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    await asyncio.sleep(3)  # Delay to allow any lingering polling session to end

    # Run polling and register the shutdown callback via the post_shutdown parameter
    await application.run_polling(post_shutdown=[shutdown_db_pool])

if __name__ == "__main__":
    asyncio.run(main())
