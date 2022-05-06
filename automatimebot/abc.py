from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class Task:
    author: str
    start: datetime
    comment: str


@dataclass
class CompleteTask:
    task: Task
    stop: datetime
    duration: timedelta = field(init=False)

    def __post_init__(self):
        self.duration = self.stop - self.task.start
