from datetime import datetime
from telegram import Chat, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext

from automatimebot import (
    START,
    START_CODE,
    STOP,
    STOP_CODE,
    ISWORKING,
    SUMMARY,
    Task,
    CompleteTask,
    workers_in_chats,
    wait_comment,
)
from automatimebot.utils import pretty_time_delta
from automatimebot.logging import get_logger
from automatimebot.database import add_complete_task, get_all_tasks

LOGGER = get_logger(__name__)


def start_msg_format(task: Task):
    return f"{START_CODE} {task.author} {task.comment}"


def stop_msg_format(complete_task: CompleteTask):
    task = complete_task.task
    human_timestamp = pretty_time_delta(complete_task.duration.total_seconds())
    return (
        f"{STOP_CODE} {task.author} stopped working"
        f" on {task.comment} after {human_timestamp} [{complete_task.duration}]"
    )


def get_chat_name(chat: Chat):
    if chat.type == "private":
        return chat.full_name
    else:
        return chat.title


def menu(update: Update, context: CallbackContext):
    buttons = [
        [KeyboardButton(START)],
        [KeyboardButton(STOP)],
        [KeyboardButton(ISWORKING)],
        [KeyboardButton(SUMMARY)],
    ]
    author = f"@{update.effective_user.username}"
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"What do you want to do {author}?",
        reply_markup=ReplyKeyboardMarkup(buttons),
    )


def messageHandler(update: Update, context: CallbackContext):
    text: str = update.message.text
    author = f"@{update.effective_user.username}"
    if ISWORKING in text:
        handle_is_working(update, context)
    elif text.startswith(STOP):
        return handle_stop(update, context)
    elif text.startswith(START):
        return handle_start(update, context)
    elif text.startswith(SUMMARY):
        return handle_summary(update, context)
    elif wait_comment is not None and author == wait_comment:
        return send_task_start(update, context, text)


def handle_start(update: Update, context: CallbackContext):
    global workers_in_chats
    global wait_comment
    author = f"@{update.effective_user.username}"
    chat = get_chat_name(update.effective_chat)
    content = update.message.text.split(" ")[1:]
    if chat not in workers_in_chats:
        workers_in_chats[chat] = {}
    if content:
        if author not in workers_in_chats[chat]:
            send_task_start(update, context, " ".join(content))
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please {author} comment what you will work on.",
        )
        wait_comment = author


def send_task_start(
    update: Update,
    context: CallbackContext,
    comment: str,
):
    global workers_in_chats
    global wait_comment
    author = f"@{update.effective_user.username}"
    chat = get_chat_name(update.effective_chat)
    date = update.message.date

    new_task = Task(author, date, comment)
    workers_in_chats[chat][author] = new_task
    msg = start_msg_format(new_task)

    LOGGER.info(f"Update on {chat}: {msg}")
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    wait_comment = None


def handle_stop(update: Update, context: CallbackContext):
    global workers_in_chats
    author = f"@{update.effective_user.username}"
    chat = get_chat_name(update.effective_chat)
    date = update.message.date
    if chat in workers_in_chats and author in workers_in_chats[chat]:
        task = workers_in_chats[chat].pop(author)
        complete_task = CompleteTask(task, date)
        add_complete_task(chat, complete_task)
        msg = stop_msg_format(complete_task)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        LOGGER.info(f"Update on {chat}: {msg}")


def handle_is_working(update: Update, context: CallbackContext):
    global workers_in_chats
    chat = get_chat_name(update.effective_chat)
    date = update.message.date

    # If chat is monitored
    if chat in workers_in_chats:
        workers_in_chat = workers_in_chats[chat]
        if workers_in_chat:
            workers_infos = [
                f"{worker} since {pretty_time_delta((date - task.start).total_seconds())}"
                f" on {task.comment}"
                for worker, task in workers_in_chat.items()
            ]
            workers_str = "\n".join(workers_infos)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Currently working:\n{workers_str}",
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No one is working at the moment.",
            )

    # If chat is not even instanciated
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No one ever worked here since I'm alive.",
        )


def handle_summary(update: Update, context: CallbackContext):
    chat = get_chat_name(update.effective_chat)
    tasks_complete = get_all_tasks(chat)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{tasks_complete}")


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )
