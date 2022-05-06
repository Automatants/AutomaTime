from datetime import datetime
from dataclasses import dataclass


@dataclass
class Task:
    author: str
    start: datetime
    comment: str
