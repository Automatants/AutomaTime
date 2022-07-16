""" Module for utils functions. """

from typing import List
from telegram import (
    Bot,
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    User,
)


def pretty_time_delta(seconds, compact=False):
    seconds = int(seconds)

    jeh, seconds = divmod(seconds, 28800)
    jeh = f"{jeh:d}JEH" if jeh > 0 else ""

    hours, seconds = divmod(seconds, 3600)
    hours = f"{hours:d}h" if hours > 0 else ""

    minutes, seconds = divmod(seconds, 60)
    minutes = f"{minutes:d}m" if minutes > 0 else ""

    seconds = f"{seconds:d}s"
    sep = "" if compact else " "
    return sep.join((jeh, hours, minutes, seconds))


def get_chat_name(chat: Chat):
    if chat.type == "private":
        return chat.full_name
    return chat.title


def get_user_name(user: User):
    return f"@{user.username}"


def try_delete_message(bot: Bot, chat: Chat, message_id) -> bool:
    if (
        chat.type == "private"
        or bot.getChatMember(chat.id, bot.bot.id).can_delete_messages
    ):
        bot.delete_message(chat.id, message_id)
        return True
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


def edit_reply_markup(
    text: str,
    query: CallbackQuery,
    options: List[str],
):
    reply_markup = create_reply_markup(options)
    query.edit_message_text(text)
    query.edit_message_reply_markup(reply_markup)
