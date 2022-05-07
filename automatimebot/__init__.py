"""AutomaTime telegram bot"""

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Chat

from automatimebot.abc import Session, CompleteSession

# Globals
START = "Start"
START_CODE = "#START"
STOP = "Stop"
STOP_CODE = "#STOP"
ISWORKING = "Who is working ?"
SUMMARY = "Summary"
LOAD_TASKS = "Upload tasks"

workers_in_chats: Dict["Chat", Dict[str, "Session"]] = {}
current_tasks_dict: dict = None
wait_comment: str = None
wait_tasks: str = None
