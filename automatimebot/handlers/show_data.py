from typing import Dict
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import CallbackContext

from automatimebot import ISWORKING, SUMMARY
from automatimebot.abc import Session
from automatimebot.handlers.utils import (
    get_chat_name,
    get_user_name,
    pretty_time_delta,
    try_delete_message,
)
from automatimebot.database import get_summary


def data_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    buttons = [
        [InlineKeyboardButton(ISWORKING, callback_data=ISWORKING)],
        [InlineKeyboardButton(SUMMARY, callback_data=SUMMARY)],
    ]
    if not try_delete_message(
        context.bot, update.effective_chat, update.message.message_id
    ):
        return

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"What do you want to do {get_user_name(user)}?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


def handle_is_working(
    update: Update,
    context: CallbackContext,
    workers_in_chats: Dict[Chat, Dict[str, Session]],
):
    call = update.callback_query
    chat = get_chat_name(update.effective_chat)
    date = call.message.date

    # If chat is monitored
    if chat in workers_in_chats:
        workers_in_chat = workers_in_chats[chat]
        if workers_in_chat:
            workers_infos = [
                f"{worker} since {pretty_time_delta((date - session.start).total_seconds())}"
                f" on {session.comment}"
                for worker, session in workers_in_chat.items()
            ]
            workers_str = "\n".join(workers_infos)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Currently working:\n{workers_str}",
            )
            call.answer()
        else:
            call.answer(text="No one is working at the moment.")

    # If chat is not even instanciated
    else:
        call.answer(text="No one ever worked here since I'm alive.")
    call.delete_message()


def handle_summary(update: Update, context: CallbackContext):
    chat = get_chat_name(update.effective_chat)
    summary = get_summary(chat)
    call = update.callback_query
    msg = "Summary of time spent:\n" + "\n".join(
        [f"{user}: {pretty_time_delta(duration)}" for user, duration in summary.values]
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    call.answer()
    call.delete_message()
