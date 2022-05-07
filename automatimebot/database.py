import sqlite3
import pandas as pd

from automatimebot import CompleteTask

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


def insert_req(table: str, columns: dict):
    return f"""INSERT INTO {table}
            ({', '.join(columns.keys())})
            VALUES ({','.join('?'*len(columns))});"""


SELECT_SUMMARY = f"""SELECT username, SUM(duration)
    FROM sessions
    WHERE project = ?
    GROUP BY username
    ORDER BY SUM(duration) DESC;"""


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


def add_complete_task(project: str, complete_task: CompleteTask):
    with connect() as db:
        db.execute(
            insert_req("sessions", TABLES["sessions"]),
            (
                project,
                complete_task.task.name,
                complete_task.task.author,
                complete_task.task.start.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.stop.strftime("%Y-%m-%d %H:%M:%S"),
                complete_task.duration.total_seconds(),
                complete_task.task.comment,
            ),
        )


def get_summary(project: str) -> pd.DataFrame:
    with connect() as db:
        summary_list = db.execute(SELECT_SUMMARY, (project,)).fetchall()
    return pd.DataFrame(data=summary_list, columns=("username", "duration"))


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
