import sqlite3

from automatimebot import CompleteTask

DATABASE_PATH = "tasks.db"
TABLE_NAME = "tasks"

INSERT = f"""INSERT INTO {TABLE_NAME}
             (project, username, duration, comment)
             VALUES (?,?,?,?);"""

SELECT_SUMMARY = f"""SELECT username, SUM(duration)
    FROM {TABLE_NAME}
    WHERE project = ?
    GROUP BY username
    ORDER BY SUM(duration) DESC;"""


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def create_database():
    create_req = f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}
        (id INTEGER PRIMARY KEY,
        project        TINYTEXT    NOT NULL,
        username       TINYTEXT    NOT NULL,
        duration       FLOAT       NOT NULL,
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
                complete_task.duration.total_seconds(),
                complete_task.task.comment,
            ),
        )


def get_summary(project: str):
    with connect() as db:
        summary_list = db.execute(SELECT_SUMMARY, (project,)).fetchall()
    return {username: total_duration for username, total_duration in summary_list}
