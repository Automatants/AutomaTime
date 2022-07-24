""" Module for handling the database requests. """

import argparse
from datetime import datetime
import os

import sqlite3
from typing import List, Tuple
import pandas as pd

from bot import CompleteSession
from bot.tasks import parse_tasks, read_tasks

TABLES = {
    "sessions": {
        "project": {"dtype": "TINYTEXT", "optional": False},
        "task": {"dtype": "TINYTEXT", "optional": True},
        "username": {"dtype": "TINYTEXT", "optional": False},
        "start": {"dtype": "DATETIME", "optional": False},
        "stop": {"dtype": "DATETIME", "optional": False},
        "duration": {"dtype": "FLOAT", "optional": False},
        "start_comment": {"dtype": "TEXT", "optional": True},
        "stop_comment": {"dtype": "TEXT", "optional": True},
    },
    "projects": {
        "project": {"dtype": "TINYTEXT", "optional": False},
        "tasks_dict": {"dtype": "TEXT", "optional": True},
    },
    "tasks": {
        "task": {"dtype": "TINYTEXT", "optional": False},
        "project": {"dtype": "TINYTEXT", "optional": False},
        "workload": {"dtype": "FLOAT", "optional": False},
    },
}


def insert_req(table: str):
    """Build a insert request based on table metadatas."""
    return f"""INSERT INTO {table}
            ({', '.join(TABLES[table].keys())})
            VALUES ({','.join('?'*len(TABLES[table]))});"""


SELECT_SUMMARY = """SELECT username, SUM(duration)
    FROM sessions
    WHERE project = ?
    GROUP BY username
    ORDER BY SUM(duration) DESC;"""

SELECT_PROJECTS_WITH_TASKS = """SELECT project
    FROM projects
    WHERE tasks_dict IS NOT NULL;"""

SELECT_TASKS_DICT = """SELECT tasks_dict FROM projects WHERE project = ?;"""

DELETE_TASKS_FROM_PROJECT = "DELETE FROM tasks WHERE project = ?;"
DELETE_PROJECT = "DELETE FROM projects WHERE project = ?;"


def connect(db_path: str) -> sqlite3.Connection:
    """Connect to the database.

    Args:
        db_path (str): Path to the database file.

    Returns:
        sqlite3.Connection: Connexion to the database.
    """
    return sqlite3.connect(db_path)


def get_columns_desc(columns: dict) -> str:
    """Get the description of all given columns.

    Args:
        columns (dict): Columns to get the descriptions from.

    Returns:
        str: Joined description of all elements from all columns.
    """
    desc_elements = []
    for column_name, column_data in columns.items():
        null_str = "" if column_data["optional"] else " NOT_NULL"
        desc_elements.append(f"{column_name} {column_data['dtype']}{null_str}")
    return ", ".join(desc_elements)


def create_database(db_path: str):
    """Create a database using tables metadata if they do not already exist.

    Args:
        db_path (str): Path to the database file.

    """
    with connect(db_path) as db:
        for table, columns in TABLES.items():
            create_req = f"""CREATE TABLE IF NOT EXISTS {table}
                (id INTEGER PRIMARY KEY, {get_columns_desc(columns)});"""
            db.execute(create_req)


def add_complete_session(db_path: str, project: str, complete_task: CompleteSession):
    """Add a complete session to the database.

    Args:
        db_path (str): Path to the database file.
        project (str): Name of the project.
        complete_task (CompleteSession): Complete work session data.
    """
    with connect(db_path) as db:
        db.execute(
            insert_req("sessions"),
            (
                project,
                complete_task.session.task,
                complete_task.session.author,
                complete_task.session.start.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.stop.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.duration.total_seconds(),
                complete_task.session.start_comment,
                complete_task.stop_comment,
            ),
        )


def add_tasks(db_path: str, project: str, tasks: dict):
    """Add tasks to the database.

    Args:
        db_path (str): Path to the database file.
        project (str): Name of the project.
        tasks (List[Tuple[str, float]]): List of tasks and their estimated times.
        tasks_dict (dict): Dictionary of the structure of tasks.
    """
    tasks_list = parse_tasks(tasks)
    with connect(db_path) as db:
        db.execute(DELETE_TASKS_FROM_PROJECT, (project,))
        db.execute(DELETE_PROJECT, (project,))
        db.execute(insert_req("projects"), (project, str(tasks)))
        for task_name, workload in tasks_list:
            db.execute(insert_req("tasks"), (task_name, project, workload))


def get_summary(db_path: str, project: str) -> pd.DataFrame:
    """Get the summary of time spent on tasks from the database.

    Args:
        db_path (str): Path to the database file.
        project (str): Name of the project.

    Returns:
        pd.DataFrame: Summary of time spent on tasks.
    """
    with connect(db_path) as db:
        summary_list = db.execute(SELECT_SUMMARY, (project,)).fetchall()
    return pd.DataFrame(data=summary_list, columns=("username", "duration"))


def get_project_tasks_dict(db_path: str, project: str) -> dict:
    """Get the structure of tasks from a project.

    Args:
        db_path (str): Path to the database file.
        project (str): Name of the project.

    Returns:
        dict: Structure of tasks of the given project.
    """
    with connect(db_path) as db:
        tasks_text = db.execute(SELECT_TASKS_DICT, (project,)).fetchall()
        if tasks_text:
            return read_tasks(tasks_text[0][0])
    return {}


def get_all(db_path: str, table) -> pd.DataFrame:
    """Get all data from the database as a Dataframe.

    Args:
        db_path (str): Path to the database file.
        table (_type_): Name of the project.

    Returns:
        pd.DataFrame: Dataframe of all data in the database.
    """
    with connect(db_path) as db:
        all_row = db.execute(f"SELECT * FROM {table}").fetchall()
    columns = ["id"] + list(TABLES[table].keys())
    return pd.DataFrame(data=all_row, columns=columns)


def dump_database_to_xlsx(db_path: str, dirpath: str):
    """Dump the database to a xlsx file.

    Args:
        db_path (str): Path to the database file.
        dirpath (str): Directory in which to dump the database.
    """
    os.makedirs(dirpath, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y-%m-%d_%Hh%M')}.xlsx"
    filepath = os.path.join(dirpath, filename)

    # pylint: disable=abstract-class-instantiated
    with pd.ExcelWriter(filepath) as writer:
        for table in TABLES:
            get_all(db_path, table).to_excel(writer, sheet_name=table)


def create_database_from_xlsx(xlsx_path: str, db_path: str):
    """Create a database from a xlsx dump file.

    Args:
        xlsx_path (str): Path to the xslx dump.
        db_path (str): Path to the created database.
    """
    xlsx_df = pd.read_excel(xlsx_path, list(TABLES.keys()), index_col=0)

    for table_name, table_ref in TABLES.items():
        table = xlsx_df[table_name]
        table = table.filter(table_ref.keys(), axis=1)
        with connect(db_path) as db:
            table.to_sql(table_name, db)


def build_parser() -> argparse.ArgumentParser:
    """Build a parser for database command line interface.

    Returns:
        ArgumentParser: Parser for the database CLI.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        "-p",
        help="Path to the database. Default to timerbot.db",
        default="timerbot.db",
    )
    parser.add_argument(
        "--dump-path",
        "-o",
        help="Path to the database dump. Default to database_dumps",
        default="database_dumps",
    )
    parser.add_argument(
        "--load-dump",
        "-l",
        help="Path to the database dump to load from. No loading if None given.",
        default=None,
    )
    return parser


def main():
    """Main database command line interface."""
    parser = build_parser()
    config = parser.parse_args()

    db_path = config.path
    if config.dump_path is not None and os.path.isfile(db_path):
        dump_database_to_xlsx(db_path, config.dump_path)

    if config.load_dump is not None:
        if os.path.isfile(db_path):
            os.remove(db_path)
        create_database_from_xlsx(config.load_dump, db_path)
        for table_name in TABLES:
            print(table_name)
            print(get_all(db_path, table_name))
            print()


if __name__ == "__main__":
    main()
