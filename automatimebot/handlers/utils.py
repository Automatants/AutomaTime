from typing import List
from telegram import Bot, Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import CallbackContext

from automatimebot.abc import Session


def pretty_time_delta(seconds):
    seconds = int(seconds)
    jeh, seconds = divmod(seconds, 28800)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if jeh > 0:
        return "%dJEH%dh%dm%ds" % (jeh, hours, minutes, seconds)
    elif hours > 0:
        return "%dh%dm%ds" % (hours, minutes, seconds)
    elif minutes > 0:
        return "%dm%ds" % (minutes, seconds)
    else:
        return "%ds" % (seconds,)


def get_chat_name(chat: Chat):
    if chat.type == "private":
        return chat.full_name
    else:
        return chat.title


def get_user_name(user: User):
    return f"@{user.username}"


def task_comment_txt(session: Session):
    task_txt = ""
    if session.task and session.comment:
        task_txt = f" on {session.task} ({session.comment})"
    elif session.task is not None:
        task_txt = f" on {session.task}"
    elif session.comment is not None:
        task_txt = f" on {session.comment}"
    return task_txt


def try_delete_message(bot: Bot, chat: Chat, message_id) -> bool:
    if (
        chat.type == "private"
        or bot.getChatMember(chat.id, bot.bot.id).can_delete_messages
    ):
        bot.delete_message(chat.id, message_id)
        return True
    else:
        bot.send_message(chat.id, "Please allow me to delete messages!")
        return False


def create_reply_markup(options: List[str]):
    def ensure_small(key: str):
        while len(key.encode("utf-8")) > 63:
            key = key[:-1]
        return key

    buttons = [
        [InlineKeyboardButton(key, callback_data=ensure_small(key))] for key in options
    ]
    return InlineKeyboardMarkup(buttons)


def edit_reply_markup(update: Update, context: CallbackContext, options: List[str]):
    text = "Choose a task:"
    call = update.callback_query
    reply_markup = create_reply_markup(options)
    call.edit_message_text(text)
    call.edit_message_reply_markup(reply_markup)