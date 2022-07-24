import pytest
from pytest_mock import MockerFixture
from telegram import Chat, User
from bot.handlers import BotHandler


@pytest.fixture
def bot(mocker: MockerFixture, tmpdir):
    mocker.patch("bot.handlers.send_session_start")
    db_path = tmpdir.mkdir("sub").join("tmp.db")
    return BotHandler(db_path)


@pytest.fixture
def user0():
    return User(0, "user0", is_bot=False, username="user0")


@pytest.fixture
def user1():
    return User(1, "user1", is_bot=False, username="user1")


@pytest.fixture
def chat():
    return Chat(0, "supergroup", title="SuperGroupChat")
