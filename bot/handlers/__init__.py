from typing import Dict
from telegram import Chat, Update
from telegram.ext import CallbackContext

from bot import ISWORKING, SUMMARY
from bot.abc import Session
from bot.database import create_database
from bot.handlers.utils import get_chat_name, get_user_name
from bot.handlers.start import (
    handle_current_tasks_dict,
    send_session_start,
    handle_start,
)
from bot.handlers.stop import handle_stop, send_session_stop
from bot.handlers.load_tasks import store_task, handle_load_task
from bot.handlers.show_data import (
    handle_is_working,
    handle_summary,
    data_menu,
)


class Bot:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        create_database(db_path)
        self.workers_in_chats: Dict[Chat, Dict[str, Session]] = {}
        self.current_tasks_dict: dict = None
        self.wait_start_comment: Dict[str, bool] = {}
        self.wait_stop_comment: Dict[str, bool] = {}
        self.wait_tasks: str = None

    def start(self, update: Update, context: CallbackContext):
        chat = get_chat_name(update.effective_chat)
        if chat not in self.workers_in_chats:
            self.workers_in_chats[chat] = {}

        task_dict, username = handle_start(update, context, self.db_path)
        if task_dict is not None:
            self.current_tasks_dict = task_dict
        if username is not None:
            self.wait_start_comment[username] = True

    def start_session(
        self,
        update: Update,
        context: CallbackContext,
        comment: str,
    ) -> Session:
        author = get_user_name(update.effective_user)
        chat = get_chat_name(update.effective_chat)
        date = update.message.date

        task = (
            self.current_tasks_dict
            if isinstance(self.current_tasks_dict, str)
            else None
        )
        session = Session(author, date, comment, task)
        self.workers_in_chats[chat][author] = session
        return session

    def stop(self, update: Update, context: CallbackContext):
        username = handle_stop(update, context, self.workers_in_chats)
        self.wait_stop_comment[username] = True

    def data_menu(self, update: Update, context: CallbackContext):
        return data_menu(update, context)

    def load_task(self, update: Update, context: CallbackContext):
        author = get_user_name(update.effective_user)
        self.wait_tasks = author
        return handle_load_task(update, context)

    def textHandler(self, update: Update, context: CallbackContext):
        text: str = update.message.text
        author = get_user_name(update.effective_user)
        if author in self.wait_start_comment and self.wait_start_comment[author]:
            session = self.start_session(update, context, text)
            self.wait_start_comment[author] = False
            self.current_tasks_dict = None
            return send_session_start(update, context, session)
        if author in self.wait_stop_comment and self.wait_stop_comment[author]:
            self.wait_stop_comment[author] = False
            return send_session_stop(update, context, self.db_path, self.workers_in_chats)

    def yamlHandler(self,  update: Update, context: CallbackContext):
        author = get_user_name(update.effective_user)
        if self.wait_tasks is not None and author == self.wait_tasks:
            self.wait_tasks = None
            return store_task(update, context, self.db_path)

    def queryHandler(self, update: Update, context: CallbackContext):
        text: str = update.callback_query.data
        if isinstance(self.current_tasks_dict, dict):
            self.current_tasks_dict, username = handle_current_tasks_dict(
                update, context, self.current_tasks_dict
            )
            if username is not None:
                self.wait_start_comment[username] = True
            return
        if text == ISWORKING:
            return handle_is_working(update, context, self.workers_in_chats)
        if text.startswith(SUMMARY):
            return handle_summary(update, context, self.db_path)

    @staticmethod
    def unknown(update: Update, context: CallbackContext):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I didn't understand that command.",
        )
