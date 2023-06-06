class MessageSendingError(Exception):
    """Сообщение не отправлено."""

    pass


class NoHomeworksKeyError(Exception):
    """В ответе от API отсутствует ключ homeworks."""

    pass


class StatusCodeNot200(Exception):
    """Статус код не 200."""

    pass


class JSONFormatError(Exception):
    """Ответ от API не в формате JSON."""

    pass


class NoHomeworksNameError(Exception):
    """В ответе от API отсутствует ключ homeworks_name."""

    pass


class UnknownStatusError(Exception):
    """Недокументированный статус домашней работы."""

    pass


class EmptyListException(Exception):
    """Если список на входу пустой."""

    pass


class APIAnswerError(Exception):
    """Сбой в получении ответа от API."""

    pass


class NoCurrentDateKeyError(Exception):
    """В ответе API тсутствует ключ current_date."""

    pass


class NoStatusKeyError(Exception):
    """В ответе от API отсутствует ключ status."""

    pass
