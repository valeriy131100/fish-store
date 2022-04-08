from textwrap import dedent

from redis import Redis
from telegram import (Update,
                      InlineKeyboardButton,
                      InlineKeyboardMarkup,
                      Message)
from telegram.ext import Filters, Updater, CallbackContext
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

import config
import elasticpath


def start(update: Update, _):
    products = elasticpath.get_products()

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products
    ]

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


def handle_menu_choose(update: Update, _):
    product = elasticpath.get_product(update.callback_query.data)

    image_id = product['relationships']['main_image']['data']['id']
    image_url = elasticpath.get_image(image_id)['link']['href']

    keyboard = [
        [
            InlineKeyboardButton(
                f'{weight}кг',
                callback_data=f'/buy {product["id"]} {weight}'
            )
            for weight in [1, 3, 5]
        ],
        [InlineKeyboardButton('Назад', callback_data='/back')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_photo(
        photo=image_url,
        caption=dedent(
            f"""
            {product['name']}
            
            {product['meta']['display_price']['with_tax']['formatted']} за кг
            {product['meta']['stock']['level']} кг доступно
            
            {product['description']}
            """
        ),
        reply_markup=reply_markup
    )

    update.callback_query.message.delete()

    return 'DESCRIPTION'


def handle_product_description(update: Update, redis: Redis):
    if update.callback_query.data == '/back':
        return start(update, redis)
    elif update.callback_query.data.startswith('/buy'):
        _, product_id, weight = update.callback_query.data.split()

        chat_id = update.callback_query.message.chat_id

        cart_id = redis.get(f'cart-{chat_id}')
        if cart_id is None:
            cart = elasticpath.create_cart(chat_id)
            cart_id = cart['id']
            redis.set(f'cart-{chat_id}', cart_id)

        elasticpath.add_product_to_cart(cart_id, product_id, int(weight))

        return 'DESCRIPTION'


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
        user_state = redis.get(f'state-{chat_id}').decode("utf-8")

    states_functions = {
        'START': start,
        'MENU_CHOOSE': handle_menu_choose,
        'DESCRIPTION': handle_product_description
    }

    state_handler = states_functions[user_state]

    next_state = state_handler(update, redis)
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

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()
    updater.idle()
