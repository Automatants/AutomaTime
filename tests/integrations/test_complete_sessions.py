""" Test for starting a work session from the user perspective. """

import pytest_check as check
from pytest_mock import MockerFixture

from telegram import Chat, User
from bot.database import add_tasks, get_project_tasks_dict
from bot.dataclasses import CompleteSession

from bot.handlers import BotHandler
from bot.handlers.utils import get_chat_name, get_user_name
from tests import bot, user0 as user, chat  # pylint: disable=unused-import


def test_complete_session_without_tasks(
    mocker: MockerFixture, bot: BotHandler, chat: Chat, user: User
):
    """should be able to make a complete work session without a knowned tasks list"""
    username = get_user_name(user)
    chat_name = get_chat_name(chat)

    # --- \start
    update = mocker.MagicMock(effective_chat=chat, effective_user=user)
    context = mocker.MagicMock()
    bot.start(update, context)
    check.is_true(bot.wait_start_comment.get(username))

    # --- start comment
    msg = mocker.MagicMock(text="test start")
    update = mocker.MagicMock(effective_chat=chat, effective_user=user, message=msg)
    context = mocker.MagicMock()
    bot.textHandler(update, context)
    check.is_false(bot.wait_start_comment.get(username))
    session = bot.workers_in_chats.get(chat_name, {}).get(get_user_name(user))
    check.is_not_none(session)
    if session:
        check.is_none(session.task)
        check.equal(session.start_comment, msg.text)

    # --- /stop
    update = mocker.MagicMock(effective_chat=chat, effective_user=user)
    context = mocker.MagicMock()
    bot.stop(update, context)
    check.is_true(bot.wait_stop_comment.get(get_user_name(user)))

    # --- stop comment
    msg = mocker.MagicMock(text="test stop")
    update = mocker.MagicMock(effective_chat=chat, effective_user=user, message=msg)
    context = mocker.MagicMock()
    add_complete_session = mocker.patch("bot.handlers.stop.add_complete_session")
    bot.textHandler(update, context)
    check.is_false(bot.wait_stop_comment.get(get_user_name(user)))
    check.is_true(add_complete_session.called)
    if add_complete_session.called:
        complete_session: CompleteSession = add_complete_session.call_args.args[-1]
        check.equal(complete_session.stop_comment, msg.text)
        check.equal(complete_session.session, session)


def test_complete_session_with_tasks(
    mocker: MockerFixture, bot: BotHandler, chat: Chat, user: User
):
    """should be able to make a complete work session with a knowned tasks list"""

    username = get_user_name(user)
    chat_name = get_chat_name(chat)

    # --- Add tasks to db
    tasks = {
        "manger": {"poulet": 1, "pates": 2, "gateau": 3},
        "boire": {"eau": 1.5, "rhum": 7.5},
    }
    add_tasks(bot.db_path, chat_name, tasks)
    check.equal(get_project_tasks_dict(bot.db_path, chat_name), tasks)

    # --- \start
    update = mocker.MagicMock(effective_chat=chat, effective_user=user)
    context = mocker.MagicMock()
    bot.start(update, context)
    check.is_false(bot.wait_start_comment.get(username))
    check.equal(bot.current_tasks_dict.get(chat_name, {}).get(username), tasks)

    # --- Choose "manger" task in querry
    query = mocker.MagicMock(data="manger")
    update = mocker.MagicMock(
        effective_chat=chat, effective_user=user, callback_query=query
    )
    context = mocker.MagicMock()
    bot.queryHandler(update, context)
    check.is_false(bot.wait_start_comment.get(username))
    check.equal(
        bot.current_tasks_dict.get(chat_name, {}).get(username), tasks["manger"]
    )

    # --- Choose "poulet" task in querry
    query = mocker.MagicMock(data="poulet")
    update = mocker.MagicMock(
        effective_chat=chat, effective_user=user, callback_query=query
    )
    context = mocker.MagicMock()
    bot.queryHandler(update, context)
    check.is_true(bot.wait_start_comment.get(username))
    check.equal(bot.current_tasks_dict.get(chat_name, {}).get(username), "poulet")

    # --- start comment
    msg = mocker.MagicMock(text="test start")
    update = mocker.MagicMock(effective_chat=chat, effective_user=user, message=msg)
    context = mocker.MagicMock()
    bot.textHandler(update, context)
    check.is_false(bot.wait_start_comment.get(username))
    session = bot.workers_in_chats.get(chat_name, {}).get(username)
    check.is_not_none(session)
    if session:
        check.equal(session.task, "poulet")
        check.equal(session.start_comment, msg.text)

    # --- /stop
    update = mocker.MagicMock(effective_chat=chat, effective_user=user)
    context = mocker.MagicMock()
    bot.stop(update, context)
    check.is_true(bot.wait_stop_comment.get(username))

    # --- stop comment
    msg = mocker.MagicMock(text="test stop")
    update = mocker.MagicMock(effective_chat=chat, effective_user=user, message=msg)
    context = mocker.MagicMock()
    add_complete_session = mocker.patch("bot.handlers.stop.add_complete_session")
    bot.textHandler(update, context)
    check.is_false(bot.wait_stop_comment.get(username))
    check.is_true(add_complete_session.called)
    if add_complete_session.called:
        complete_session: CompleteSession = add_complete_session.call_args.args[-1]
        check.equal(complete_session.stop_comment, msg.text)
        check.equal(complete_session.session, session)
