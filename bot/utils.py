import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("CodeAssistantBot")

async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main menu as a new message."""
    keyboard = [
        [
            InlineKeyboardButton("Add Project", callback_data="add_project"),
            InlineKeyboardButton("Show Projects", callback_data="show_projects"),
        ],
        [
            InlineKeyboardButton("Delete Project", callback_data="delete_project"),
            InlineKeyboardButton("Set Reminder", callback_data="set_reminder"),
        ],
        [
            InlineKeyboardButton("Stop Reminder", callback_data="stop_reminder"),
            InlineKeyboardButton("Motivation", callback_data="motivation"),
        ],
        [InlineKeyboardButton("Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = update.callback_query.message.chat_id if update.callback_query else update.message.chat_id
    await context.bot.send_message(chat_id, "Main Menu:", reply_markup=reply_markup)
