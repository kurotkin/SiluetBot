#!/usr/bin/python3

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
import io
import emoji
import socket
from datetime import datetime

# Get the configuration data from the file
config = yaml.load(open('conf.yaml'))
jsonUrl = config['S7_1200']['jsonUrl']

# Basic Setup logging
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO,
                    filename = 'log.log')

logger = logging.getLogger(__name__)

# Emoji
emj_cake = emoji.emojize(":cake:", use_aliases = True)
emj_cityscape = emoji.emojize(":cityscape:", use_aliases = True)
emj_couch_and_lamp = emoji.emojize(":couch_and_lamp:", use_aliases = True)
emj_warning = emoji.emojize(":warning:", use_aliases = True)
emj_balc = emoji.emojize(":classical_building:", use_aliases = True)
emj_bellhop_bell= emoji.emojize(":bellhop_bell:", use_aliases = True)
emj_thermometer = emoji.emojize(":thermometer:", use_aliases = True)
emj_sun = emoji.emojize(":sun with face:", use_aliases = True)
emj_droplet = emoji.emojize(":droplet:", use_aliases = True)
emj_snowflake = emoji.emojize(":snowflake:", use_aliases = True)
emj_test = emoji.emojize(":clipboard:", use_aliases = True)
emj_back = emoji.emojize(":door:", use_aliases = True)
emj_exclamation_mark = emoji.emojize(":exclamation_mark:", use_aliases = True)
emj_press = emoji.emojize(":crystal_ball:", use_aliases = True)
emj_co2 = emoji.emojize(":fog:", use_aliases = True)
emj_settings = emoji.emojize(":gear:", use_aliases = True)

def main_keyboard():
    keyboard = [['/Балкон ' + emj_balc, '/Тест ' + emj_test], 
                ['/Улица ' + emj_cityscape, '/Комната ' + emj_couch_and_lamp]]
    return keyboard

def custom_keyboard():
    keyboard = [['/Основное_меню ' + emj_back, '/Тестовая_информация ' + emj_bellhop_bell]]
    return keyboard

# Adding %20 instead of " " for GET query
def addStr(Str):
    out = '%25'.join(Str.split("%"))
    return '%20'.join(out.split(" "))

# Yandex voice speech
def getSpeech(Str):
    name_mp3 = 'm' + datetime.now().strftime('%Y%m%d%H%M%S%f') + ".mp3"
    url_mp3 = "https://tts.voicetech.yandex.net/generate"
    url_mp3 = url_mp3 + "?text=" + addStr(Str)
    url_mp3 = url_mp3 + "&format=mp3"
    url_mp3 = url_mp3 + "&lang=ru-RU"
    url_mp3 = url_mp3 + "&speaker=oksana"
    url_mp3 = url_mp3 + "&emotion=good"
    url_mp3 = url_mp3 + "&key=" + config['YANDEX_KEY']
    mp3 = requests.get(url_mp3)
    out = open(name_mp3, "wb")
    out.write(mp3.content)
    out.close()
    return name_mp3

# Start Bot
def start(bot, update):
    update.message.reply_text("Привет, дорогой друг!\n Для получения информации набери /info")

def auth(bot, update):
    if config['telegtam']['password'] in update.message.text:
        if update.message.chat_id not in config['telegtam']['authenticated_users']:
            config['telegtam']['authenticated_users'].append(update.message.chat_id)
        reply_markup = ReplyKeyboardMarkup(main_keyboard())
        bot.sendMessage(
            chat_id = update.message.chat_id,
            text = "Вы авторизованы.",
            reply_markup = reply_markup
        )
        logger.info('Send message: {}'.format(update.message.chat_id))
        update.message.reply_text("Ваш id " + str(update.message.chat_id))
    else:
        bot.sendMessage(chat_id = update.message.chat_id, text = "Неправильный пароль.")

def getImage(url_img):
    name_img = "img.jpg"
    p = requests.get(url_img)
    out = open(name_img, "wb")
    out.write(p.content)
    out.close()
    return name_img

def help(bot, update):
    update.message.reply_text("Для получения информации набери /info <- или нажми")

def getVal (req, location, sign):
    parsed_r = json.loads(req.text)
    for obj in parsed_r:
        if obj['name'] == location:
            for cont in obj['content']:
                if cont['name'] == sign:
                    return cont['val']

def Out(bot, update):
    r = requests.get(jsonUrl)
    # Temperature
    t_text = " Температура на улице " + getVal(r, 'out', 'temp') + " градусов"
    update.message.reply_text(emj_thermometer + t_text)
    # Humidity
    d_text = " Влажность " + getVal(r, 'out', 'dump') + " %"
    update.message.reply_text(emj_droplet + d_text)
    # Pressure
    p_text = " Давление " + getVal(r, 'out', 'press') + " мм.рт.ст."
    update.message.reply_text(emj_press + p_text)
    # Brightness
    l_text = " Солнце светит на  " + getVal(r, 'out', 'light') + " лк"
    update.message.reply_text(l_text)
    # Street picture
    name_img = getImage(config['Cam1'])
    bot.sendPhoto(chat_id = update.message.chat_id, photo = open(name_img, 'rb'))
    os.remove(name_img)
    # Audio
    text_mp3 = t_text + d_text + p_text + l_text
    name_mp3 = getSpeech(text_mp3)
    logger.info(text_mp3)
    bot.sendAudio(chat_id = update.message.chat_id, audio = open(name_mp3, 'rb'))
    os.remove(name_mp3)


def info(bot, update):
    update.message.reply_text("Для получения дополнительной информации авторизируйся,\n" + \
                              "отправь /auth password.\n" + \
                              "Сейчас доступна только свободная информация.\n")
    Out(bot, update)

def echo(bot, update):
    info(bot, update)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

### Decorators ###
# Authentication
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

# Logging
def log(func):
    @functools.wraps(func)
    def wrapped(bot, update):
        logger.info('Received message: {}'.format(
            update.message.text if update.message else update.callback_query.data)
        )
        func(bot, update)
        logger.info('Response was sent')
    return wrapped


### Commands ###
@log
@auth_required
def openTestMenu(bot, update):
    reply_markup = ReplyKeyboardMarkup(custom_keyboard())
    bot.sendMessage(
        chat_id = update.message.chat_id,
        text = "Меню тестирования",
        reply_markup = reply_markup
    )

@log
@auth_required
def openMainMenu(bot, update):
    reply_markup = ReplyKeyboardMarkup(main_keyboard())
    bot.sendMessage(
        chat_id = update.message.chat_id,
        text = "Основное меню",
        reply_markup = reply_markup
    )

@log
@auth_required
def testTemp(bot, update):
    r = requests.get(jsonUrl)
    update.message.reply_text(r.text)

@log
@auth_required
def In(bot, update):
    r = requests.get(jsonUrl)
    # Temperature
    t_text = " Температура в комнате " + getVal(r, 'in', 'temp') + " градусов"
    update.message.reply_text(emj_thermometer + t_text)
    # Humidity
    d_text = " Влажность " + getVal(r, 'in', 'dump') + " %"
    update.message.reply_text(emj_droplet + d_text)
    # CO2
    co2_text = " Содержание углекислого газа " + getVal(r, 'in', 'CO2') + " ppm"
    update.message.reply_text(emj_co2 + co2_text)
    # Audio
    text_mp3 = t_text + d_text + co2_text
    name_mp3 = getSpeech(text_mp3)
    logger.info(text_mp3)
    bot.sendAudio(chat_id = update.message.chat_id, audio = open(name_mp3, 'rb'))
    os.remove(name_mp3)

@log
@auth_required
def Balc(bot, update):
    r = requests.get(jsonUrl)
    # Temperature
    t_text = " Температура на балконе " + getVal(r, 'balc', 'temp') + " градусов"
    update.message.reply_text(emj_thermometer + t_text)
    # Humidity
    d_text = " Влажность " + getVal(r, 'balc', 'dump') + " %"
    update.message.reply_text(emj_droplet + d_text)
    # Audio
    text_mp3 = t_text + d_text
    name_mp3 = getSpeech(text_mp3)
    logger.info(text_mp3)
    bot.sendAudio(chat_id = update.message.chat_id, audio = open(name_mp3, 'rb'))
    os.remove(name_mp3)

def narodmon_send(bot, job):
    DEVICE_MAC = config['DEVICE_MAC']
    SENSOR_ID_1 = DEVICE_MAC + '01'
    SENSOR_ID_2 = DEVICE_MAC + '02'
    SENSOR_ID_3 = DEVICE_MAC + '03'
    SENSOR_ID_4 = DEVICE_MAC + '04'
    r = requests.get(jsonUrl)
    sendMess = "#{}\n#{}#{}\n#{}#{}\n#{}#{}\n#{}#{}\n##".format(DEVICE_MAC, 
                                                SENSOR_ID_1, getVal(r, 'out', 'temp'), 
                                                SENSOR_ID_2, getVal(r, 'out', 'dump'),
                                                SENSOR_ID_3, getVal(r, 'out', 'press'),
                                                SENSOR_ID_4, getVal(r, 'out', 'light'))
    sock = socket.socket()
    try:
        sock.connect(('narodmon.ru', 8283))
        sock.send(sendMess.encode("utf-8"))
        data = sock.recv(1024)
        sock.close()
        logger.info("narodmon.ru: {}".format(data))
    except socket.error as e:
        logger.info('ERROR! Exception {}'.format(e))

def check_temperature(bot, job):
    """Periodic temperature test from sensors

        If the temperature is lower than the set minimum -
        Send notification to registered users
    """
    r = requests.get(jsonUrl)
    tempString = getVal(r, 'balc', 'temp')
    temp = float(tempString)

    if temp < 15.0:
        w_text = 'Температура ниже {} градусов: {}!'.format(15.0, temp)
        name_mp3 = getSpeech(w_text)
        for user_chat in config['telegtam']['authenticated_users']:
            bot.sendMessage(
                chat_id = user_chat,
                parse_mode = ParseMode.MARKDOWN,
                text = emj_warning + " *" + w_text + "*"
            )
            bot.sendAudio(chat_id = user_chat, audio = open(name_mp3, 'rb'))
        os.remove(name_mp3)

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

    dp.add_handler(CommandHandler('Тест', openTestMenu))
    dp.add_handler(CommandHandler('Основное_меню', openMainMenu))
    dp.add_handler(CommandHandler('Тестовая_информация', testTemp))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # Every 30 minutes
    job_queue.put(Job(check_temperature, 60*30), next_t = 60*6)

    # Every 5 minutes
    job_queue.put(Job(narodmon_send, 60*6), next_t = 60*6)

    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()