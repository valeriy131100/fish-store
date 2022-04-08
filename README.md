# fish-store

[Telegram](https://telegram.org)-бот для продажи рыбы с CMS в [ElasticPath](https://euwest.cm.elasticpath.com/).

[Пример telegram-бота](https://t.me/DvmnFishStoreBot).

## Установка
Вам понадобится установленный Python 3.6+ и git.

Склонируйте репозиторий:
```bash
$ git clone https://github.com/valeriy131100/fish-store
```

Создайте в этой папке виртуальное окружение:
```bash
$ cd fish-store
$ python3 -m venv venv
```

Активируйте виртуальное окружение и установите зависимости:
```bash
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Использование

### Переменные среды
Заполните файл .env.example и переименуйте его в .env или иным образом задайте переменные среды:
* `TELEGRAM_TOKEN` - токен бота Telegram. Можно получить у [@BotFather](https://t.me/BotFather).
* `ELASTICSEARCH_CLIENT_ID` - id клиента магазина Elastic Search. Находится в разделе `Home`. Продукты для продажи необходимо добавлять в разделе `Catalog (legacy edition)`, а не `Products`.
* `ELASTICSEARCH_CLIENT_SECRET` - секретный ключ магазина Elastic Search. Находится также в разделе `Home`.

### Запуск
Находясь в директории fish-store исполните:
```bash
$ venv/bin/python telegram_bot.py
```

### Деплой на [Heroku](https://heroku.com/)

1. Зарегистрируйтесь и создайте приложение Heroku.
2. Соедините аккаунт Heroku и GitHub и выберите этот репозиторий.
3. Перейдите в раздел `Settings - Config Vars` и задайте те же переменные среды, что и для запуска локально.
4. Вернитесь к разделу `Deploy`, пролистните до самого конца и нажмите на кнопку `Deploy Branch`.
5. Перейдите в раздел `Resources` и запустите dyno для `telegram_bot`.