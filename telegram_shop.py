from textwrap import dedent

from redis import Redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

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

    keyboard = [
        [
            InlineKeyboardButton(
                f'Убрать из корзины {cart_item["name"]}',
                callback_data=f'/remove {cart_item["id"]}'
            )
        ]
        for cart_item in cart_items
    ]

    keyboard.append(
        [InlineKeyboardButton('Оплатить', callback_data='/pay')]
    )

    keyboard.append(
        [InlineKeyboardButton('В меню', callback_data='/menu')]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

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
        ),
        reply_markup=reply_markup
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
        [InlineKeyboardButton('Корзина', callback_data='/cart')],
        [InlineKeyboardButton('Назад', callback_data='/back')],
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