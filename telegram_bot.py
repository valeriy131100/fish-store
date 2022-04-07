from redis import Redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

import config


def start(update):
    update.message.reply_text('Привет!')
    return 'ECHO'


def echo(update):
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return 'ECHO'


def handle_users_reply(update, context):
    redis = context.bot_data['redis']

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = redis.get(f'{chat_id}').decode("utf-8")

    states_functions = {
        'START': start,
        'ECHO': echo
    }

    state_handler = states_functions[user_state]

    next_state = state_handler(update)
    redis.set(chat_id, next_state)


if __name__ == '__main__':
    token = config.telegram_token
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['redis'] = Redis(
        host=config.redis_host,
        port=config.redis_port,
        password=config.redis_password
    )

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()
    updater.idle()
