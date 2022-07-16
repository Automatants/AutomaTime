""" Module for work session start handler. """

from typing import Any, Dict, Tuple, Union
from telegram import Bot, CallbackQuery, Chat, Update, Message, User
from telegram.ext import CallbackContext

from bot import START_CODE
from bot.dataclasses import Session
from bot.handlers.utils import (
    create_reply_markup,
    get_chat_name,
    try_delete_message,
    get_user_name,
    edit_reply_markup,
)
from bot.tasks import read_tasks
from bot.database import get_project_tasks_dict
from bot.logging import get_logger


LOGGER = get_logger(__name__)


def session_comment_txt(session: Session):
    task_txt = ""
    if session.task and session.start_comment:
        task_txt = f" on {session.task} ({session.start_comment})"
    elif session.task is not None:
        task_txt = f" on {session.task}"
    elif session.start_comment is not None:
        task_txt = f" on {session.start_comment}"
    return task_txt


def start_msg_format(session: Session):
    return (
        f"{START_CODE} {session.author} started working{session_comment_txt(session)}"
    )


def handle_start(
    user: User,
    bot: Bot,
    chat: Chat,
    message: Message,
    query: CallbackQuery,
    db_path: str,
) -> Tuple[dict, str]:

    if not try_delete_message(bot, chat, message.message_id):
        return {}, ""

    tasks_text = get_project_tasks_dict(db_path, get_chat_name(chat))
    if tasks_text:
        _, tasks_dict = read_tasks(tasks_text[0][0])
        reply_markup = create_reply_markup(list(tasks_dict.keys()))
        text = "Choose a task:"
        bot.send_message(chat_id=chat.id, text=text, reply_markup=reply_markup)
        return tasks_dict, None

    ask_comment(user, bot, chat, query)
    if query is not None:
        query.delete_message()
    return {}, get_user_name(user)


def send_session_start(
    bot: Bot,
    chat: Chat,
    message: Message,
    session: Session,
):
    chat_name = get_chat_name(chat)
    bot.delete_message(chat, message.message_id)
    msg = start_msg_format(session)
    bot.send_message(chat, msg)
    LOGGER.info("Update on %s: %s", chat_name, msg)


def ask_comment(user: User, bot: Bot, chat: Chat, query: CallbackQuery):
    msg = f"Please {get_user_name(user)} comment what you will work on."
    if query is not None:
        query.answer(text=msg)
    else:
        bot.send_message(chat.id, msg)


def _get_next_layer(current_tasks_dict: Dict[str, Union[dict, Any]], data: str):
    if data in current_tasks_dict:
        return current_tasks_dict[data], data
    for key in current_tasks_dict:
        if key.startswith(data):
            current_tasks_dict = current_tasks_dict[key]
            return current_tasks_dict[key], key
    raise KeyError(f"{data} not found in current_tasks_dict")


def handle_current_tasks_dict(
    user: User,
    bot: Bot,
    chat: Chat,
    query: CallbackQuery,
    current_tasks_dict: Dict[str, Union[dict, Any]],
):
    current_tasks_dict, key = _get_next_layer(current_tasks_dict, query.data)

    if isinstance(current_tasks_dict, dict):
        edit_reply_markup("Choose a task:", query, list(current_tasks_dict.keys()))
        query.answer()
        username = get_user_name(user)
    else:
        current_tasks_dict = key
        ask_comment(user, bot, chat, query)
        username = None
        query.delete_message()
    return current_tasks_dict, username
