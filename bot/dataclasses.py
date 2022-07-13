""" Module for dataclasses. """

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    """ Planned work session """
    author: str
    start: datetime
    start_comment: Optional[str] = field(default=None, repr=False)
    task: Optional[str] = field(default=None)


@dataclass
class CompleteSession:
    """ Complete work session """
    session: Session
    stop: datetime
    stop_comment: Optional[str] = field(default=None, repr=False)
    duration: timedelta = field(init=False)

    def __post_init__(self):
        self.duration = self.stop - self.session.start
