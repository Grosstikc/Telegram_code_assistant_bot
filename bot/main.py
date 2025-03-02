import os
import asyncio
import nest_asyncio
nest_asyncio.apply()  # Optional: Remove in production if not needed

from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db, get_db_pool
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

# Post-shutdown callback to close the DB pool gracefully
async def shutdown_db_pool(app):
    pool = await get_db_pool()
    await pool.close()  # Await the close() coroutine if needed
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

    # Register handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)
    application.post_shutdown.append(shutdown_db_pool)

    logger.info("Bot is running...")
    await asyncio.sleep(3)  # Short delay to allow any lingering sessions to end

    # Run polling (this call blocks until shutdown)
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
