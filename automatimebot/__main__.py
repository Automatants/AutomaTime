from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
import logging

from automatimebot.handler_functions import menu, messageHandler, queryHandler, unknown
from automatimebot.logging import init_logger
from automatimebot.database import create_database

if __name__ == "__main__":
    init_logger(logging.INFO, __package__)
    create_database()

    updater = Updater("5328266305:AAGen99eby9tmWj62_EFzNhiNc73f_d6Jds")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("automatime", menu))
    dispatcher.add_handler(MessageHandler(Filters.text, messageHandler))
    dispatcher.add_handler(CallbackQueryHandler(queryHandler))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
    updater.idle()
