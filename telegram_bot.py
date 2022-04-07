from redis import Redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackContext
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

import config


def start(update: Update):
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data='1'),
            InlineKeyboardButton("Option 2", callback_data='2')
        ],
        [
            InlineKeyboardButton("Option 3", callback_data='3')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Пожалуйста, выберите:',
        reply_markup=reply_markup
    )

    return 'MENU_CHOOSE'


def handle_menu_choose(update: Update):
    update.callback_query.message.edit_text(
        f'Вы выбрали: {update.callback_query.data}'
    )
    return 'MENU_CHOOSE'


def handle_users_reply(update: Update, context: CallbackContext):
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
        'MENU_CHOOSE': handle_menu_choose
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
