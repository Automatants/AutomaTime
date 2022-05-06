"""AutomaTime telegram bot"""

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Chat

from automatimebot.abc import Task, CompleteTask

# Globals
START = "Start"
START_CODE = "#START"
STOP = "Stop"
STOP_CODE = "#STOP"
ISWORKING = "Who is working ?"
SUMMARY = "Summary"
LOAD_TASKS = "Upload tasks"

workers_in_chats: Dict["Chat", Dict[str, "Task"]] = {}
wait_comment: str = None
