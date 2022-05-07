from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import CallbackContext

from automatimebot import (
    START,
    START_CODE,
    STOP,
    STOP_CODE,
    ISWORKING,
    SUMMARY,
    LOAD_TASKS,
    Task,
    CompleteTask,
    workers_in_chats,
    wait_comment,
    wait_tasks,
)
from automatimebot.utils import pretty_time_delta
from automatimebot.logging import get_logger
from automatimebot.database import add_complete_task, get_summary
from automatimebot.tasks import read_tasks, print_tasks

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


def get_user_name(user: User):
    return f"@{user.username}"


def is_working(user: User, chat: Chat):
    global workers_in_chats
    chat_name = get_chat_name(chat)
    return (
        chat_name in workers_in_chats
        and get_user_name(user) in workers_in_chats[chat_name]
    )


def menu(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat
    start_button = InlineKeyboardButton(START, callback_data=START)
    stop_button = InlineKeyboardButton(STOP, callback_data=STOP)
    action_button = stop_button if is_working(user, chat) else start_button
    buttons = [
        [action_button],
        [
            InlineKeyboardButton(ISWORKING, callback_data=ISWORKING),
            InlineKeyboardButton(SUMMARY, callback_data=SUMMARY),
        ],
        [InlineKeyboardButton(LOAD_TASKS, callback_data=LOAD_TASKS)],
    ]

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"What do you want to do {get_user_name(user)}?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    context.bot.delete_message(update.effective_chat.id, update.message.message_id)


def messageHandler(update: Update, context: CallbackContext):
    global wait_comment
    global wait_tasks
    text: str = update.message.text
    author = get_user_name(update.effective_user)
    if wait_comment is not None and author == wait_comment:
        return send_start(update, context, text)
    if wait_tasks is not None and author == wait_tasks:
        return store_task(update, context)


def queryHandler(update: Update, context: CallbackContext):
    text: str = update.callback_query.data
    if text == ISWORKING:
        handle_is_working(update, context)
    elif text.startswith(STOP):
        handle_stop(update, context)
    elif text.startswith(START):
        handle_start(update, context)
    elif text.startswith(SUMMARY):
        handle_summary(update, context)
    elif text.startswith(LOAD_TASKS):
        handle_load_task(update, context)
    update.callback_query.delete_message()


def handle_start(update: Update, context: CallbackContext):
    global workers_in_chats
    global wait_comment
    author = get_user_name(update.effective_user)
    chat = get_chat_name(update.effective_chat)
    call = update.callback_query
    if chat not in workers_in_chats:
        workers_in_chats[chat] = {}
    call.answer(text=f"Please {author} comment what you will work on.")
    wait_comment = author


def send_start(
    update: Update,
    context: CallbackContext,
    comment: str,
):
    global workers_in_chats
    global wait_comment
    author = get_user_name(update.effective_user)
    chat = get_chat_name(update.effective_chat)
    date = update.message.date

    new_task = Task(author, date, comment)
    workers_in_chats[chat][author] = new_task
    msg = start_msg_format(new_task)

    LOGGER.info(f"Update on {chat}: {msg}")
    context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    context.bot.send_message(update.effective_chat.id, msg)
    wait_comment = None


def handle_stop(update: Update, context: CallbackContext):
    global workers_in_chats
    author = get_user_name(update.effective_user)
    chat = get_chat_name(update.effective_chat)
    date = update.callback_query.message.date
    if chat in workers_in_chats and author in workers_in_chats[chat]:
        task = workers_in_chats[chat].pop(author)
        complete_task = CompleteTask(task, date)
        add_complete_task(chat, complete_task)
        msg = stop_msg_format(complete_task)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        LOGGER.info(f"Update on {chat}: {msg}")


def handle_is_working(update: Update, context: CallbackContext):
    global workers_in_chats
    call = update.callback_query
    chat = get_chat_name(update.effective_chat)
    date = call.message.date

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
            call.answer()
        else:
            call.answer(text="No one is working at the moment.")

    # If chat is not even instanciated
    else:
        call.answer(text="No one ever worked here since I'm alive.")


def handle_summary(update: Update, context: CallbackContext):
    chat = get_chat_name(update.effective_chat)
    summary = get_summary(chat)
    msg = "Summary of time spent:\n" + "\n".join(
        [f"{user}: {pretty_time_delta(duration)}" for user, duration in summary.values]
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    update.callback_query.answer()


def store_task(update: Update, context: CallbackContext):
    tasks, tasks_dicts = read_tasks(update.message.text)


def handle_load_task(update: Update, context: CallbackContext):
    global workers_in_chats
    global wait_tasks
    author = get_user_name(update.effective_user)
    call = update.callback_query
    call.answer(text=f"Please {author} send tasks in yaml format.")
    wait_tasks = author


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )
