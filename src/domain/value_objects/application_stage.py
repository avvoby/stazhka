from enum import StrEnum


class ApplicationStage(StrEnum):
    SAVED = "saved"           # Сохранено
    APPLIED = "applied"       # Откликнулся
    SCREENING = "screening"   # Скрининг резюме
    TEST = "test"             # Тестовое задание
    INTERVIEW = "interview"   # Интервью
    OFFER = "offer"           # Получен оффер
    REJECTED = "rejected"     # Отказ

    @property
    def label(self) -> str:
        return {
            self.SAVED: "💾 Сохранено",
            self.APPLIED: "📤 Откликнулся",
            self.SCREENING: "🔍 Скрининг",
            self.TEST: "📝 Тестовое",
            self.INTERVIEW: "🎙 Интервью",
            self.OFFER: "🎉 Оффер",
            self.REJECTED: "❌ Отказ",
        }[self]
