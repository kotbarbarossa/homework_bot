import requests
import os
from dotenv import load_dotenv
import time
import telegram
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
import logging
from random import randrange

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
# PRACTICUM_TOKEN = None
# TELEGRAM_TOKEN = None
# TELEGRAM_CHAT_ID = None
# TOKENS = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]

RETRY_TIME = 30
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def wake_up(update, context):
    """Отправка сообщения при подключении бота."""
    logging.info(
        f'Функция {wake_up.__name__} подключает бота '
        f'для пользователся {update.message.chat.username}')
    chat = update.effective_chat
    name = update.message.chat.first_name
    username = update.message.chat.username
    try:
        context.bot.send_message(
            chat_id=chat.id,
            text=f'Minor demon helper активирован >:-Е! '
            f'{name}.{username} теперь ты подписан '
            f'на демонические обновления!'
        )
    except Exception as error:
        logging.exception(f'{error} Ошибка отправки ответа в телеграм')
    logging.info(f'Пользователь {name}.{username} активировал бота')


def say_no(update, context):
    """Отправка рандомного ответа в чат."""
    logging.info(
        f'Функция {say_no.__name__} отправляет рандомный ответ в Телеграм')
    chat = update.effective_chat
    random_answer = randrange(6)
    answers = {
        '0': 'Не прерывай чтение заклинания!',
        '1': 'Всё так же ни чего нового...',
        '2': 'Запомни: терпение и дисциплина',
        '3': 'Я знал что ты это спросишь',
        '4': 'Мы тут не для этого собрались',
        '5': 'Чем больше вопросов тем меньше ответов',
    }
    text = answers[str(random_answer)]
    try:
        context.bot.send_message(
            chat_id=chat.id,
            text=text
        )
    except Exception as error:
        logging.exception(f'{error} Ошибка отправки ответа в телеграм')
    message = update.message.text
    name = update.message.chat.first_name
    username = update.message.chat.username
    logging.info(f'Пользователь {name}.{username} написал "{message}"')
    logging.info(f'Пользователь {name}.{username} получил ответ "{text}"')


def check(update, context):
    """Отправка сообщения о статусе последней работы."""
    logging.info(
        f'Функция {check.__name__} проверяет состояние последней домашки')
    chat = update.effective_chat
    thirty_days: int = 2592000
    current_timestamp = int(time.time()) - thirty_days
    response = get_api_answer(current_timestamp)
    homework = check_response(response)
    homework_status = homework[0]["status"]
    homework_name = homework[0]["homework_name"]

    if "homework_name" not in homework[0]:
        raise AssertionError('"homework_name" отсутствует в "homework"')
    if "status" not in homework[0]:
        raise AssertionError('"status" отсутствует в "homework"')
    if homework_status not in HOMEWORK_VERDICTS:
        raise AssertionError('Неизвестный науке статус работы')

    message = (
        f'Текущий статус проверки работы "{homework_name}": {homework_status}'
    )
    try:
        context.bot.send_message(chat_id=chat.id, text=message)
    except Exception as error:
        logging.exception(f'{error} Ошибка отправки ответа в телеграм')
    name = update.message.chat.first_name
    username = update.message.chat.username
    logging.info(f'Пользователь {name}.{username} запросил статус домашки')
    logging.info(f'Пользователь {name}.{username} получил ответ "{message}"')


def send_message(bot, message):
    """Отправка сообщения в чат."""
    logging.info(
        f'Функция {send_message.__name__} '
        f'пытается отправить сообщение "{message}" в Телеграм')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        raise AssertionError(f'{error} Ошибка отправки в телеграм')
    logging.info(
        f'Пользователю {TELEGRAM_CHAT_ID} отправлено сообщение "{message}"'
    )


def get_api_answer(current_timestamp):
    """Функия получает ответ от Яндекс API."""
    logging.info(
        f'Функция {get_api_answer.__name__} запрашивает ответ у "{ENDPOINT}"')
    timestamp = current_timestamp or int(time.time())
    REQUEST_PARAMS = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    try:
        response = requests.get(**REQUEST_PARAMS)
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка подключения к Яндекс API {error}')
    status_code = response.status_code
    if status_code != 200:
        raise AssertionError(
            f'Ошибка ответа с параметрами {REQUEST_PARAMS} '
            f'Текст ответа: status_code = '
            f'{response.status_code}, {response.text}')
    return response.json()


def check_response(response):
    """Функия проверяет ответ от Яндекс API."""
    logging.info(
        f'Функция {check_response.__name__} проверяет response "{ENDPOINT}"')
    homework = response["homeworks"]
    if type(response) is not dict:
        raise AssertionError('response не является словарем')
    if type(homework) is not list:
        raise AssertionError('Задания поступили не списком')
    if "homeworks" not in response:
        raise AssertionError('Ответ не содержит "homeworks"')
    return homework


def parse_status(homework):
    """Функия получает статус из ответа от Яндекс API."""
    logging.info(
        f'Функция {parse_status.__name__} числяет статус домашней работы')
    homework_name = homework["homework_name"]
    homework_status = homework["status"]

    if homework is None:
        raise AssertionError('Домашняя работа отсутствует')
    if "homework_name" not in homework:
        raise AssertionError('"homework_name" отсутствует в "homework"')
    if "status" not in homework:
        raise AssertionError('"status" отсутствует в "homework"')
    if homework_status not in HOMEWORK_VERDICTS:
        raise AssertionError('Неизвестный науке статус работы')

    verdict = HOMEWORK_VERDICTS[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функия проверяет наличие токенов."""
    logging.info(f'Функция {check_tokens.__name__} проверяет наличие токенов')
    TOKENS = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    flag = True
    for token in TOKENS:
        if token is None:
            flag = False
            logging.critical('Ошибка проверки токенов')
    return flag


def main():
    """Основная логика работы бота."""
    UPADTER = Updater(token=TELEGRAM_TOKEN)
    UPADTER.dispatcher.add_handler(CommandHandler('start', wake_up))
    UPADTER.dispatcher.add_handler(CommandHandler('check', check))
    UPADTER.dispatcher.add_handler(MessageHandler(Filters.text, say_no))
    UPADTER.start_polling()

    # current_timestamp = int(time.time())
    current_timestamp = 1

    prev_report = {}
    current_report = {}

    while check_tokens() is True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_report = {
                homework[0]["homework_name"]: homework[0]["status"]
            }
            if homework and current_report != prev_report:
                bot = telegram.Bot(token=TELEGRAM_TOKEN)
                message = parse_status(homework[0])
                send_message(bot, message)
                prev_report = current_report.copy()
            # current_timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            try:
                send_message(bot, message)
            except Exception as error:
                logging.exception(f'{error} Ошибка отправки в телеграм')

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        filename='practicum_hw_status_bot.log',
        format='%(asctime)s - %(name)s - %(levelname)s - LINE: %(lineno)d'
        ' - FUNCTION: %(funcName)s - MESSAGE: %(message)s',
        level=logging.INFO,
        filemode='w'
    )
    main()
