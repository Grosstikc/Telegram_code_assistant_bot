import os
import asyncio
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

    # Initialize the database (this creates tables and sets up the connection pool)
    await init_db()

    # Build the Telegram bot application (using long polling)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers and the error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    # Optional: Delay a few seconds to allow any previous polling session to end
    await asyncio.sleep(3)

    # Run polling (this call blocks until the bot is stopped)
    await application.run_polling()

    # After polling stops, gracefully close the DB connection pool
    pool = await get_db_pool()
    await pool.close()
    logger.info("Database connection pool closed.")

def run_bot():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If an event loop is already running, schedule main() as a task.
            loop.create_task(main())
        else:
            asyncio.run(main())
    except Exception as e:
        logger.error("Error running bot", exc_info=e)

if __name__ == "__main__":
    run_bot()
