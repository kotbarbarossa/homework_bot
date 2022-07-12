import requests
import os
from dotenv import load_dotenv
import time
import telegram
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
import logging
from random import randrange

load_dotenv()

logging.basicConfig(
    filename='practicum_hw_status_bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filemode='w'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

UPADTER = Updater(token=TELEGRAM_TOKEN)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def wake_up(update, context):
    """Отправка сообщения при подключении бота."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    username = update.message.chat.username
    context.bot.send_message(chat_id=chat.id,
                             text=f'Minor demon helper активирован >:-Е! '
                             f'{name}.{username} теперь ты подписан '
                             f'на демонические обновления!'
                             )
    logging.info(f'Пользователь {name}.{username} активировал бота')


def say_no(update, context):
    """Отправка рандомного ответа в чат."""
    chat = update.effective_chat
    random_answer = randrange(6)
    answers = {
        '0': 'Не прерывай чтение заклинания!',
        '1': 'Всё так же ни чего нового...',
        '2': 'Запмни: терпение и дисциплина',
        '3': 'Я знал что ты это спросишь',
        '4': 'Мы тут не для этого собрались',
        '5': 'Чем больше вопросов тем меньше ответов',
    }
    text = answers[str(random_answer)]
    context.bot.send_message(
        chat_id=chat.id,
        text=text
    )
    message = update.message.text
    name = update.message.chat.first_name
    username = update.message.chat.username
    logging.info(f'Пользователь {name}.{username} написал "{message}"')
    logging.info(f'Пользователь {name}.{username} получил ответ "{text}"')


def check(update, context):
    """Отправка сообщения о статусе последней работы."""
    chat = update.effective_chat
    thirty_days: int = 2592000
    current_timestamp = int(time.time()) - thirty_days
    response = get_api_answer(current_timestamp)
    homework = check_response(response)
    homework_status = homework[0]["status"]
    homework_name = homework[0]["homework_name"]
    message = (
        f'Текущий статус проверки работы "{homework_name}": {homework_status}'
    )
    context.bot.send_message(chat_id=chat.id, text=message)
    name = update.message.chat.first_name
    username = update.message.chat.username
    logging.info(f'Пользователь {name}.{username} запросил статус домашки')
    logging.info(f'Пользователь {name}.{username} получил ответ "{message}"')


def send_message(bot, message):
    """Отправка сообщения в чат."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logging.info(
        f'Пользователю {TELEGRAM_CHAT_ID} отправлено сообщение "{message}"'
    )


def get_api_answer(current_timestamp):
    """Функия получает ответ от Яндекс API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка подключения к Яндекс API {error}')
    status_code = response.status_code
    if status_code != 200:
        raise AssertionError('Сервер не отдал код 200')
    return response.json()


def check_response(response):
    """Функия проверяет ответ от Яндекс API."""
    homework = response["homeworks"]
    if type(response) is not dict:
        raise AssertionError('response не является словарем')
    if type(homework) is not list:
        raise AssertionError('Задания поступили не списком')
    return homework


def parse_status(homework):
    """Функия получает статус из ответа от Яндекс API."""
    homework_name = homework["homework_name"]
    homework_status = homework["status"]

    if "homework_name" not in homework:
        raise AssertionError('"homework_name" отсутствует в "homework"')
    if "status" not in homework:
        raise AssertionError('"status" отсутствует в "homework"')
    if homework_status not in HOMEWORK_STATUSES:
        raise AssertionError('Неизвестный науке статус работы')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функия проверяет наличие токенов."""
    flag = True
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if token is None:
            flag = False
    return flag


def main():
    """Основная логика работы бота."""
    UPADTER.dispatcher.add_handler(CommandHandler('start', wake_up))
    UPADTER.dispatcher.add_handler(CommandHandler('check', check))
    UPADTER.dispatcher.add_handler(MessageHandler(Filters.text, say_no))
    UPADTER.start_polling()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    # thirty_days: int = 2592000
    # current_timestamp = int(time.time()) - thirty_days

    check_tokens()

    i = 1
    a = 'tik'
    b = 'tak'

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
            current_timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            try:
                send_message(bot, message)
            except Exception as error:
                logging.exception(f'{error} Ошибка отправки в телеграм')

        print(a, i)
        i += 1
        (a, b) = (b, a)

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
