from typing import Any, Dict, Union
from telegram import Update
from telegram.ext import CallbackContext

from automatimebot import START_CODE
from automatimebot.abc import Session
from automatimebot.handlers.utils import (
    create_reply_markup,
    task_comment_txt,
    get_chat_name,
    try_delete_message,
    get_user_name,
    edit_reply_markup,
)
from automatimebot.tasks import read_tasks
from automatimebot.database import get_project_tasks_dict
from automatimebot.logging import get_logger


LOGGER = get_logger(__name__)


def start_msg_format(session: Session):
    return f"{START_CODE} {session.author} started working{task_comment_txt(session)}"


def handle_start(
    update: Update,
    context: CallbackContext,
):
    if not try_delete_message(
        context.bot, update.effective_chat, update.message.message_id
    ):
        return

    tasks_text = get_project_tasks_dict(get_chat_name(update.effective_chat))
    if tasks_text:
        _, tasks_dict = read_tasks(tasks_text[0][0])
        reply_markup = create_reply_markup(list(tasks_dict.keys()))
        text = "Choose a task:"
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup
        )
        return tasks_dict, None
    else:
        ask_comment(update, context)
        update.callback_query.delete_message()
        return None, get_user_name(update.effective_user)


def send_session_start(
    update: Update,
    context: CallbackContext,
    session: Session,
):
    chat = get_chat_name(update.effective_chat)
    context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    msg = start_msg_format(session)
    context.bot.send_message(update.effective_chat.id, msg)
    LOGGER.info(f"Update on {chat}: {msg}")


def ask_comment(update: Update, context: CallbackContext):
    author = get_user_name(update.effective_user)
    call = update.callback_query
    call.answer(text=f"Please {author} comment what you will work on.")


def handle_current_tasks_dict(
    update: Update,
    context: CallbackContext,
    current_tasks_dict: Dict[str, Union[dict, Any]],
):
    call = update.callback_query
    data = call.data

    try:
        current_tasks_dict = current_tasks_dict[data]
    except KeyError:
        for key in current_tasks_dict:
            if key.startswith(data):
                current_tasks_dict = current_tasks_dict[key]
                data = key
                break

    if isinstance(current_tasks_dict, dict):
        edit_reply_markup(update, context, list(current_tasks_dict.keys()))
        call.answer()
        username = get_user_name(update.effective_user)
    else:
        current_tasks_dict = data
        ask_comment(update, context)
        username = None
        call.delete_message()
    return current_tasks_dict, username
