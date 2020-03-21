# -*- coding: utf-8 -*-
import os
from typing import NamedTuple, Any
from datetime import datetime
from nasa import earth
import requests
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


END = range(1)

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


def tester(n, bisector):
        """
        Displays the current candidate to the user and asks them to
        check if they see wildfire damages.
        """
        print(bisector.image)
        # bisector.index = n
        # bot.send_photo(
        #     chat_id=update.message.chat.id,
        #     photo=bisector.image.url)
        key = input()
        key = key.lower('see fire y/n')
        if key in ['y', 'n']:
            return key
        else:
            wrong_keyword()
        #show
        return 'y'
def bisect(n, mapper, tester, bisector):
    """
    Runs a bisection.

    - `n` is the number of elements to be bisected
    - `mapper` is a callable that will transform an integer from "0" to "n"
      into a value that can be tested
    - `tester` returns true if the value is within the "right" range
    """

    if n < 1:
        raise ValueError('Cannot bissect an empty array')

    left = 0
    right = n - 1

    while left + 1 < right:
        mid = int((left + right) / 2)

        val = mapper(mid)

        if tester(val, bisector) == 'y':
            right = mid
        else:
            left = mid

    return mapper(right)


class Shot(NamedTuple):
    """
    Represents a shot from Landsat. The asset is the output of the listing
    and the image contains details about the actual image.
    """

    date: Any
    url: Any


def cache_crator(out):
    """since the Nasa API is a bit slow to get the imagen save the cache 
    of the url and the date since is all we need to do this ejercise"""
    urls = ';'.join([f'({shot.asset.date}, {shot.image.url})' for shot in out])
    with open('url_imagen_cache.txt', 'w') as f:
        f.write(urls)
    
class LandsatBisector:
    """
    Manages the different assets from landsat to facilitate the (bisect)ion
    algorithm.
    """

    def __init__(self, lon, lat):
        self.lon, self.lat = lon, lat
        self.shots = self.get_shots()
        self.index = 0
        self.image = self.shots[self.index].url
        
        print(f'First = {self.shots[0].date}')
        print(f'Last = {self.shots[-1].date}')
        print(f'Count = {len(self.shots)}')
    @property
    def count(self):
        return len(self.shots)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self.image = self.shots[index].url
        self._index = index
    
    @property
    def date(self):
        return self.shots[self.index].date
    
    def get_shots(self):
            """
            Not all returned assets are useful (some have clouds). This function
            does some filtering in order to remove those useless assets and returns
            pre-computed shots which can be used more easily.
            """
    
            begin = '2015-01-01'
            end = '2016-01-01'
            # end = datetime.now().strftime('%Y-%m-%d')
            
    
            assets = earth.assets(lat=self.lat, lon=self.lon, begin=begin, end=end)

            out = []
            
            for asset in assets:
                img = asset.get_asset_image(cloud_score=True)
            
                if (img['cloud_score'] or 1.0) <= MAX_CLOUD_SCORE:
                    out.append(Shot(img['date'], img['url']))

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
  
    bot.sendMessage(chat_id=update.message.chat_id,
                  text='¡Genial! Hemos terminado, si quieres interactuar '
                       'otra vez pulsa'
                       '/fire ', reply_markup=ReplyKeyboardRemove())

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

    bisector = LandsatBisector(LON, LAT)
    culprit = bisect(bisector.count, mapper, tester, bisector)
    bisector.index = culprit
    print(f"Found! First apparition = {bisector.date}")
    return END


def cancel(bot,update):
  # user = update.message.from_user
  bot.sendMessage(chat_id=update.message.chat_id,
                  text = 'Hasta otra {user.first_name}'
                    , reply_markup =ReplyKeyboardRemove())
  return ConversationHandler.END


if __name__=='__main__':
    token = TELEGRAM_TOKEN
    bisector = LandsatBisector(LON, LAT)
    culprit = bisect(bisector.count, mapper, tester, bisector)
    bisector.index = culprit
    print(f"Found! First apparition = {bisector.date}")
    # updater = Updater(token, use_context=False)
    # dp = updater.dispatcher
    # conv_handler = ConversationHandler(
    #   entry_points=[CommandHandler('fire', fire)],
    
    #   states={
    
     
    #   END: [MessageHandler(Filters.regex('^(yes|no)$'), end)],
    
    #   },
    
    #   fallbacks=[CommandHandler('cancel', cancel)]
    # )
    # dp.add_handler(CommandHandler('start',start))
    # dp.add_handler(conv_handler)
    # dp.add_handler(CommandHandler('ayuda',ayuda))
    # updater.start_polling()
    # updater.idle()
   