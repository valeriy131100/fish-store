from redis import Redis
from telegram import (Update,
                      InlineKeyboardButton,
                      InlineKeyboardMarkup)
from telegram.ext import Filters, Updater, CallbackContext
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

import config
import telegram_shop
from elasticpath import ElasticPath


def start(update: Update, _, elasticpath: ElasticPath):
    products = elasticpath.get_products()

    keyboard = [
        [
            InlineKeyboardButton(
                product['name'],
                callback_data=f'/description {product["id"]}'
            )
        ]
        for product in products
    ]

    keyboard.append(
        [InlineKeyboardButton('Корзина', callback_data='/cart')]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    message.reply_text(
        'Пожалуйста, выберите:',
        reply_markup=reply_markup
    )

    if update.callback_query:
        message.delete()

    return 'MENU_CHOOSE'


def handle_menu_choose(update: Update, redis: Redis, elasticpath: ElasticPath):
    callback = update.callback_query.data

    if callback.startswith('/description'):
        return telegram_shop.show_product_description(
            update, redis, elasticpath
        )
    elif callback == '/cart':
        return telegram_shop.show_cart(
            update, redis, elasticpath
        )


def handle_product_description(update: Update, redis: Redis,
                               elasticpath: ElasticPath):
    callback = update.callback_query.data

    if callback == '/back':
        return start(update, redis, elasticpath)
    elif callback.startswith('/buy'):
        _, product_id, weight = callback.split()

        chat_id = update.callback_query.message.chat_id

        cart_id = telegram_shop.get_or_create_cart_id(
            elasticpath, redis, chat_id
        )

        elasticpath.add_product_to_cart(cart_id, product_id, int(weight))

        update.callback_query.answer(text='Продукт добавлен в корзину!')

        return 'DESCRIPTION'
    elif callback == '/cart':
        return telegram_shop.show_cart(update, redis, elasticpath)


def handle_cart(update: Update, redis: Redis, elasticpath: ElasticPath):
    callback = update.callback_query.data

    if callback == '/menu':
        return start(update, redis, elasticpath)
    elif callback.startswith('/remove'):
        _, item_id = callback.split()

        chat_id = update.callback_query.message.chat_id
        cart_id = redis.get(f'cart-{chat_id}')

        if cart_id is None:
            raise ValueError

        elasticpath.remove_product_from_cart(cart_id, item_id)
        return telegram_shop.show_cart(update, redis, elasticpath)
    elif callback == '/pay':
        update.callback_query.message.reply_text(
            'Пришлите мне, пожалуйста, свою почту'
        )

        return 'WAITING_EMAIL'


def handle_email(update: Update, _, elasticpath: ElasticPath):
    email = update.message.text
    chat_id = update.message.chat_id

    elasticpath.create_customer(chat_id, email)

    update.message.reply_text(
        'Мы с вами свяжемся!'
    )

    return 'START'


def handle_users_reply(update: Update, context: CallbackContext):
    redis = context.bot_data['redis']
    elasticpath = context.bot_data['elasticpath']

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
        user_state = redis.get(f'state-{chat_id}').decode("utf-8")

    states_functions = {
        'START': start,
        'MENU_CHOOSE': handle_menu_choose,
        'DESCRIPTION': handle_product_description,
        'CART': handle_cart,
        'WAITING_EMAIL': handle_email
    }

    state_handler = states_functions[user_state]

    next_state = state_handler(update, redis, elasticpath)
    redis.set(f'state-{chat_id}', next_state)


if __name__ == '__main__':
    token = config.telegram_token
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['redis'] = Redis(
        host=config.redis_host,
        port=config.redis_port,
        password=config.redis_password
    )

    dispatcher.bot_data['elasticpath'] = ElasticPath(
        client_id=config.elasticpath_client_id,
        client_secret=config.elasticpath_client_secret
    )

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()
    updater.idle()
