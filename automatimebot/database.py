import sqlite3

from automatimebot import CompleteTask

DATABASE_PATH = "tasks.db"
TABLE_NAME = "tasks"

INSERT = f"""INSERT INTO {TABLE_NAME}
             (project, username, duration, comment)
             VALUES (?,?,?,?);"""

SELECT = f"SELECT * FROM {TABLE_NAME} WHERE project = ?"


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def create_database():
    create_req = f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}
        (id INTEGER PRIMARY KEY,
        project        TINYTEXT    NOT NULL,
        username       TINYTEXT    NOT NULL,
        duration       TIMESTAMP   NOT NULL,
        comment        TEXT);"""
    with connect() as db:
        db.execute(create_req)


def add_complete_task(project: str, complete_task: CompleteTask):
    with connect() as db:
        db.execute(
            INSERT,
            (
                project,
                complete_task.task.author,
                str(complete_task.duration),
                complete_task.task.comment,
            ),
        )


def get_all_tasks(project: str):
    with connect() as db:
        return db.execute(SELECT, (project,)).fetchall()
