import os
import pytz
from datetime import datetime, time
from dotenv import load_dotenv
import requests
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import logger

load_dotenv()
API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_URL = os.getenv('WEATHER_URL')

async def get_weather(location):
    """Fetch weather data from the API."""
    try:
        params = {"q": location, "appid": API_KEY, "units": "metric"}
        response = requests.get(WEATHER_URL, params=params)
        data = response.json()

        if data["cod"] != 200:
            return f"Error: {data['message']}"
        
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]

        return f"Weather in {location}:\n🌡 Temperature: {temp}°C (Feels like {feels_like}°C)\n🌤 Condition: {weather}"
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return "Unable to fetch weather data. Please try again."

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /weather command."""
    if not context.args:
        await update.message.reply_text("Usage: /weather [location]")
        return
    
    location = " ".join(context.args)
    weather_info = await get_weather(location)
    await update.message.reply_text(weather_info)

async def set_weather_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set daily weather updates for a user."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        user_input = context.args
        location = user_input[0]
        time_str = user_input[1]  # Expected in HH:MM format

        # Convert user-specified time to UTC
        user_time = datetime.strptime(time_str, "%H:%M").time()
        utc_time = datetime.combine(datetime.now(), user_time).astimezone(pytz.UTC).time()

        context.job_queue.run_daily(
            callback=send_daily_weather,
            time=utc_time,
            chat_id=chat_id,
            name=f"weather_update_{user_id}",
            data={"location": location, "chat_id": chat_id},
        )

        logger.info(f"Weather update scheduled: location={location}, time={utc_time}, chat_id={chat_id}")
        await update.message.reply_text(f"Weather updates set for {location} daily at {time_str} (UTC).")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_weather_updates [location] [HH:MM] UTC")

async def send_daily_weather(context: ContextTypes.DEFAULT_TYPE):
    try:
        job_data = context.job.data
        location = job_data["location"]
        chat_id = job_data["chat_id"]

        logger.info(f"Executing weather update for chat_id={chat_id} and location={location}.")
        weather_info = await get_weather(location)

        logger.info(f"Weather info retrieved: {weather_info}")
        await context.bot.send_message(chat_id=chat_id, text=weather_info)
    except Exception as e:
        logger.error(f"Error in send_daily_weather: {e}")

def setup_weather_handlers(application):
    from telegram.ext import CommandHandler

    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("set_weather_updates", set_weather_updates))
