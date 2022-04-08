from datetime import datetime

import requests


class ElasticPath:
    API_BASE = 'https://api.moltin.com/v2'

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._expires = None

    def get_token(self):
        if self._token and (self._expires > datetime.now()):
            return self._token

        response = requests.post(
            'https://api.moltin.com/oauth/access_token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
        )
        response.raise_for_status()

        credentials = response.json()

        self._token = credentials['access_token']
        self._expires = datetime.fromtimestamp(credentials['expires'])

        return self._token

    def make_api_call(self, method, path, **kwargs):
        token = self.get_token()
        headers = {
            'Authorization': f'Bearer {token}'
        }

        response: requests.Response = method(
            f'{self.API_BASE}{path}',
            headers=headers,
            **kwargs
        )
        response.raise_for_status()

        api_answer = response.json()['data']

        return api_answer

    def get_products(self):
        return self.make_api_call(requests.get, '/products')

    def get_product(self, product_id):
        return self.make_api_call(requests.get, f'/products/{product_id}')

    def get_image(self, image_id):
        return self.make_api_call(
            requests.get,
            f'/files/{image_id}'
        )

    def get_cart(self, cart_id):
        return self.make_api_call(
            requests.get,
            f'/carts/{cart_id}'
        )

    def get_cart_items(self, cart_id):
        return self.make_api_call(
            requests.get,
            f'/carts/{cart_id}/items'
        )

    def create_cart(self, user_id):
        return self.make_api_call(
            requests.post,
            '/carts',
            json={
                'data': {
                    'name': f'Cart of user {user_id}',
                    'description': f'Cart of user {user_id} in FishStore'
                }
            }
        )

    def add_product_to_cart(self, cart_id, product_id, quantity):
        return self.make_api_call(
            requests.post,
            f'/carts/{cart_id}/items',
            json={
                'data': {
                    'id': product_id,
                    'type': 'cart_item',
                    'quantity': quantity
                }
            }
        )

    def remove_product_from_cart(self, cart_id, item_id):
        return self.make_api_call(
            requests.delete,
            f'/carts/{cart_id}/items/{item_id}'
        )
