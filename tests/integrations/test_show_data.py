""" Integration tests for data showing. """
# pylint: disable=unused-import, attribute-defined-outside-init

from datetime import datetime, timedelta
import pytest
import pytest_check as check
from pytest_mock import MockerFixture
from telegram import Chat, User
from bot.dataclasses import CompleteSession, Session
from tests import bot, user0, user1, chat

from bot.handlers import BotHandler
from bot.handlers.utils import get_chat_name, get_user_name
from bot.handlers.show_data import handle_summary, plot_gantt
from bot.database import (
    add_complete_session,
    add_tasks,
    get_all,
    get_summary,
)


class TestShowData:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        bot: BotHandler,
        chat: Chat,
        user0: User,
        user1: User,
    ):
        # --- Add tasks to db
        tasks = {
            "manger": {"poulet": 1, "pates": 2, "gateau": 3},
            "boire": {"eau": 1.5, "rhum": 7.5},
        }
        self.bot = bot
        self.chat = chat
        self.user0 = user0
        self.user1 = user1
        self.project = get_chat_name(chat)
        self.author0 = get_user_name(user0)
        self.author1 = get_user_name(user1)

        add_tasks(bot.db_path, self.project, tasks)

        self.day1 = datetime(2022, 7, 1, 1, 30)

        complete_session = CompleteSession(
            Session(self.author0, self.day1, "First work session", task="poulet"),
            self.day1 + timedelta(hours=1, minutes=24),
            stop_comment="Ended first work session",
        )
        add_complete_session(bot.db_path, self.project, complete_session)
        complete_session = CompleteSession(
            Session(
                self.author1,
                self.day1 + timedelta(minutes=10),
                "Parallel work session",
                task="pates",
            ),
            self.day1 + timedelta(hours=1, minutes=3),
            stop_comment="Ended first parallel work session",
        )
        add_complete_session(bot.db_path, self.project, complete_session)

    def test_get_summary(self):
        expected_times = {
            "@user0": timedelta(hours=1, minutes=24).seconds,
            "@user1": timedelta(minutes=53).seconds,
        }
        df = get_summary(self.bot.db_path, self.project)
        for user, time in df.to_numpy():
            check.equal(time, expected_times[user])

    def test_gantt(self):
        sessions_df = get_all(self.bot.db_path, "sessions")
        plot_gantt(sessions_df)
        assert True
