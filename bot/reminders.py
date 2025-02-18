import logging
from datetime import datetime, time
import pytz

logger = logging.getLogger("CodeAssistantBot")


async def set_reminder(update, context):
    """Set a daily reminder in UTC."""
    try:
        # Parse the time input by the user in HH:MM format
        user_time = datetime.strptime(update.message.text.strip(), "%H:%M").time()

        # Convert the user's time to UTC
        user_timezone = pytz.timezone("Etc/UTC")  # Adjust if users specify a different time zone
        local_datetime = datetime.combine(datetime.now(), user_time)
        utc_datetime = local_datetime.astimezone(pytz.UTC)
        utc_time = utc_datetime.time()

        # Schedule the reminder in UTC
        context.job_queue.run_daily(
            daily_reminder,
            time=utc_time,
            chat_id=update.effective_chat.id,
            name=str(update.effective_chat.id),
        )
        await update.message.reply_text(f"Reminder set for {user_time.strftime('%H:%M')} UTC.")
    except ValueError:
        await update.message.reply_text("Invalid time format! Use HH:MM (24-hour format).")
    except Exception as e:
        logger.error(f"Error in set_reminder: {e}")
        await update.message.reply_text("An error occurred while setting the reminder.")


async def daily_reminder(context):
    """Send a daily reminder message."""
    try:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="Don't forget to code today! What project are you working on?",
        )
    except Exception as e:
        logger.error(f"Error in daily_reminder: {e}")


async def stop_reminder(update, context):
    """Stop a daily reminder."""
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))

    if not jobs:
        # Check if triggered by a callback query
        if update.callback_query:
            await update.callback_query.edit_message_text("No active reminders to stop.")
        else:
            await update.message.reply_text("No active reminders to stop.")
        return

    for job in jobs:
        job.schedule_removal()

    # Send feedback based on trigger type
    if update.callback_query:
        await update.callback_query.edit_message_text("Reminder stopped.")
    else:
        await update.message.reply_text("Reminder stopped.")
