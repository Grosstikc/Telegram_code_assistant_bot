from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import logger
import datetime

DEFAULT_WORK_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
active_pomodoros = {}

async def start_pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new Pomodoro session."""
    user_id = update.effective_user.id 
    if user_id in active_pomodoros:
        await update.message.reply_text("You already have a pomodoro session! Use /stop_pomodoro to cancel it.")
        logger.info(f"User {user_id} attempted to start a new Pomodoro while one was already active.")
        return
    
    work_duration = DEFAULT_WORK_MINUTES * 60 
    break_duration = DEFAULT_BREAK_MINUTES * 60
    
    # Schedule work session
    utc_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=work_duration)
    work_job = context.job_queue.run_once(
        pomodoro_work_end,
        when=utc_time,
        chat_id=update.effective_chat.id,
        name=f"pomodoro_work_{user_id}",
        data={"user_id": user_id, "break_duration": break_duration}, 
    )
    active_pomodoros[user_id] = [work_job]
    logger.info(f"Pomodoro started for user {user_id}: Work duration {DEFAULT_WORK_MINUTES} minutes.")
    await update.message.reply_text(f"Pomodoro started! Focus for {DEFAULT_WORK_MINUTES} minutes.")
    
async def stop_pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the current Pomodoro session."""
    user_id = update.effective_user.id
    if user_id not in active_pomodoros:
        await update.message.reply_text("You don't have any active Pomodoro sessins to stop.")
        logger.info(f"User {user_id} tried to stop a Pomodoro session, but none were active.")
        return
    
    for job in active_pomodoros[user_id]:
        job.schedule_removal()
    del active_pomodoros[user_id]
    logger.info(f"Pomodoro session stopped for user {user_id}.")
    await update.message.reply_text("Pomodoro session stopped.")

async def pomodoro_work_end(context: ContextTypes.DEFAULT_TYPE):
    """Handle end of work session."""
    data = context.job.data
    user_id = data["user_id"]
    break_duration = data["break_duration"]
    chat_id = context.job.chat_id

    logger.info(f"Work session ended for user {user_id}. Scheduling break.")
    await context.bot.send_message(chat_id=chat_id, text=f"Work session complete! Time for a {DEFAULT_BREAK_MINUTES}-minute break.")
    
    # Schedule break session
    utc_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=break_duration)
    break_job = context.job_queue.run_once(
        pomodoro_break_end,
        when=utc_time,
        chat_id=chat_id,
        name=f"Pomodoro break_{user_id}",
        data={"user_id": user_id},
    )
    active_pomodoros[user_id].append(break_job)

async def pomodoro_break_end(context: ContextTypes.DEFAULT_TYPE):
    """Handle end of break session."""
    data = context.job.data
    user_id = data["user_id"]
    chat_id = context.job.chat_id
    
    logger.info(f"Break session ended for user {user_id}. Pomodoro complete.")
    await context.bot.send_message(chat_id=chat_id, text="Break time over! Pomodoro session complete.")
    if user_id in active_pomodoros:
        del active_pomodoros[user_id]

def setup_pomodoro_handlers(application):
    """Add pomodoro handlres to the application."""
    from telegram.ext import CommandHandler
    application.add_handler(CommandHandler("start_pomodoro", start_pomodoro))
    application.add_handler(CommandHandler("stop_pomodoro", stop_pomodoro))
