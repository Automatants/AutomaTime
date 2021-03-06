""" Main entry point of the bot application. """

import os
import logging
from dotenv import load_dotenv

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)

from bot.handlers import BotHandler
from bot.logging import init_logger

if __name__ == "__main__":
    init_logger(logging.INFO, __package__)

    dotenv_path = ".env"
    if os.path.isfile(dotenv_path):
        load_dotenv(dotenv_path)

    key = os.environ.get("BOT_KEY")

    updater = Updater(key)
    dispatcher = updater.dispatcher
    bot = BotHandler(db_path="timerbot.db")

    handlers = (
        CommandHandler("start", bot.start),
        CommandHandler("stop", bot.stop),
        CommandHandler("tasks", bot.load_task),
        CommandHandler("data", bot.data_menu),
        MessageHandler(
            Filters.text & (~Filters.forwarded) & (~Filters.update.edited_message),
            bot.textHandler,
        ),
        MessageHandler(Filters.document.file_extension("yaml"), bot.yamlHandler),
        CallbackQueryHandler(bot.queryHandler),
        MessageHandler(Filters.command, bot.unknown),
    )

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()
