#!/usr/bin/python3
# Библиотеки:
# http://docs.python-requests.org/en/master/user/quickstart/
# https://pypi.python.org/pypi/python-telegram-bot/#installing
# pip install PyYAML
# python -m pip install --upgrade pip
# pip install Pillow


from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job
from telegram import ReplyKeyboardMarkup, ParseMode
import logging
import os
import json
import logging
import functools

import yaml
import requests
import urllib.request
from PIL import Image
import io

# Получаем конфигруационные данные из файла
config = yaml.load(open('conf.yaml'))
ur = yaml.load(open('conf_s7-1200.yaml'))
jsonUrl = ur['S7_1200']['jsonUrl']

# Базовые настройка логирования
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text("Привет, дорогой друг!\n Для получения информации набери /info")

def auth(bot, update):
    if config['telegtam']['password'] in update.message.text:
        if update.message.chat_id not in config['telegtam']['authenticated_users']:
            config['telegtam']['authenticated_users'].append(update.message.chat_id)
        custom_keyboard = [
            ['/Балкон'],
            ['/Улица', '/Комната']
        ]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(
            chat_id = update.message.chat_id,
            text = "Вы авторизованы.",
            reply_markup = reply_markup
        )
        logger.info('Send message: {}'.format(update.message.chat_id))
        update.message.reply_text("Ваш id " + str(update.message.chat_id))
    else:
        bot.sendMessage(chat_id = update.message.chat_id, text = "Неправильный пароль.")

def help(bot, update):
    update.message.reply_text("Для получения информации набери /info <- или нажми")

def getImg (url):
    r = requests.get(url)
    with io.BytesIO(r.content) as f:
        with Image.open(f) as img:
            return img

def getVal (req, location, sign):
    parsed_r = json.loads(req.text)
    for obj in parsed_r:
        if obj['name'] == location:
            for cont in obj['content']:
                if cont['name'] == sign:
                    return cont['val']

def Out(bot, update):
    r = requests.get(jsonUrl)
    # Температура
    update.message.reply_text("Температура на улице " + getVal(r, 'out', 'temp') + " градусов")
    # Влажность
    update.message.reply_text("Влажность " + getVal(r, 'out', 'dump') + " %")
    # Давление
    update.message.reply_text("Давление " + getVal(r, 'out', 'press') + " мм.рт.ст.")
    # Яркость
    update.message.reply_text("Солнышко светит на  " + getVal(r, 'out', 'light') + " лк")

def info(bot, update):
    update.message.reply_text("Для получения дополнительной информации авторизируйся,\n" + \
                              "отправь /auth password.\n" + \
                                "Сейчас доступна только свободная информация.\n" + \
                                "Для получения информации набери /info <- или нажми\n")
    Out(bot, update)

def echo(bot, update):
    info(bot, update)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

### Декораторы ###
# Аутентификация
def auth_required(func):
    @functools.wraps(func)
    def wrapped(bot, update):
        if update.message.chat_id not in config['telegtam']['authenticated_users']:
            bot.sendMessage(
                chat_id = update.message.chat_id,
                text = "Вы неавторизованы.\nДля авторизации отправьте /auth password."
            )
        else:
            return func(bot, update)
    return wrapped

# Логирование
def log(func):
    @functools.wraps(func)
    def wrapped(bot, update):
        logger.info('Received message: {}'.format(
            update.message.text if update.message else update.callback_query.data)
        )
        func(bot, update)
        logger.info('Response was sent')
    return wrapped


### Команды ###
@log
@auth_required
def outdoor_light_on(bot, update):
    logger.info('outdoor_light_on')
    bot.sendMessage(chat_id = update.message.chat_id, text = 'outdoor_light_on')

@log
@auth_required
def outdoor_light_off(bot, update):
    logger.info('outdoor_light_off')
    bot.sendMessage(chat_id = update.message.chat_id, text = 'outdoor_light_off')


@log
@auth_required
def heaters_on(bot, update):
    logger.info('heaters_on')
    bot.sendMessage(chat_id = update.message.chat_id, text = 'heaters_on')


@log
@auth_required
def heaters_off(bot, update):
    logger.info('outdoor_light_off')
    bot.sendMessage(chat_id = update.message.chat_id, text = 'outdoor_light_off')

@log
@auth_required
def In(bot, update):
    r = requests.get(jsonUrl)
    # Температура
    update.message.reply_text("Температура в комнате " + getVal(r, 'in', 'temp') + " градусов")
    # Влажность
    update.message.reply_text("Влажность " + getVal(r, 'in', 'dump') + " %")
    # CO2
    update.message.reply_text("Содержание углекислого газа " + getVal(r, 'in', 'CO2') + " ppm")

@log
@auth_required
def Balc(bot, update):
    r = requests.get(jsonUrl)
    # Температура
    update.message.reply_text("Температура на балконе " + getVal(r, 'balc', 'temp') + " градусов")
    # Влажность
    update.message.reply_text("Влажность " + getVal(r, 'balc', 'dump') + " %")


def check_temperature(bot, job):
    """Переодическая проверка температуры с датчиков

    Eсли температура ниже, чем установленный минимум -
    посылаем уведомление зарегистрированным пользователям
    """
    r = requests.get(jsonUrl)
    # Температура
    tempString = getVal(r, 'balc', 'temp')
    temp = float(tempString)

    if temp < 15.0:
        for user_chat in config['telegtam']['authenticated_users']:
            bot.sendMessage(
                chat_id = user_chat,
                parse_mode = ParseMode.MARKDOWN,
                text='*Температура ниже {} градусов: {}!*'.format(
                    15.0,
                    temp
                )
            )


def main():
    updater = Updater(config['telegtam']['TOKEN'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    job_queue = updater.job_queue

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("info", info))

    dp.add_handler(CommandHandler('Улица', Out))
    dp.add_handler(CommandHandler('Комната', In))
    dp.add_handler(CommandHandler('Балкон', Balc))

    dp.add_handler(CommandHandler('auth', auth))

    dp.add_handler(CommandHandler('Включить_обогреватели', heaters_on))
    dp.add_handler(CommandHandler('Выключить_обогреватели', heaters_off))
    dp.add_handler(CommandHandler('Включить_прожектор', outdoor_light_on))
    dp.add_handler(CommandHandler('Выключить_прожектор', outdoor_light_off))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    job_queue.put(Job(check_temperature, 60*30), next_t=60*6)

    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()