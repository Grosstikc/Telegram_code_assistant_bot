import os
import asyncio
import nest_asyncio
nest_asyncio.apply()

from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

async def main():
    # Load environment variables
    load_dotenv()

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found in .env file")

    # Initialize the database (creates tables and sets up the connection pool)
    await init_db()
    logger.info("Database initialized successfully.")

    # Build the Telegram bot application (using long polling)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register your handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    # Optional: delay a few seconds to allow any previous polling session to terminate
    await asyncio.sleep(3)

    # Run polling (this call blocks until the bot is stopped)
    await application.run_polling()

    # After polling stops, gracefully close the database connection pool
    pool = await get_db_pool()
    await pool.close()
    logger.info("Database connection pool closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # If the event loop is already running (common in some managed environments),
        # schedule main() on the current loop and run forever.
        if "already running" in str(e):
            loop = asyncio.get_running_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
