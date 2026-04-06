from pydantic_settings import BaseSettings


class CareerWeekSettings(BaseSettings):
    career_week_enabled: bool = False
    career_week_admin_ids: list[int] = [5645685337]
    google_sheets_id: str = ""
    google_service_account_json: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


career_week_settings = CareerWeekSettings()
