""" Module for telegram bot handlers. """

from typing import Dict
from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup, User

from telegram.ext import CallbackContext

from bot import ISWORKING, SUMMARY
from bot.dataclasses import Session
from bot.database import create_database
from bot.handlers.utils import get_chat_name, get_user_name, try_delete_message
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
)


class Bot:
    """The global Bot class to handle users interactions."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        create_database(db_path)
        self.workers_in_chats: Dict[Chat, Dict[str, Session]] = {}
        self.current_tasks_dict: dict = None
        self.wait_start_comment: Dict[str, bool] = {}
        self.wait_stop_comment: Dict[str, bool] = {}
        self.wait_tasks: Dict[str, bool] = {}

    def start(self, update: Update, context: CallbackContext) -> None:
        """Let a user start a task.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.
        """
        chat = get_chat_name(update.effective_chat)
        if chat not in self.workers_in_chats:
            self.workers_in_chats[chat] = {}

        task_dict, username = handle_start(update, context, self.db_path)
        if task_dict:
            self.current_tasks_dict = task_dict
        if username:
            self.wait_start_comment[username] = True

    def start_session(
        self,
        update: Update,
        comment: str,
    ) -> Session:
        """Start a working session for the user that sent the message.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.
            comment (str): Comment given by the user.

        Returns:
            Session: _description_
        """
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

    def stop(self, update: Update, context: CallbackContext) -> None:
        """Stop a session for the given user.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.
        """
        username = handle_stop(update, context, self.workers_in_chats)
        if username:
            self.wait_stop_comment[username] = True

    def data_menu(self, update: Update, context: CallbackContext) -> None:
        """Display the data menu.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.

        """
        user = update.effective_user
        buttons = [
            [InlineKeyboardButton(ISWORKING, callback_data=ISWORKING)],
            [InlineKeyboardButton(SUMMARY, callback_data=SUMMARY)],
        ]
        if not try_delete_message(
            context.bot,
            update.effective_chat,
            update.message.message_id,
        ):
            return

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"What do you want to do {get_user_name(user)}?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    def load_task(self, update: Update, context: CallbackContext) -> None:
        """Load a tasks yaml file.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.

        """
        author = get_user_name(update.effective_user)
        self.wait_tasks[author] = True
        handle_load_task(update, context)

    def textHandler(self, update: Update, context: CallbackContext):
        """Handle a text input.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.

        """
        text: str = update.message.text
        author = get_user_name(update.effective_user)
        if author in self.wait_start_comment and self.wait_start_comment[author]:
            session = self.start_session(update, text)
            self.wait_start_comment[author] = False
            self.current_tasks_dict = None
            send_session_start(update, context, session)
        if author in self.wait_stop_comment and self.wait_stop_comment[author]:
            self.wait_stop_comment[author] = False
            send_session_stop(update, context, self.db_path, self.workers_in_chats)

    def yamlHandler(self, update: Update, context: CallbackContext):
        """Handle a yaml file input.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.

        """
        author = get_user_name(update.effective_user)
        if author in self.wait_tasks and self.wait_tasks[author]:
            self.wait_tasks[author] = False
            store_task(update, context, self.db_path)

    def queryHandler(self, update: Update, context: CallbackContext):
        """Handle queries inputs.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.
        """
        text: str = update.callback_query.data
        if isinstance(self.current_tasks_dict, dict):
            self.current_tasks_dict, username = handle_current_tasks_dict(
                update, context, self.current_tasks_dict
            )
            if username is not None:
                self.wait_start_comment[username] = True
        elif text == ISWORKING:
            handle_is_working(update, context, self.workers_in_chats)
        elif text.startswith(SUMMARY):
            handle_summary(update, context, self.db_path)

    @staticmethod
    def unknown(update: Update, context: CallbackContext):
        """Handle unknown commands.

        Args:
            update (Update): Incomming update.
            context (CallbackContext): Context of the update.
        """
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I didn't understand that command.",
        )
