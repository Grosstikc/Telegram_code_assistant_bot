import os
import asyncio
from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

def close_db_pool():
    async def _close():
        pool = await get_db_pool()
        await pool.close()
        logger.info("Database connection pool closed.")
    return _close()

def main():
    # Load environment variables
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found in .env file")
    
    # Create and set a new event loop in the main thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize the database (create tables and set up connection pool)
    loop.run_until_complete(init_db())
    logger.info("Database initialized successfully.")
    
    # Build the Telegram bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Delete any existing webhook (to avoid conflicts with polling)
    loop.run_until_complete(application.bot.delete_webhook())
    logger.info("Existing webhook deleted.")
    
    # Register your handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running...")
    
    try:
        # Run polling; run_polling() will manage its own event loop internally.
        application.run_polling()
    finally:
        # When polling stops, gracefully close the DB pool
        loop.run_until_complete(close_db_pool())
        logger.info("Database connection pool closed.")

if __name__ == "__main__":
    main()
