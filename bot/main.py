import os
import asyncio
from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

async def async_main():
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
    # Optional: a short delay to let previous sessions clear
    await asyncio.sleep(3)
    
    # Start polling (this call blocks until the bot is stopped)
    await application.run_polling()
    
    # After polling stops, gracefully close the DB pool
    pool = await get_db_pool()
    await pool.close()
    logger.info("Database connection pool closed.")

def main():
    # Create a new event loop and set it as the current loop in the main thread.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_main())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
