import sqlite3

from automatimebot import CompleteTask

DATABASE_PATH = "tasks.db"
TABLE_NAME = "tasks"

DATABASE_COLUMNS = {
    "project": {"dtype": "TINYTEXT", "optional": False},
    "username": {"dtype": "TINYTEXT", "optional": False},
    "start": {"dtype": "DATETIME", "optional": False},
    "stop": {"dtype": "DATETIME", "optional": False},
    "duration": {"dtype": "FLOAT", "optional": False},
    "comment": {"dtype": "TEXT", "optional": True},
}

INSERT = f"""INSERT INTO {TABLE_NAME}
             ({', '.join(DATABASE_COLUMNS.keys())})
             VALUES ({','.join('?'*len(DATABASE_COLUMNS))});"""

SELECT_SUMMARY = f"""SELECT username, SUM(duration)
    FROM {TABLE_NAME}
    WHERE project = ?
    GROUP BY username
    ORDER BY SUM(duration) DESC;"""


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def get_columns_desc():
    desc_elements = []
    for column_name, column_data in DATABASE_COLUMNS.items():
        null_str = "" if column_data["optional"] else " NOT_NULL"
        desc_elements.append(f"{column_name} {column_data['dtype']}{null_str}")
    return ", ".join(desc_elements)


def create_database():
    create_req = f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}
        (id INTEGER PRIMARY KEY, {get_columns_desc()});"""
    with connect() as db:
        db.execute(create_req)


def add_complete_task(project: str, complete_task: CompleteTask):
    with connect() as db:
        db.execute(
            INSERT,
            (
                project,
                complete_task.task.author,
                complete_task.task.start.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.stop.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.duration.total_seconds(),
                complete_task.task.comment,
            ),
        )


def get_summary(project: str):
    with connect() as db:
        summary_list = db.execute(SELECT_SUMMARY, (project,)).fetchall()
    return {username: total_duration for username, total_duration in summary_list}
