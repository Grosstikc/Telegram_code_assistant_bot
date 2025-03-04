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
    
    # Run async database initialization in its own event loop
    asyncio.run(init_db())
    logger.info("Database initialized successfully.")
    
    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register your handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running...")
    
    # Now run polling synchronously.
    application.run_polling()  # This call creates and manages its own event loop.
    
    # After polling (when the bot shuts down), close the DB pool
    asyncio.run(close_db_pool())

if __name__ == "__main__":
    main()
