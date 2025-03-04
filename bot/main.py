import os
import asyncio
from telegram.ext import ApplicationBuilder
from bot.utils import logger
from bot.handlers import error_handler, setup_handlers
from bot.database import init_db
from bot.pomodoro import setup_pomodoro_handlers
from bot.weather import setup_weather_handlers
from dotenv import load_dotenv

async def main():
    load_dotenv()  # Load environment variables

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found in .env file")

    # Initialize the database (creates tables and sets up the connection pool)
    await init_db()
    logger.info("Database initialized successfully.")

    # Build the Telegram bot application (using long polling)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers and error handler
    setup_handlers(application)
    setup_pomodoro_handlers(application)
    setup_weather_handlers(application)
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    # Optional delay to help clear any lingering sessions
    await asyncio.sleep(3)

    try:
        await application.run_polling()
    except RuntimeError as e:
        # Catch and log shutdown errors related to the event loop closure
        if "Cannot close a running event loop" in str(e):
            logger.warning("Shutdown error: cannot close a running event loop; ignoring.")
        else:
            raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # If the event loop is already running, schedule main() on the current loop
        if "already running" in str(e):
            loop = asyncio.get_running_loop()
            loop.create_task(main())
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                pass
        else:
            raise
