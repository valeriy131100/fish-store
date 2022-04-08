from datetime import datetime

import requests

import config

_token = None
_expires = None


def get_token():
    global _token, _expires

    if _token and _expires > datetime.now():
        return _token

    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data={
            'client_id': config.elasticpath_client_id,
            'client_secret': config.elasticpath_client_secret,
            'grant_type': 'client_credentials'
        }
    )

    response.raise_for_status()

    credentials = response.json()

    _token = credentials['access_token']
    _expires = datetime.fromtimestamp(credentials['expires'])

    return _token


def get_products():
    token = get_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        'https://api.moltin.com/v2/products',
        headers=headers
    )
    response.raise_for_status()

    products = response.json()['data']

    return products


def get_product(product_id):
    token = get_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        f'https://api.moltin.com/v2/products/{product_id}', headers=headers
    )
    response.raise_for_status()

    product = response.json()['data']

    return product


def get_image(image_id):
    token = get_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        f'https://api.moltin.com/v2/files/{image_id}', headers=headers
    )
    response.raise_for_status()

    image = response.json()['data']

    return image


def create_cart(user_id):
    token = get_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(
        'https://api.moltin.com/v2/carts',
        headers=headers,
        json={
            'data': {
                'name': f'Cart of user {user_id}',
                'description': f'Cart of user {user_id} in FishStore'
            }
        },
    )
    response.raise_for_status()

    cart = response.json()['data']
    return cart


def add_product_to_cart(cart_id, product_id, quantity):
    token = get_token()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(
        f'https://api.moltin.com/v2/carts/{cart_id}/items',
        headers=headers,
        json={
            'data': {
                'id': product_id,
                'type': 'cart_item',
                'quantity': quantity
            }
        }
    )
    response.raise_for_status()

    cart = response.json()['data']
    return cart
