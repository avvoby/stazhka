from enum import StrEnum


class SearchStatus(StrEnum):
    ACTIVE = "active"           # Активно ищу стажировку
    PASSIVE = "passive"         # Рассматриваю предложения
    OFFER_RECEIVED = "offer_received"  # Получил оффер
