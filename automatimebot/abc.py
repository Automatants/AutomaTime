from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    author: str
    start: datetime
    comment: Optional[str] = field(default=None, repr=False)
    name: Optional[str] = field(default=None)


@dataclass
class CompleteTask:
    task: Task
    stop: datetime
    duration: timedelta = field(init=False)

    def __post_init__(self):
        self.duration = self.stop - self.task.start
