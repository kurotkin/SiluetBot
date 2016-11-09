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
            ['/Включить_обогреватели', '/Выключить_обогреватели'],
            ['/Включить_прожектор', '/Выключить_прожектор'],
            ['/Улица', '/Комната']
        ]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(
            chat_id = update.message.chat_id,
            text = "Вы авторизованы.",
            reply_markup = reply_markup
        )
    else:
        bot.sendMessage(chat_id = update.message.chat_id, text = "Неправильный пароль.")

def help(bot, update):
    update.message.reply_text("Для получения информации набери /info <- или нажми")

def getImg (url):
    r = requests.get(url)
    with io.BytesIO(r.content) as f:
        return f

def tempOut(bot, update):
    # Температура
    t_url = ur['S7_1200']['url'] + ur['S7_1200']['Out']['Temp']
    t = requests.get(t_url)
    update.message.reply_text("Температура на улице " + t.text + " градусов")
    # Влажность
    d_url = ur['S7_1200']['url'] + ur['S7_1200']['Out']['Dump']
    d = requests.get(d_url)
    update.message.reply_text("Влажность " + d.text + " %")
    # Яркость
    l_url = ur['S7_1200']['url'] + ur['S7_1200']['Out']['Light']
    l = requests.get(l_url)
    update.message.reply_text("Солнышко светит на  " + l.text + " непонятных единиц.")

    pic = getImg(ur['S7_1200']['url_img'])
    #bot.sendPhoto(chat_id = update.message.chat_id, photo = pic)
    bot.sendPhoto(chat_id = update.message.chat_id, photo = pic)

def info(bot, update):
    update.message.reply_text("Для получения дополнительной информации авторизируйся,\n" + \
                              "отправь /auth password.\n" + \
                                "Сейчас доступна только свободная информация.\n")
    tempOut(bot, update)

def echo(bot, update):
    #update.message.reply_text(update.message.text)
    update.message.reply_text("Для получения информации набери /info <- или нажми\n" + \
                                "Для авторизации отправь /auth password.")

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
def tempIn(bot, update):
    # Температура
    t_url = ur['S7_1200']['url'] + ur['S7_1200']['In']['Temp']
    t = requests.get(t_url)
    update.message.reply_text("Температура в комнате" + t.text + " градусов")
    # Влажность
    d_url = ur['S7_1200']['url'] + ur['S7_1200']['In']['Dump']
    d = requests.get(d_url)
    update.message.reply_text("Влажность " + d.text + " %")
    # CO2
    co2_url = ur['S7_1200']['url'] + ur['S7_1200']['In']['CO2']
    co2 = requests.get(co2_url)
    update.message.reply_text(im_sun + " Солнышко светит на  " + l.text + " непонятных единиц.")
    #bot.sendPhoto(chat_id = update.message.chat_id, photo = ur['S7_1200']['url_img'])

def main():
    updater = Updater(config['telegtam']['TOKEN'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("info", info))

    dp.add_handler(CommandHandler('Улица', tempOut))
    dp.add_handler(CommandHandler('Комната', tempIn))

    dp.add_handler(CommandHandler('auth', auth))

    dp.add_handler(CommandHandler('Включить_обогреватели', heaters_on))
    dp.add_handler(CommandHandler('Выключить_обогреватели', heaters_off))
    dp.add_handler(CommandHandler('Включить_прожектор', outdoor_light_on))
    dp.add_handler(CommandHandler('Выключить_прожектор', outdoor_light_off))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))



    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()