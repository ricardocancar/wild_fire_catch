# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta
from nasa import earth
import sqlite3
from telegram import  (
    ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    ConversationHandler, Filters)
from credentials import NASA_API_KEY, TELEGRAM_TOKEN
MAX_CLOUD_SCORE = 0.5

LON = -120.70418
LAT = 38.32974

conn = sqlite3.connect('nasa_imagen_url.db', check_same_thread=False)
C = conn.cursor()

ANSWER1, END1 = range(2)


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

    
def read():
    """Get the data in cache from the sql data db"""
    C.execute('SELECT * FROM url_imagen')
    return C.fetchall()
    

def bisect(n, update, left, right):
    """
    Runs a bisection.

    - `row[5]` is the number of elements to be bisected
    - `mapper` is a callable that will transform an integer from "0" to "n"
      into a value that can be tested
    - if the previous message from the user is yes we set right to mid value
    - left the minimun date to be guessed 
    - right the maximun date to be guessed 
    """
    
    if n < 1:
        raise ValueError('Cannot bissect an empty array')

    
    mid = int((left + right) / 2)
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

    begin = (datetime.now() + timedelta(-365)).strftime('%Y-%m-%d')
    end = datetime.now().strftime('%Y-%m-%d')
    

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
    """Set the keybords that will be show to the user"""
    bol = False
    keyboard = [['Yes','No']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard = True,
                                       one_time_keyboard= bol)
    return reply_markup
    
def start(bot, update):
    """This send the first message to the user showing how to use the bot"""
    bot.sendMessage(chat_id = update.message.chat_id, text = 
                    (f'Hello {update.message.from_user.first_name}. '
                     'Thank you for participating. To interact '
                     'with me you can use these commands:'))
    bot.sendMessage(chat_id = update.message.chat_id, text = (
                   '/fire To start a new iteration\n'
                   '/cancel To cancel the iteration.\n'
                   '/help It gives a description of the operation of the bot.'
                   ' You can access these commands at any time '
                   'by pressing the slash /.' 
                   ))
    bot.sendMessage(chat_id = update.message.chat_id,
                    text = 'To start press /fire.')


def ayuda(bot,update):
    """Description of the bot operation."""
    update.message.reply_text(
      ('The bot will show the images to the user and the user will have '
       'to say if he sees. Forest wild fire damage on them. At the end, the '
       'bot will indicate the date he guessed for the events.'),
      reply_markup=ReplyKeyboardRemove())


def end(bot, update):
    """
    restaure the default values of the table and finish the conversation.
    """
    rows=read()
    index = rows[0][5]
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f"Found! First apparition = {rows[index][3]}"))
    bot.sendMessage(chat_id=update.message.chat_id,
                  text='Great! We\'re done, if you want to interact ' 
                       'again press '
                       '/fire ', reply_markup=ReplyKeyboardRemove())
    C.execute('Update url_imagen set ind = 0')
    conn.commit()
    C.execute('Update url_imagen set left = 0')
    conn.commit()
    C.execute('Update url_imagen set right = 0')
    conn.commit()
    return ConversationHandler.END


def fire(bot, update):
    """
    Start the conversation bettween human and the bot.
    bot: is the bot object allowing to send message to the user.
    update: update the status of the user conversation
    """
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f'Glad {update.message.from_user.first_name} '
                'that you want to continue.'))
    bot.sendMessage(chat_id = update.message.chat.id,
                    text=('Press "Yes" buton if you see a wild fire\n'
                          'Press "No" button if you don\'t see any fire.'),
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
    bot.send_photo(
        chat_id=update.message.chat.id,
        photo=rows[0][4])
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text = (f'Do you see wild fire damage? y/n'))
    C.execute(f'Update url_imagen set right = {n-1}')
    conn.commit
    bisect(n, update, 0, n-1)
    
    return ANSWER1


def answer(bot, update):
    rows=read()
    index = rows[0][5]
    print(index)
    url = read()[index][4]
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
    dp.add_handler(CommandHandler('help',ayuda))
    updater.start_polling()
    updater.idle()
    
    conn.close()