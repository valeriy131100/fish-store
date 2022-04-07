from environs import Env

env = Env()
env.read_env()

telegram_token = env.str('TELEGRAM_TOKEN')

redis_host = env.str('REDIS_HOST', 'localhost')
redis_port = env.int('REDIS_PORT', 6379)
redis_password = env.str('REDIS_PASSWORD', None)
