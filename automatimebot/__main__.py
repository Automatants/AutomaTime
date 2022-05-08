from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
import logging

from automatimebot.handlers import AutomatimeBot
from automatimebot.logging import init_logger

if __name__ == "__main__":
    init_logger(logging.INFO, __package__)

    updater = Updater("5328266305:AAGen99eby9tmWj62_EFzNhiNc73f_d6Jds")
    dispatcher = updater.dispatcher
    bot = AutomatimeBot(db_path="automatime.db")

    dispatcher.add_handler(CommandHandler("start", bot.start))
    dispatcher.add_handler(CommandHandler("stop", bot.stop))
    dispatcher.add_handler(CommandHandler("tasks", bot.load_task))
    dispatcher.add_handler(CommandHandler("data", bot.data_menu))
    dispatcher.add_handler(MessageHandler(Filters.text, bot.messageHandler))
    dispatcher.add_handler(CallbackQueryHandler(bot.queryHandler))
    dispatcher.add_handler(MessageHandler(Filters.command, bot.unknown))

    updater.start_polling()
    updater.idle()
