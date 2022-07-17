""" Module for work session start handler. """

from typing import Any, Dict, Tuple, Union
from telegram import Bot, CallbackQuery, Chat, Message, User

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


def session_comment_txt(session: Session) -> str:
    """Generate a start message for the given session.

    Args:
        session (Session): Session to generate the message from.

    Returns:
        str: Generated starting message for the Session.
    """
    task_txt = f"{session.author} started working"
    if not (session.task or session.start_comment):
        return task_txt

    start_comment = session.start_comment
    if session.task and session.start_comment:
        start_comment = f"({session.start_comment})"

    suffix_parts = [s for s in (" on", session.task, start_comment) if s is not None]
    return task_txt + " ".join(suffix_parts)


def start_msg_format(session: Session):
    return f"{START_CODE} {session_comment_txt(session)}"


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
        bot.send_message(
            chat_id=chat.id,
            text="Choose a task:",
            reply_markup=reply_markup,
        )
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


def _get_next_task_layer(current_tasks_dict: Dict[str, Union[dict, Any]], data: str):
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
    current_tasks_dict, key = _get_next_task_layer(current_tasks_dict, query.data)

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
