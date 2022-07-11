import requests
import os
from dotenv import load_dotenv
from pprint import pprint
from datetime import datetime, timedelta
import time
#from telegram import Bot, ReplyKeyboardMarkup
import telegram
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
import logging
from random import randrange

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

UPADTER = Updater(token=TELEGRAM_TOKEN)
bot = telegram.Bot(token=TELEGRAM_TOKEN)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    username = update.message.chat.username 
    context.bot.send_message(chat_id=chat.id, 
                             text=f'Minor demon helper активирован >:-Е! {name}.{username} теперь ты подписан на демонические обновления!',
                             )

def say_no(update, context):
    chat = update.effective_chat
    random_answer = randrange(6)
    answers = {
        '0':'Не прерывай чтение заклинания!',
        '1':'Всё так же ни чего нового...',
        '2':'Запмни: терпение и дисциплина',
        '3':'Я знал что ты это спросишь',
        '4':'Мы тут не для этого собрались',
        '5':'Чем больше вопросов тем меньше ответов',
    }
    context.bot.send_message(chat_id=chat.id,text=answers.get(str(random_answer)))

def check(update, context):
    chat = update.effective_chat
    # response = get_api_answer(1549962000)
    # homework = response.json().get("homeworks")
    # homework_status = homework[0].get("status")
    # homework_name = homework[0].get("homework_name")
    # context.bot.send_message(chat_id=chat.id,text=f'{Текущий статус проверки работы "{homework_name}": {homework_status}}')    
    thirty_days = 2592000
    current_timestamp = int(time.time()) - thirty_days    
    response = get_api_answer(current_timestamp)
    homework = check_response(response)
    message = parse_status(homework)  
    context.bot.send_message(chat_id=chat.id,text=f'{message}')

def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID,text=message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return response


def check_response(response):
    homeworks = response.json().get("homeworks")
    homework = homeworks[0]
    return homework
    ...


def parse_status(homework):
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    flag = True
    if PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
        flag = False
    return flag


def main():
    """Основная логика работы бота."""
    UPADTER.dispatcher.add_handler(CommandHandler('start', wake_up))
    UPADTER.dispatcher.add_handler(CommandHandler('check', check))
    UPADTER.dispatcher.add_handler(MessageHandler(Filters.text, say_no))
    UPADTER.start_polling()
    # UPADTER.idle() 

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    twelve_hours = 43200
    thirty_days = 2592000
    current_timestamp = int(time.time()) - thirty_days

    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)

            #current_timestamp = ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            # time.sleep(RETRY_TIME)
        # else:
        #     ...

        time.sleep(RETRY_TIME)
        


if __name__ == '__main__':
    main()
