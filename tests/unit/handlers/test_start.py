""" Module for work session start handler. """

import pytest_check as check
from pytest_mock import MockerFixture

from bot.dataclasses import Session
from bot.handlers.start import session_comment_txt


class TestSessionComment:
    """session_comment_txt"""

    def test_session_comment_txt_notask(self, mocker: MockerFixture):
        """Should have comment without parentheses when no task is given."""
        session = Session(
            "author", start=mocker.Mock(), start_comment="session_comment"
        )
        expected_txt = "author started working on session_comment"
        txt = session_comment_txt(session)
        check.equal(txt, expected_txt)

    def test_session_comment_txt_nocomment(self, mocker: MockerFixture):
        """Should have comment without parentheses when no task is given."""
        session = Session("author", start=mocker.Mock(), task="task")
        expected_txt = "author started working on task"
        txt = session_comment_txt(session)
        check.equal(txt, expected_txt)

    def test_session_comment_txt_nothing(self, mocker: MockerFixture):
        """Should have comment without parentheses when no task is given."""
        session = Session("author", start=mocker.Mock())
        expected_txt = "author started working"
        txt = session_comment_txt(session)
        check.equal(txt, expected_txt)

    def test_session_comment_txt_both(self, mocker: MockerFixture):
        """Should have comment without parentheses when no task is given."""
        session = Session(
            "author",
            start=mocker.Mock(),
            task="task",
            start_comment="session_comment",
        )
        expected_txt = "author started working on task (session_comment)"
        txt = session_comment_txt(session)
        check.equal(txt, expected_txt)
