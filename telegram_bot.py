from textwrap import dedent

from redis import Redis
from telegram import (Update,
                      InlineKeyboardButton,
                      InlineKeyboardMarkup)
from telegram.ext import Filters, Updater, CallbackContext
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

import config
from elasticpath import ElasticPath


def get_or_create_cart_id(elasticpath: ElasticPath, redis: Redis, chat_id):
    cart_id = redis.get(f'cart-{chat_id}')
    if cart_id is None:
        cart = elasticpath.create_cart(chat_id)
        cart_id = cart['id']
        redis.set(f'cart-{chat_id}', cart_id)

    return cart_id


def show_cart(update: Update, redis: Redis, elasticpath: ElasticPath):
    chat_id = update.callback_query.message.chat_id
    cart_id = get_or_create_cart_id(elasticpath, redis, chat_id)

    cart = elasticpath.get_cart(cart_id)
    cart_items = elasticpath.get_cart_items(cart_id)

    cart_price = cart['meta']['display_price']['with_tax']['formatted']

    prepared_cart_items = []

    for cart_item in cart_items:
        name = cart_item['name']
        description = cart_item['description']
        prices = cart_item['meta']['display_price']['with_tax']
        full_price = prices['value']['formatted']
        unit_price = prices['unit']['formatted']
        quantity = cart_item['quantity']

        prepared_cart_items.append(
            f"""
            {name}
            {description}
            {unit_price} за кг
            {quantity} кг в корзине за {full_price}"""
        )

    formatted_cart_items = '\n'.join(prepared_cart_items)

    update.callback_query.message.reply_text(
        dedent(
            f"""
            {formatted_cart_items}
            
            Всего: {cart_price}"""
        )
    )

    update.callback_query.message.delete()

    return 'CART'


def show_product_description(update: Update, _, elasticpath: ElasticPath):
    _, product_id = update.callback_query.data.split()

    product = elasticpath.get_product(product_id)

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

    name = product['name']
    price = product['meta']['display_price']['with_tax']['formatted']
    amount = product['meta']['stock']['level']
    description = product['description']

    update.callback_query.message.reply_photo(
        photo=image_url,
        caption=dedent(
            f"""
            {name}

            {price} за кг
            {amount} кг доступно

            {description}"""
        ),
        reply_markup=reply_markup
    )

    update.callback_query.message.delete()

    return 'DESCRIPTION'


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
    if update.callback_query.data.startswith('/description'):
        return show_product_description(update, redis, elasticpath)
    elif update.callback_query.data == '/cart':
        return show_cart(update, redis, elasticpath)


def handle_product_description(update: Update, redis: Redis,
                               elasticpath: ElasticPath):
    if update.callback_query.data == '/back':
        return start(update, redis, elasticpath)
    elif update.callback_query.data.startswith('/buy'):
        _, product_id, weight = update.callback_query.data.split()

        chat_id = update.callback_query.message.chat_id

        cart_id = get_or_create_cart_id(elasticpath, redis, chat_id)

        elasticpath.add_product_to_cart(cart_id, product_id, int(weight))

        return 'DESCRIPTION'
    elif update.callback_query.data == '/cart':
        return show_cart(update, redis, elasticpath)


def handle_cart(update: Update, redis: Redis, elasticpath: ElasticPath):
    return 'CART'


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
        'CART': handle_cart
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
