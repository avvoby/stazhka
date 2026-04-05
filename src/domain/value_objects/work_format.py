from enum import StrEnum


class WorkFormat(StrEnum):
    OFFICE = "office"           # Офис
    REMOTE = "remote"           # Удалённо
    HYBRID = "hybrid"           # Гибрид
    UNSPECIFIED = "unspecified" # Не указан
