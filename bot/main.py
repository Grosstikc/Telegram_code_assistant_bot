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

    # Initialize the database (creates tables and sets up the connection pool)
    await init_db()

    # Build the Telegram bot application (using long polling)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    # Optional: short delay to allow previous polling sessions to clear
    await asyncio.sleep(3)

    # Instead of run_polling(), we initialize, start polling, and idle:
    await application.initialize()
    await application.start_polling()
    # Block here until shutdown is requested (this method returns when the bot stops)
    await application.updater.idle()

    # On shutdown, gracefully close the DB pool:
    pool = await get_db_pool()
    await pool.close()
    logger.info("Database connection pool closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Fallback: if an event loop is already running, schedule main() and run forever.
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
