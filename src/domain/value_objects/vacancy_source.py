from enum import StrEnum


class VacancySource(StrEnum):
    MANUAL = "manual"       # Добавлено вручную
    HH_RU = "hh_ru"         # С hh.ru
    URL = "url"             # Парсинг по ссылке
    TELEGRAM = "telegram"   # Из Telegram-канала
