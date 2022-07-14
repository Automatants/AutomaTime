""" Module for tasks loaders handler. """

from telegram import Update
from telegram.ext import CallbackContext

from bot.handlers.utils import get_chat_name, get_user_name
from bot.tasks import read_tasks
from bot.database import add_tasks
from bot.logging import get_logger

LOGGER = get_logger(__name__)


def store_task(update: Update, context: CallbackContext, db_path: str):
    chat = get_chat_name(update.effective_chat)
    author = get_user_name(update.effective_user)

    yaml_file = update.message.document.get_file()
    tasks, tasks_dict = read_tasks(yaml_file)
    add_tasks(db_path, chat, tasks, tasks_dict)

    context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    context.bot.send_message(
        update.effective_chat.id, f"{author} has updated project tasks."
    )
    tasks_str = str([task for task, _ in tasks])
    LOGGER.info("Tasks uploaded on %s: %s", chat, tasks_str)


def handle_load_task(update: Update, context: CallbackContext):
    author = get_user_name(update.effective_user)
    context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    context.bot.send_message(
        update.effective_chat.id, f"Please {author} send tasks in yaml format."
    )
