""" Module for in-chat data visualisation handler """

from datetime import timedelta
import os
from typing import Dict
import plotly
from telegram import Bot, Chat, Update
from telegram.ext import CallbackContext


from bot.dataclasses import Session
from bot.handlers.utils import (
    get_chat_name,
    pretty_time_delta,
)
from bot.database import get_all, get_summary

import pandas as pd
import plotly.express as px


def handle_is_working(
    update: Update,
    context: CallbackContext,
    workers_in_chats: Dict[Chat, Dict[str, Session]],
):
    call = update.callback_query
    chat = get_chat_name(update.effective_chat)
    date = call.message.date

    # If chat is monitored
    if chat in workers_in_chats:
        workers_in_chat = workers_in_chats[chat]
        if workers_in_chat:
            workers_infos = [
                f"{worker} since {pretty_time_delta((date - session.start).total_seconds())}"
                f" on {session.start_comment}"
                for worker, session in workers_in_chat.items()
            ]
            workers_str = "\n".join(workers_infos)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Currently working:\n{workers_str}",
            )
            call.answer()
        else:
            call.answer(text="No one is working at the moment.")

    # If chat is not even instanciated
    else:
        call.answer(text="No one ever worked here since I'm alive.")
    call.delete_message()


def handle_summary(update: Update, context: CallbackContext, db_path: str):
    chat = get_chat_name(update.effective_chat)
    summary = get_summary(db_path, chat)
    call = update.callback_query
    msg = "Summary of time spent:\n" + "\n".join(
        [f"{user}: {pretty_time_delta(duration)}" for user, duration in summary.values]
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    call.answer()
    call.delete_message()


def plot_gantt(sessions_df: pd.DataFrame) -> plotly.graph_objs.Figure:
    sessions_df.columns = [title.capitalize() for title in sessions_df.columns]
    sessions_df["Duration"] = sessions_df["Duration"].apply(
        lambda dt: str(timedelta(seconds=dt))
    )
    sessions_df["Task"] = sessions_df["Task"].apply(lambda task: task.capitalize())

    # create gantt/timeline chart.
    fig = px.timeline(
        sessions_df,
        x_start="Start",
        x_end="Stop",
        y="Task",
        color="Username",
        text="Duration",
        title="Project timeline",
        hover_data=[
            "Start",
            "Stop",
            "Start_comment",
            "Stop_comment",
            "Duration",
        ],
    )
    # shows charts in reversed, so last row of dataframe will show at bottom
    fig.update_yaxes(autorange="reversed")
    return fig


def send_gantt(bot: Bot, chat: Chat, db_path: str, tmp_path="tmp_gantt.html"):
    sessions_df = get_all(db_path, "sessions")
    fig = plot_gantt(sessions_df)
    fig.write_html(tmp_path)

    with open(tmp_path, "rb") as tmp_file:
        bot.send_document(chat_id=chat.id, document=tmp_file)

    os.remove(tmp_file)
