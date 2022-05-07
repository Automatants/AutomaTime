import sqlite3
from typing import List, Tuple
import pandas as pd

from automatimebot import CompleteSession

DATABASE_PATH = "automatime.db"

TABLES = {
    "sessions": {
        "project": {"dtype": "TINYTEXT", "optional": False},
        "task": {"dtype": "TINYTEXT", "optional": True},
        "username": {"dtype": "TINYTEXT", "optional": False},
        "start": {"dtype": "DATETIME", "optional": False},
        "stop": {"dtype": "DATETIME", "optional": False},
        "duration": {"dtype": "FLOAT", "optional": False},
        "comment": {"dtype": "TEXT", "optional": True},
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
    return f"""INSERT INTO {table}
            ({', '.join(TABLES[table].keys())})
            VALUES ({','.join('?'*len(TABLES[table]))});"""


SELECT_SUMMARY = f"""SELECT username, SUM(duration)
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


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def get_columns_desc(columns: dict):
    desc_elements = []
    for column_name, column_data in columns.items():
        null_str = "" if column_data["optional"] else " NOT_NULL"
        desc_elements.append(f"{column_name} {column_data['dtype']}{null_str}")
    return ", ".join(desc_elements)


def create_database():
    with connect() as db:
        for table, columns in TABLES.items():
            create_req = f"""CREATE TABLE IF NOT EXISTS {table}
                (id INTEGER PRIMARY KEY, {get_columns_desc(columns)});"""
            db.execute(create_req)


def add_complete_session(project: str, complete_task: CompleteSession):
    with connect() as db:
        db.execute(
            insert_req("sessions"),
            (
                project,
                complete_task.session.task,
                complete_task.session.author,
                complete_task.session.start.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.stop.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.duration.total_seconds(),
                complete_task.session.comment,
            ),
        )


def add_tasks(project: str, tasks: List[Tuple[str, float]], tasks_dict: dict):
    with connect() as db:
        db.execute(DELETE_TASKS_FROM_PROJECT, (project,))
        db.execute(DELETE_PROJECT, (project,))
        db.execute(insert_req("projects"), (project, str(tasks_dict)))
        for task_name, workload in tasks:
            db.execute(insert_req("tasks"), (task_name, project, workload))


def get_summary(project: str) -> pd.DataFrame:
    with connect() as db:
        summary_list = db.execute(SELECT_SUMMARY, (project,)).fetchall()
    return pd.DataFrame(data=summary_list, columns=("username", "duration"))


def get_project_tasks_dict(project: str) -> dict:
    with connect() as db:
        return db.execute(SELECT_TASKS_DICT, (project,)).fetchall()


def get_all(table) -> pd.DataFrame:
    with connect() as db:
        all_row = db.execute(f"SELECT * FROM {table}").fetchall()
    columns = ["id"] + list(TABLES[table].keys())
    return pd.DataFrame(data=all_row, columns=columns)


if __name__ == "__main__":
    for table in TABLES:
        print(table)
        print(get_all(table))
        print()
