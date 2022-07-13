import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)

from bot.handlers import Bot
from bot.logging import init_logger

if __name__ == "__main__":
    init_logger(logging.INFO, __package__)

    key_path = ".key"
    with open(key_path, "r", encoding="utf-8") as key_file:
        key = key_file.readline()

    updater = Updater(key)
    dispatcher = updater.dispatcher
    bot = Bot(db_path="timerbot.db")

    dispatcher.add_handler(CommandHandler("start", bot.start))
    dispatcher.add_handler(CommandHandler("stop", bot.stop))
    dispatcher.add_handler(CommandHandler("tasks", bot.load_task))
    dispatcher.add_handler(CommandHandler("data", bot.data_menu))
    dispatcher.add_handler(
        MessageHandler(
            Filters.text & (~Filters.forwarded) & (~Filters.update.edited_message),
            bot.textHandler,
        )
    )
    dispatcher.add_handler(
        MessageHandler(Filters.document.file_extension("yaml"), bot.yamlHandler)
    )
    dispatcher.add_handler(CallbackQueryHandler(bot.queryHandler))
    dispatcher.add_handler(MessageHandler(Filters.command, bot.unknown))

    updater.start_polling()
    updater.idle()
