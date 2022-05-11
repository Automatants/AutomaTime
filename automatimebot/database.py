from datetime import datetime
import sqlite3
from typing import List, Tuple
import pandas as pd

from automatimebot import CompleteSession

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


def connect(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def get_columns_desc(columns: dict):
    desc_elements = []
    for column_name, column_data in columns.items():
        null_str = "" if column_data["optional"] else " NOT_NULL"
        desc_elements.append(f"{column_name} {column_data['dtype']}{null_str}")
    return ", ".join(desc_elements)


def create_database(db_path: str):
    with connect(db_path) as db:
        for table, columns in TABLES.items():
            create_req = f"""CREATE TABLE IF NOT EXISTS {table}
                (id INTEGER PRIMARY KEY, {get_columns_desc(columns)});"""
            db.execute(create_req)


def add_complete_session(db_path: str, project: str, complete_task: CompleteSession):
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


def add_tasks(
    db_path: str, project: str, tasks: List[Tuple[str, float]], tasks_dict: dict
):
    with connect(db_path) as db:
        db.execute(DELETE_TASKS_FROM_PROJECT, (project,))
        db.execute(DELETE_PROJECT, (project,))
        db.execute(insert_req("projects"), (project, str(tasks_dict)))
        for task_name, workload in tasks:
            db.execute(insert_req("tasks"), (task_name, project, workload))


def get_summary(db_path: str, project: str) -> pd.DataFrame:
    with connect(db_path) as db:
        summary_list = db.execute(SELECT_SUMMARY, (project,)).fetchall()
    return pd.DataFrame(data=summary_list, columns=("username", "duration"))


def get_project_tasks_dict(db_path: str, project: str) -> dict:
    with connect(db_path) as db:
        return db.execute(SELECT_TASKS_DICT, (project,)).fetchall()


def get_all(db_path: str, table) -> pd.DataFrame:
    with connect(db_path) as db:
        all_row = db.execute(f"SELECT * FROM {table}").fetchall()
    columns = ["id"] + list(TABLES[table].keys())
    return pd.DataFrame(data=all_row, columns=columns)


def dump_database_to_xlsx(db_path: str, filename: str):
    file_name = f"{filename}_{datetime.now().strftime('%Y-%m-%d_%Hh%M')}.xlsx"
    with pd.ExcelWriter(file_name) as writer:
        for table in TABLES:
            get_all(db_path, table).to_excel(writer, sheet_name=table)


def create_databale_from_xlsx(xlsx_path: str, db_path: str):
    xlsx_df = pd.read_excel(xlsx_path, list(TABLES.keys()), index_col=0)

    for table_name in TABLES:
        table = xlsx_df[table_name]

        # TODO: Split comments at promt to remove this
        if table_name == "sessions":

            def fusion_comment(row):
                has_start = isinstance(row["comment_start"], str)
                has_stop = isinstance(row["comment_stop"], str)
                if has_start and has_stop:
                    return f"{row['comment_start'].capitalize()}, {row['comment_stop'].lower()}"
                elif has_start:
                    return row["comment_start"].capitalize()
                elif has_stop:
                    return row["comment_stop"].capitalize()

            table["comment"] = table.apply(fusion_comment, axis=1)

        table = table.filter(TABLES[table_name].keys(), axis=1)
        with connect(db_path) as db:
            table.to_sql(table_name, db)


if __name__ == "__main__":
    db_path = "automatime.db"
    dump_database_to_xlsx(db_path, "database_dump")

    # create_databale_from_xlsx("database_dump_2022-05-08_20h42.xlsx", db_path)
    # for table_name in TABLES:
    #     print(table_name)
    #     print(get_all(db_path, table_name))
    #     print()
