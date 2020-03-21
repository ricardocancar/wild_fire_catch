# -*- coding: utf-8 -*-
import os
from typing import NamedTuple, Any
from datetime import datetime
from nasa import earth
import requests
import sqlite3

from telegram import  (
    ReplyKeyboardMarkup, ReplyKeyboardRemove, User,
    Bot,InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    ConversationHandler, Filters,RegexHandler,CallbackQueryHandler)
from credentials import NASA_API_KEY, TELEGRAM_TOKEN
MAX_CLOUD_SCORE = 0.5

LON = -120.70418
LAT = 38.32974

conn = sqlite3.connect('nasa_imagen_url.db', check_same_thread=False)
C = conn.cursor()

ANSWER1, END1 = range(2)

with open('./url_imagen_cache.txt', 'r') as file:
    URLS_CACHE = file.read().split(';')

os.environ.setdefault(
    'NASA_API_KEY',
     NASA_API_KEY,
)

def mapper(n):
    """
    In that case there is no need to map (or rather, the mapping
    is done visually by the user)
    """

    return n

def wrong_keyword():
    key = input()
    key = key.lower()
    if key in ['y', 'n']:
        return key
    else:
        wrong_keyword()

class Shot(NamedTuple):
    """
    Represents a shot from Landsat. The asset is the output of the listing
    and the image contains details about the actual image.
    """

    date: Any
    url: Any
    

def read():
    C.execute('SELECT * FROM url_imagen')
    return C.fetchall()
    

def bisect(n, update, left, right):
    """
    Runs a bisection.

    - `row[5]` is the number of elements to be bisected
    - `mapper` is a callable that will transform an integer from "0" to "n"
      into a value that can be tested
    - `tester` returns true if the value is within the "right" range
    """
    
    if n < 1:
        raise ValueError('Cannot bissect an empty array')

    
    mid = int((left + right) / 2)
    print(f'biscet {mid}, left {left}, right {right}')
    C.execute(f'Update url_imagen set ind = {mid}')
    conn.commit()
    if update.message.text == 'Yes':
        C.execute(f'Update url_imagen set right = {mid}')
        conn.commit()
    else:
        C.execute(f'Update url_imagen set left = {mid}')
        conn.commit()


def get_shots():
    """
    Not all returned assets are useful (some have clouds). This function
    does some filtering in order to remove those useless assets and returns
    pre-computed shots which can be used more easily.
    """

    begin = '2015-01-01'
    end = '2016-01-01'
    # end = datetime.now().strftime('%Y-%m-%d')
    

    assets = earth.assets(lat=LAT, lon=LON, begin=begin, end=end)

    out = []
    sql = ''' INSERT INTO url_imagen(lat, lon, date,url,ind,left,right)
              VALUES(?,?,?,?,?,?,?)'''
    index = 0
    for asset in assets:
        img = asset.get_asset_image(cloud_score=True)
    
        if (img['cloud_score'] or 1.0) <= MAX_CLOUD_SCORE:
            row = (index, LAT, LON, img['date'], img['url'], 0,0,0)
            out.append(row)
            C.execute(sql, row[1:])
            conn.commit()
            index += 1
    return out
    
        
def keyboards():
    bol = False
    keyboard = [['Yes','No']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard = True,
                                       one_time_keyboard= bol)
    return reply_markup
    
def start(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text = 
                    (f'Hola {update.message.from_user.first_name}. '
                     'Gracias por participar. Para interactuar '
                     'conmigo puedes usar estos comandos:'))
    bot.sendMessage(chat_id = update.message.chat_id, text = (
                   '/fire Para comenzar una nueva encuesta\n'
                   '/cancel Cancelar el programa.\n'
                   '/ayuda Da una descripcion del funcionamiento del bot.\n'
                   'Puedes acceder a estos comandos en cualquier momento '
                   'pulsando la barra /.' 
                   ))
    bot.sendMessage(chat_id = update.message.chat_id,
                    text = 'Para comenzar pulsa /fire.')


def ayuda(bot,update):
    update.message.reply_text(
      ('El bot mostrará las imágenes al usuario y éste tendrá que decir si ve '
       'daños por incendio forestal en ellas. Al final, el bot indicará la '
       'fecha que adivinó para los eventos.'),
      reply_markup=ReplyKeyboardRemove())


def end(bot, update):
    rows=read()
    index = rows[0][5]
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f"Found! First apparition = {rows[index][3]}"))
    bot.sendMessage(chat_id=update.message.chat_id,
                  text='¡Genial! Hemos terminado, si quieres interactuar '
                       'otra vez pulsa'
                       '/fire ', reply_markup=ReplyKeyboardRemove())
    C.execute('Update url_imagen set ind = 0')
    conn.commit()
    C.execute('Update url_imagen set left = 0')
    conn.commit()
    C.execute('Update url_imagen set right = 0')
    conn.commit()
    return ConversationHandler.END


def fire(bot, update):
   
  
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f'Encantado {update.message.from_user.first_name} '
                'que quieras continuar.'))
    bot.sendMessage(chat_id = update.message.chat.id,
                    text='pulsa "yes" si ves un incendio\n'
                          'pulsa "no" para indicar lo contrario.',
                    reply_markup=keyboards())
    if read():
        rows = read()
    else:
        bot.sendMessage(
            chat_id=update.message.chat_id,
            text = (
                f'Searching for the imagens this could take several minutes'
                'sorry for the waiting'))
        rows = get_shots()
    n = len(rows)
    conn.commit()
        # bisector.index = n
    bot.send_photo(
        chat_id=update.message.chat.id,
        photo=rows[0][4])
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f'Do you see fire y/n'))
    C.execute(f'Update url_imagen set right = {n-1}')
    conn.commit
    bisect(n, update, 0, n-1)
    
    return ANSWER1


def answer(bot, update):
    rows=read()
    index = rows[0][5]
    print(index)
    url = read()[index][4]
        # bisector.index = n
    bot.send_photo(
        chat_id=update.message.chat.id,
        photo=url)
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f'Do you see fire y/n'))
    if rows[index][6] + 1 >= rows[index][7]:
        return END1
    bisect(rows[index][5], update, rows[index][6], rows[index][7])
    return ANSWER1


def cancel(bot,update):
  # user = update.message.from_user
  bot.sendMessage(chat_id=update.message.chat_id,
                  text = 'Hasta otra {user.first_name}'
                    , reply_markup =ReplyKeyboardRemove())
  return ConversationHandler.END

def error(bot, update, error):
    """Log Errors caused by Updates."""
    print('Update "%s" caused error "%s"', update, error)

if __name__=='__main__':
    # C.execute('DROP TABLE IF EXISTS url_imagen')
    C.execute('''CREATE TABLE IF NOT EXISTS url_imagen (
        id integer PRIMARY KEY, lat float,lon float, date text, url text,
        ind integer, left integer, right integer);''')
    # bisector = LandsatBisector(LON, LAT)
    # culprit = bisect(bisector.count)
    # bisector.index = culprit
    # print(f"Found! First apparition = {bisector.date}")
    token = TELEGRAM_TOKEN
    updater = Updater(token, use_context=False)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
      entry_points=[CommandHandler('fire', fire)],
      states={
      ANSWER1: [MessageHandler(Filters.regex('^(Yes|No)$'), answer)],
      END1: [MessageHandler(Filters.regex('^(Yes|No)$'), end)],
      },
      fallbacks=[CommandHandler('cancel', cancel)]
    )
    updater.dispatcher.add_error_handler(error)
    dp.add_handler(CommandHandler('start',start))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('ayuda',ayuda))
    updater.start_polling()
    updater.idle()
    
    conn.close()