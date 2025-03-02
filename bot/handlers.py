import datetime
import pytz
from datetime import datetime, time
from telegram.error import Conflict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from bot.database import (
    add_task_to_db,
    get_user_id,
    delete_task as db_delete_task,
    get_or_create_user,
    add_project_to_db,
    delete_project_from_db,
    get_projects_from_db,
    get_tasks_from_db,
    update_task as db_update_task,
    delete_task  # async version
)
from bot.reminders import daily_reminder, set_reminder, stop_reminder
from bot.utils import logger
from bot.quotes import get_random_quote
from bot.weather import get_weather, send_daily_weather

async def error_handler(update: object, context: CallbackContext) -> None:
    # Check if the error is a Conflict error
    if isinstance(context.error, Conflict):
        logger.warning("Conflict error (getUpdates): ignoring.", exc_info=context.error)
        return
    # Log other errors
    logger.error("Unhandled exception:", exc_info=context.error)
    
# ---------- USER INITIALIZATION ----------
async def initialize_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ensure the user is registered in the database."""
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    await get_or_create_user(telegram_id, username, first_name, last_name)    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and initialize user."""
    await initialize_user(update, context)
    await send_menu(update, context)

# ---------- MENU FUNCTIONS WITH ENHANCED VISUALS ----------
async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the top-level main menu.
    This function sends a new message.
    """
    keyboard = [
        [InlineKeyboardButton("📁 *Projects*", callback_data="menu_projects"),
         InlineKeyboardButton("📝 *Tasks*", callback_data="menu_tasks")],
        [InlineKeyboardButton("⏰ *Reminders*", callback_data="menu_reminders"),
         InlineKeyboardButton("🌦 *Weather*", callback_data="menu_weather")],
        [InlineKeyboardButton("✨ *Extras*", callback_data="menu_extras")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = (update.callback_query.message.chat_id if update.callback_query else update.message.chat_id)
    await context.bot.send_message(chat_id, "*Main Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_menu_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Update the current message inline to show the main menu.
    This is used for a "back" button to avoid sending a new message.
    """
    keyboard = [
        [InlineKeyboardButton("📁 *Projects*", callback_data="menu_projects"),
         InlineKeyboardButton("📝 *Tasks*", callback_data="menu_tasks")],
        [InlineKeyboardButton("⏰ *Reminders*", callback_data="menu_reminders"),
         InlineKeyboardButton("🌦 *Weather*", callback_data="menu_weather")],
        [InlineKeyboardButton("✨ *Extras*", callback_data="menu_extras")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("*Main Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_projects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Projects submenu."""
    keyboard = [
        [InlineKeyboardButton("➕ *Add Project*", callback_data="add_project"),
         InlineKeyboardButton("📋 *Show Projects*", callback_data="show_projects")],
        [InlineKeyboardButton("🗑 *Delete Project*", callback_data="delete_project")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("*Projects Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Tasks submenu."""
    keyboard = [
        [InlineKeyboardButton("➕ *Add Task*", callback_data="add_task"),
         InlineKeyboardButton("👀 *View Tasks*", callback_data="view_tasks")],
        [InlineKeyboardButton("🔄 *Update Task*", callback_data="update_task"),
         InlineKeyboardButton("🗑 *Delete Task*", callback_data="delete_task")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("*Tasks Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_reminders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Reminders submenu."""
    keyboard = [
        [InlineKeyboardButton("⏰ *Set Reminder*", callback_data="set_reminder"),
         InlineKeyboardButton("⏹ *Stop Reminder*", callback_data="stop_reminder")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("*Reminders Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_weather_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Weather submenu."""
    keyboard = [
        [InlineKeyboardButton("🌤 *One-time Weather*", callback_data="weather_one_time"),
         InlineKeyboardButton("📅 *Set Weather Updates*", callback_data="weather_updates")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("*Weather Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_extras_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the Extras submenu."""
    keyboard = [
        [InlineKeyboardButton("💡 *Motivational Quotes*", callback_data="motivation"),
         InlineKeyboardButton("🍅 *Pomodoro Timer*", callback_data="pomodoro_timer")],
        [InlineKeyboardButton("❓ *Help*", callback_data="help")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("*Extras Menu:*", parse_mode="Markdown", reply_markup=reply_markup)

async def send_return_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Send a message with a 'Main Menu' button so the user can return.
    This sends a new message.
    """
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- BUTTON CALLBACK HANDLER ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks from all menus."""
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "back_inline_main":
            await send_menu_inline(update, context)
            return
        if data == "back_to_main":
            await send_menu(update, context)
            return
        elif data == "menu_projects":
            await send_projects_menu(update, context)
            return
        elif data == "menu_tasks":
            await send_tasks_menu(update, context)
            return
        elif data == "menu_reminders":
            await send_reminders_menu(update, context)
            return
        elif data == "menu_weather":
            await send_weather_menu(update, context)
            return
        elif data == "menu_extras":
            await send_extras_menu(update, context)
            return

        # ---------- PROJECTS COMMANDS ----------
        if data == "add_project":
            await query.edit_message_text("Send the project name to add it:")
            context.user_data['next_action'] = 'add_project'
            return
        elif data == "delete_project":
            await query.edit_message_text("Send the project name to delete it:")
            context.user_data['next_action'] = 'delete_project'
            return
        elif data == "show_projects":
            user_id = await get_user_id(update.effective_user.id)
            projects = await get_projects_from_db(user_id)
            if projects:
                project_list = "\n".join([f"- {proj}" for proj in projects])
                await query.edit_message_text(f"Your Projects:\n{project_list}")
            else:
                await query.edit_message_text("You have no projects yet.")
            return

        # ---------- TASKS COMMANDS ----------
        elif data == "add_task":
            await query.edit_message_text("Send the task description:")
            context.user_data['next_action'] = 'add_task'
            return
        elif data == "view_tasks":
            user_id = await get_user_id(update.effective_user.id)
            tasks = await get_tasks_from_db(user_id)
            if tasks:
                task_list = "\n".join([f"{task[0]}. {task[1]} (Status: {task[2]})" for task in tasks])
                await query.edit_message_text(f"📌 Your Tasks:\n{task_list}")
            else:
                await query.edit_message_text("You have no tasks yet.")
            return
        elif data == "update_task":
            user_id = await get_user_id(update.effective_user.id)
            tasks = await get_tasks_from_db(user_id)
            if not tasks:
                await query.edit_message_text("You have no tasks to update.")
                return
            keyboard = [
                [InlineKeyboardButton(f"{task[0]}: {task[1]}", callback_data=f"update_task_{task[0]}")]
                for task in tasks
            ]
            keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="menu_tasks"),
                             InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Select a task to update:", reply_markup=reply_markup)
            return
        elif data.startswith("update_task_"):
            task_id = data.split("_")[-1]
            keyboard = [
                [InlineKeyboardButton("Pending", callback_data=f"set_status_{task_id}_Pending")],
                [InlineKeyboardButton("In Progress", callback_data=f"set_status_{task_id}_In Progress")],
                [InlineKeyboardButton("Completed", callback_data=f"set_status_{task_id}_Completed")],
                [InlineKeyboardButton("⬅ Back", callback_data="menu_tasks"),
                 InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Choose a new status:", reply_markup=reply_markup)
            return
        elif data.startswith("set_status_"):
            parts = data.split("_")
            task_id = int(parts[2])
            new_status = parts[3].replace("_", " ")
            logger.info(f"Updating task {task_id} to status '{new_status}'")
            success = await db_update_task(task_id, new_status)
            if success:
                text = f"✅ Task {task_id} updated to *{new_status}*."
            else:
                text = "⚠️ Failed to update task. Please try again."
            user_id = await get_user_id(update.effective_user.id)
            tasks = await get_tasks_from_db(user_id)
            if tasks:
                task_list = "\n".join([f"{task[0]}. {task[1]} (Status: {task[2]})" for task in tasks])
                text += f"\n\n📌 *Updated Tasks:*\n{task_list}"
            await send_return_to_main_menu(update, context, text)
            return
        elif data == "delete_task":
            user_id = await get_user_id(update.effective_user.id)
            tasks = await get_tasks_from_db(user_id)
            if not tasks:
                await query.edit_message_text("You have no tasks to delete.")
                return
            keyboard = [
                [InlineKeyboardButton(f"{task[0]}: {task[1]}", callback_data=f"delete_task_{task[0]}")]
                for task in tasks
            ]
            keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="menu_tasks"),
                              InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Select a task to delete:", reply_markup=reply_markup)
            return
        elif data.startswith("delete_task_"):
            task_id = int(data.split("_")[-1])
            logger.info(f"Deleting task with ID: {task_id}")
            success = await db_delete_task(task_id)
            if success:
                text = f"🗑 Task {task_id} deleted successfully."
            else:
                text = "⚠️ Failed to delete task. Please try again."
            user_id = await get_user_id(update.effective_user.id)
            tasks = await get_tasks_from_db(user_id)
            if tasks:
                task_list = "\n".join([f"{task[0]}. {task[1]} (Status: {task[2]})" for task in tasks])
                text += f"\n\n📌 *Updated Tasks:*\n{task_list}"
            await send_return_to_main_menu(update, context, text)
            return

        # ---------- REMINDERS, WEATHER, EXTRAS ----------
        elif data == "set_reminder":
            await query.edit_message_text("Send the time in HH:MM format to set a daily reminder:")
            context.user_data['next_action'] = 'set_reminder'
            return
        elif data == "stop_reminder":
            reminder_stopped = await stop_reminder(update, context)
            if reminder_stopped:
                await send_return_to_main_menu(update, context, "⏹ Reminder stopped.")
            else:
                await send_return_to_main_menu(update, context, "No active reminders to stop.")
            return
        elif data == "motivation":
            quote = await get_random_quote(context)
            await send_return_to_main_menu(update, context, f"💡 Motivation:\n_{quote}_")
            return
        elif data == "weather_one_time":
            await query.edit_message_text("Send the location to get the current weather:")
            context.user_data['next_action'] = 'weather_one_time'
            return
        elif data == "weather_updates":
            await query.edit_message_text("Send the location and time (HH:MM) to set daily weather updates:")
            context.user_data['next_action'] = 'set_weather_updates'
            return
        elif data == "pomodoro_timer":
            await query.edit_message_text("🍅 Pomodoro Timer: Use /start_pomodoro to begin or /stop_pomodoro to stop.")
            return
        elif data == "help":
            keyboard = [
                [InlineKeyboardButton("➕ Add Project", callback_data="add_project"),
                 InlineKeyboardButton("🗑 Delete Project", callback_data="delete_project")],
                [InlineKeyboardButton("📌 Show Projects", callback_data="show_projects"),
                 InlineKeyboardButton("📝 Add Task", callback_data="add_task")],
                [InlineKeyboardButton("✅ View Tasks", callback_data="view_tasks"),
                 InlineKeyboardButton("🔄 Update Task", callback_data="update_task")],
                [InlineKeyboardButton("🗑 Delete Task", callback_data="delete_task"),
                 InlineKeyboardButton("⏰ Set Reminder", callback_data="set_reminder")],
                [InlineKeyboardButton("⏹ Stop Reminder", callback_data="stop_reminder"),
                 InlineKeyboardButton("🍅 Pomodoro Timer", callback_data="pomodoro_timer")],
                [InlineKeyboardButton("🌦 One-Time Weather", callback_data="weather_one_time"),
                 InlineKeyboardButton("📅 Set Weather Updates", callback_data="weather_updates")],
                [InlineKeyboardButton("💡 Get Motivation", callback_data="motivation")],
                [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
                 InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            help_text = ("🔹 *Here are the available commands:*\n\n"
                         "📌 Use `/add_project [name]` to add a project\n"
                         "📌 Use `/delete_project [name]` to delete a project\n"
                         "📌 Use `/set_reminder HH:MM` to schedule a reminder\n"
                         "📌 Use `/weather [location]` to check the weather\n\n"
                         "_Click a button below for quick actions:_")
            await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=reply_markup)
            return

        # Fallback: if no branch is matched, return to the main menu.
        await send_menu(update, context)

    except Exception as e:
        logger.error(f"Error in button_callback: {e}")
        await query.edit_message_text("An error occurred. Please try again later.")

# ---------- TEXT HANDLER ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for the next action."""
    try:
        next_action = context.user_data.get('next_action')

        if next_action == 'add_project':
            project_name = update.message.text.strip()
            user_id = await get_user_id(update.effective_user.id)
            if await add_project_to_db(user_id, project_name):
                await update.message.reply_text(f"Project '{project_name}' added successfully!")
            else:
                await update.message.reply_text(f"Project '{project_name}' already exists.")
            context.user_data['next_action'] = None

        elif next_action == 'delete_project':
            project_name = update.message.text.strip()
            user_id = await get_user_id(update.effective_user.id)
            if await delete_project_from_db(user_id, project_name):
                await update.message.reply_text(f"Project '{project_name}' deleted successfully!")
            else:
                await update.message.reply_text(f"Project '{project_name}' does not exist.")
            context.user_data['next_action'] = None

        elif next_action == 'set_reminder':
            try:
                reminder_time = datetime.strptime(update.message.text, "%H:%M").time()
                utc_time = datetime.combine(datetime.today(), reminder_time).astimezone(pytz.UTC).time()
                context.job_queue.run_daily(
                    callback=daily_reminder,
                    time=utc_time,
                    chat_id=update.effective_chat.id,
                    name=str(update.effective_chat.id),
                )
                await update.message.reply_text(f"Daily reminder set for {reminder_time.strftime('%H:%M')} UTC.")
            except ValueError:
                await update.message.reply_text("Invalid time format! Use HH:MM (24-hour format).")
            context.user_data['next_action'] = None

        elif next_action == 'weather_one_time':
            location = update.message.text.strip()
            weather_info = await get_weather(location)
            await update.message.reply_text(weather_info)
            context.user_data['next_action'] = None

        elif next_action == 'set_weather_updates':
            try:
                user_input = update.message.text.split()
                location = user_input[0]
                time_str = user_input[1]
                user_time = datetime.strptime(time_str, "%H:%M").time()
                utc_time = datetime.combine(datetime.today(), user_time).astimezone(pytz.UTC).time()
                context.job_queue.run_daily(
                    callback=send_daily_weather,
                    time=utc_time,
                    chat_id=update.effective_chat.id,
                    name=f"weather_update_{update.effective_user.id}",
                    data={"location": location, "chat_id": update.effective_chat.id},
                )
                await update.message.reply_text(f"Daily weather updates set for {location} at {time_str} UTC.")
            except (IndexError, ValueError):
                await update.message.reply_text("Invalid input! Use the format: [location] [HH:MM].")
            context.user_data['next_action'] = None

        elif next_action == 'add_task':
            task_description = update.message.text.strip()
            user_id = await get_user_id(update.effective_user.id)
            success = await add_task_to_db(user_id, task_description)
            if success:
                await update.message.reply_text(f"✅ Task added: {task_description}")
            else:
                await update.message.reply_text(f"❌ Failed to add task: {task_description}")
            context.user_data['next_action'] = None

        await send_menu(update, context)

    except Exception as e:
        logger.error(f"Error in handle_text: {e}")
        await update.message.reply_text("⚠️ An error occurred. Please try again.")

# ---------- HELP COMMAND ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provide help information with clickable buttons."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Project", callback_data="add_project"),
         InlineKeyboardButton("🗑 Delete Project", callback_data="delete_project")],
        [InlineKeyboardButton("📌 Show Projects", callback_data="show_projects"),
         InlineKeyboardButton("📝 Add Task", callback_data="add_task")],
        [InlineKeyboardButton("✅ View Tasks", callback_data="view_tasks"),
         InlineKeyboardButton("🔄 Update Task", callback_data="update_task")],
        [InlineKeyboardButton("🗑 Delete Task", callback_data="delete_task"),
         InlineKeyboardButton("⏰ Set Reminder", callback_data="set_reminder")],
        [InlineKeyboardButton("⏹ Stop Reminder", callback_data="stop_reminder"),
         InlineKeyboardButton("🍅 Pomodoro Timer", callback_data="pomodoro_timer")],
        [InlineKeyboardButton("🌦 One-Time Weather", callback_data="weather_one_time"),
         InlineKeyboardButton("📅 Set Weather Updates", callback_data="weather_updates")],
        [InlineKeyboardButton("💡 Get Motivation", callback_data="motivation")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_inline_main"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    help_text = ("🔹 *Here are the available commands:*\n\n"
                 "📌 Use `/add_project [name]` to add a project\n"
                 "📌 Use `/delete_project [name]` to delete a project\n"
                 "📌 Use `/set_reminder HH:MM` to schedule a reminder\n"
                 "📌 Use `/weather [location]` to check the weather\n\n"
                 "_Click a button below for quick actions:_")
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=reply_markup)

# ---------- COMMAND HANDLERS ----------
async def add_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = await get_user_id(update.effective_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /add_project [project_name]")
        return
    project_name = " ".join(context.args)
    if await add_project_to_db(user_id, project_name):
        await update.message.reply_text(f"Project '{project_name}' added!")
    else:
        await update.message.reply_text(f"Project '{project_name}' already exists.")

async def delete_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = await get_user_id(update.effective_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /delete_project [project_name]")
        return
    project_name = " ".join(context.args)
    if await delete_project_from_db(user_id, project_name):
        await update.message.reply_text(f"Project '{project_name}' deleted!")
    else:
        await update.message.reply_text(f"Project '{project_name}' does not exist.")

async def show_projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the user's projects."""
    user_id = await get_user_id(update.effective_user.id)
    if not user_id:
        await update.message.reply_text("Failed to retrieve user information.")
        return
    projects = await get_projects_from_db(user_id)
    if projects:
        project_list = "\n".join([f"- {proj[0]}: {proj[1] if proj[1] else 'No description'}" for proj in projects])
        await update.message.reply_text(f"Your Projects:\n{project_list}")
    else:
        await update.message.reply_text("You have no projects yet.")

async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /add_task command."""
    try:
        user_id = await get_user_id(update.effective_user.id)
        if len(context.args) < 1:
            await update.message.reply_text("Please provide a task description.")
            return
        description = " ".join(context.args)
        success = await add_task_to_db(user_id, description)
        if success:
            await update.message.reply_text(f"✅ Task added: {description}")
        else:
            await update.message.reply_text(f"❌ Failed to add task: {description}")
    except Exception as e:
        logger.error(f"Error in add_task_command: {e}")
        await update.message.reply_text("An error occurred while adding the task.")

async def view_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /view_tasks command."""
    try:
        user_id = await get_user_id(update.effective_user.id)
        tasks = await get_tasks_from_db(user_id)
        if not tasks:
            await update.message.reply_text("You have no tasks!")
        else:
            task_list = "\n".join([f"{task[0]}. {task[1]} (Status: {task[2]}, Due: {task[3] or 'No due date'})" for task in tasks])
            await update.message.reply_text(f"Your tasks:\n{task_list}")
    except Exception as e:
        logger.error(f"Error in view_tasks_command: {e}")
        await update.message.reply_text("An error occurred while retrieving tasks.")

async def update_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /update_task command."""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /update_task [task_id] [new_status]")
            return
        task_id = int(context.args[0])
        new_status = context.args[1]
        success = await db_update_task(task_id, new_status)
        if success:
            await update.message.reply_text(f"Task {task_id} updated to status: {new_status}.")
        else:
            await update.message.reply_text("Failed to update task. Check task ID.")
    except Exception as e:
        logger.error(f"Error in update_task_command: {e}")
        await update.message.reply_text("An error occurred while updating the task.")

async def delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /delete_task command."""
    try:
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /delete_task [task_id]")
            return
        task_id = int(context.args[0])
        success = await delete_task(task_id)
        if success:
            await update.message.reply_text(f"Task {task_id} deleted successfully.")
        else:
            await update.message.reply_text("Failed to delete task. Check task ID.")
    except Exception as e:
        logger.error(f"Error in delete_task_command: {e}")
        await update.message.reply_text("An error occurred while deleting the task.")

def setup_handlers(application):
    """Register all handlers."""
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    from bot.reminders import set_reminder, stop_reminder
    from bot.quotes import get_random_quote

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_project", add_project_command))
    application.add_handler(CommandHandler("delete_project", delete_project_command))
    application.add_handler(CommandHandler("show_projects", show_projects_command))
    application.add_handler(CommandHandler("set_reminder", set_reminder))
    application.add_handler(CommandHandler("stop_reminder", stop_reminder))
    application.add_handler(CommandHandler("motivation", get_random_quote))
    application.add_handler(CommandHandler("add_task", add_task_command))
    application.add_handler(CommandHandler("view_tasks", view_tasks_command))
    application.add_handler(CommandHandler("update_task", update_task_command))
    application.add_handler(CommandHandler("delete_task", delete_task_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
