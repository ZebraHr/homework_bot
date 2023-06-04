import os
import sys
import time
import logging
import telegram
import requests
from http import HTTPStatus
from dotenv import load_dotenv
from exceptions import (NoHomeworksKeyError,
                        StatusCodeNot200,
                        JSONFormatError,
                        NoHomeworksNameError,
                        UnknownStatusError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    vars = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for var in vars:
        if var is None:
            logger.critical('Отсутствует переменная окружения!')
            return False
        return True


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug('Сообщение отправлено в чат')
    except telegram.TelegramError as error:
        logger.error(
            f'Сообщение не отправлено: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS, params=payload)
    except Exception as error:
        message = f'Сбой в получении ответа от API: {error}'
        logger.error(message)
    if homework_statuses.status_code != HTTPStatus.OK:
        message = (f'API {ENDPOINT} недоступен, '
                   f'код ошибки {homework_statuses.status_code}')
        logger.error(message)
        raise StatusCodeNot200(message)
    try:
        return homework_statuses.json()
    except Exception as error:
        raise JSONFormatError(error)


def check_response(response):
    """Проверяет валидность ответа API."""
    if type(response) is not dict:
        message = 'Ответ от API не является словарем!'
        logger.error(message)
        raise TypeError(message)
    try:
        homeworks = response['homeworks']
    except Exception:
        message = 'Отсутствует ключ homeworks!'
        logger.error(message)
        raise NoHomeworksKeyError(message)
    if type(homeworks) is not list:
        message = 'Значение ключа homeworks приходит не в виде списка!'
        logger.error(message)
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if type(homework) is not list:  # добавила это, потому что тесты утверждали
        homework = [homework]  # мне, что homework - словарь, а не список
    last_work = homework[0]  # и здесь выпадала ошибка KeyError: 0,
    status = last_work.get('status')  # бот при этом работал корректно,
    if 'homework_name' not in last_work:  # и на входе был list
        message = 'Отсутствует ключ homework_name!'
        logger.error(message)
        raise NoHomeworksNameError(message)
    homework_name = last_work.get('homework_name')
    if status not in HOMEWORK_VERDICTS:
        message = 'Отсутствует ключ status!'
        raise UnknownStatusError(message)
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    send_message(bot, 'Бот включен')
    old_message = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != old_message:
                send_message(bot, message)
                old_message = message
        finally:
            timestamp = response.get('current_date')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
