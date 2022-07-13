from typing import Tuple, Union
from telegram import File
import yaml


def read_tasks(file: Union[str, File]) -> Tuple[list, dict]:
    """Read the tasks structure from a yaml file or a string.

    Args:
        file (Union[str, File]): Yaml file or string to read tasks from.

    Returns:
        Tuple[list, dict]: List of tasks and their hierarchical structure as a dict.
    """
    if isinstance(file, File):
        with open(file.download(), "r", encoding="utf-8") as f:
            tasks_dicts = yaml.safe_load(f)
    else:
        tasks_dicts = yaml.safe_load(file)
    tasks = parse_tasks(tasks_dicts)
    return tasks, tasks_dicts


def parse_tasks(tasks_dicts: dict, tasks: list = None) -> list:
    """Parse all tasks from a structure of tasks as a dict.

    Args:
        tasks_dicts (dict): Structure of tasks as a dict.
        tasks (list, optional): Previous tasks. Defaults to None.

    Returns:
        list: List of tasks present in the tasks structure.
    """
    tasks = tasks if tasks is not None else []
    for task_name, value in tasks_dicts.items():
        if isinstance(value, dict):
            parse_tasks(value, tasks)
        else:
            tasks.append((task_name, value))
    return tasks


def print_tasks(d: dict, level=0):
    """Print a dictionary of tasks.

    Args:
        d (dict): Dict of tasks structures.
        level (int, optional): Depth of hierarchy being print. Defaults to 0.
    """
    for k, v in d.items():
        if isinstance(v, dict):
            print("  " * level + k + ":")
            print_tasks(v, level + 1)
        else:
            print("  " * level + f"{k}: {v}")
