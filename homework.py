import os
import sys
import time
import logging
from http import HTTPStatus

import telegram
import requests
from dotenv import load_dotenv

from exceptions import (NoHomeworksKeyError,
                        StatusCodeNot200,
                        JSONFormatError,
                        NoHomeworksNameError,
                        UnknownStatusError,
                        APIAnswerError,
                        NoCurrentDateKeyError,
                        NoStatusKeyError)

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
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        logger.debug('Начало отправки сообщения')
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
        logger.debug('Начало запроса к API')
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS, params=payload)
    except Exception as error:
        raise APIAnswerError(f'Сбой в получении ответа от API: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        raise StatusCodeNot200(f'API {ENDPOINT} недоступен, '
                               f'код ошибки {homework_statuses.status_code}')
    try:
        return homework_statuses.json()
    except Exception as error:
        raise JSONFormatError(error)


def check_response(response):
    """Проверяет валидность ответа API."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API не является словарем!')
    if 'homeworks' not in response:
        raise NoHomeworksKeyError('Отсутствует ключ homeworks!')
    if 'current_date' not in response:
        raise NoCurrentDateKeyError('Отсутствует ключ current_date!')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Значение ключа homeworks приходит не в виде списка!')
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        raise NoHomeworksNameError('Отсутствует ключ homework_name!')
    if 'status' not in homework:
        raise NoStatusKeyError('Отсутствует ключ status!')
    if homework_status not in HOMEWORK_VERDICTS:
        raise UnknownStatusError('Неожижанное значение ключа status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует переменная окружения!')
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
                message = parse_status(homework[0])
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
