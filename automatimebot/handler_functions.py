from typing import List
from telegram import Bot, Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import CallbackContext

from automatimebot import (
    START,
    START_CODE,
    STOP,
    STOP_CODE,
    ISWORKING,
    SUMMARY,
    LOAD_TASKS,
    Session,
    CompleteSession,
    workers_in_chats,
    current_tasks_dict,
    wait_comment,
    wait_tasks,
)
from automatimebot.utils import pretty_time_delta
from automatimebot.logging import get_logger
from automatimebot.database import (
    add_complete_session,
    get_project_tasks_dict,
    get_summary,
    add_tasks,
)
from automatimebot.tasks import read_tasks

LOGGER = get_logger(__name__)


def task_comment_txt(session: Session):
    task_txt = ""
    if session.task and session.comment:
        task_txt = f" on {session.task} ({session.comment})"
    elif session.task is not None:
        task_txt = f" on {session.task}"
    elif session.comment is not None:
        task_txt = f" on {session.comment}"
    return task_txt


def start_msg_format(session: Session):
    return f"{START_CODE} {session.author} started working{task_comment_txt(session)}"


def stop_msg_format(complete_session: CompleteSession):
    session = complete_session.session
    human_timestamp = pretty_time_delta(complete_session.duration.total_seconds())
    return (
        f"{STOP_CODE} {session.author} stopped working"
        f"{task_comment_txt(session)} after {human_timestamp} [{complete_session.duration}]"
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

    if isinstance(current_tasks_dict, dict):
        handle_current_tasks_dict(update, context)
        return

    if text == ISWORKING:
        handle_is_working(update, context)
    elif text.startswith(SUMMARY):
        handle_summary(update, context)
    update.callback_query.delete_message()


def handle_start(update: Update, context: CallbackContext):
    global workers_in_chats
    global current_tasks_dict
    chat = get_chat_name(update.effective_chat)
    call = update.callback_query

    if not try_delete_message(
        context.bot, update.effective_chat, update.message.message_id
    ):
        return

    if chat not in workers_in_chats:
        workers_in_chats[chat] = {}

    tasks_text = get_project_tasks_dict(chat)
    if tasks_text:
        _, tasks_dict = read_tasks(tasks_text[0][0])
        current_tasks_dict = tasks_dict
        edit_reply_markup(update, context, list(current_tasks_dict.keys()))
        call.answer()
    else:
        ask_comment(update, context)
        update.callback_query.delete_message()


def ask_comment(update: Update, context: CallbackContext):
    global wait_comment
    author = get_user_name(update.effective_user)
    call = update.callback_query
    call.answer(text=f"Please {author} comment what you will work on.")
    wait_comment = author


def handle_current_tasks_dict(update: Update, context: CallbackContext):
    global current_tasks_dict
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
    else:
        current_tasks_dict = data
        ask_comment(update, context)
        call.delete_message()


def edit_reply_markup(update: Update, context: CallbackContext, new_options: List[str]):
    def ensure_small(key: str):
        while len(key.encode("utf-8")) > 63:
            key = key[:-1]
        return key

    buttons = [
        [InlineKeyboardButton(key, callback_data=ensure_small(key))]
        for key in new_options
    ]

    text = "Choose a task:"
    call = update.callback_query
    if call is None:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        call.edit_message_text(text)
        call.edit_message_reply_markup(InlineKeyboardMarkup(buttons))


def send_start(
    update: Update,
    context: CallbackContext,
    comment: str,
):
    global workers_in_chats
    global wait_comment
    global current_tasks_dict

    author = get_user_name(update.effective_user)
    chat = get_chat_name(update.effective_chat)
    date = update.message.date

    task = current_tasks_dict if isinstance(current_tasks_dict, str) else None
    session = Session(author, date, comment, task)
    workers_in_chats[chat][author] = session

    context.bot.delete_message(update.effective_chat.id, update.message.message_id)

    msg = start_msg_format(session)
    context.bot.send_message(update.effective_chat.id, msg)
    wait_comment = None
    current_tasks_dict = None
    LOGGER.info(f"Update on {chat}: {msg}")


def handle_stop(update: Update, context: CallbackContext):
    global workers_in_chats
    author = get_user_name(update.effective_user)
    chat = get_chat_name(update.effective_chat)
    date = update.message.date

    if not try_delete_message(
        context.bot, update.effective_chat, update.message.message_id
    ):
        return

    if chat in workers_in_chats and author in workers_in_chats[chat]:
        session = workers_in_chats[chat].pop(author)
        complete_session = CompleteSession(session, date)
        add_complete_session(chat, complete_session)
        msg = stop_msg_format(complete_session)
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


def handle_summary(update: Update, context: CallbackContext):
    chat = get_chat_name(update.effective_chat)
    summary = get_summary(chat)
    msg = "Summary of time spent:\n" + "\n".join(
        [f"{user}: {pretty_time_delta(duration)}" for user, duration in summary.values]
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    update.callback_query.answer()


def store_task(update: Update, context: CallbackContext):
    chat = get_chat_name(update.effective_chat)
    tasks, _ = read_tasks(update.message.text)
    author = get_user_name(update.effective_user)
    add_tasks(chat, tasks, update.message.text)
    context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    context.bot.send_message(
        update.effective_chat.id, f"{author} has updated project tasks."
    )
    LOGGER.info(f"Tasks uploaded on {chat}: {[task for task, _ in tasks]}")


def handle_load_task(update: Update, context: CallbackContext):
    global workers_in_chats
    global wait_tasks
    author = get_user_name(update.effective_user)
    context.bot.delete_message(update.effective_chat.id, update.message.message_id)
    context.bot.send_message(
        update.effective_chat.id, f"Please {author} send tasks in yaml format."
    )
    wait_tasks = author


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )
