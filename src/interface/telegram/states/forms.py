from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    waiting_privacy = State()
    waiting_specialization = State()
    waiting_course = State()
    waiting_skills = State()
    waiting_companies = State()
    # Редактирование отдельных полей профиля
    editing_specialization = State()
    editing_course = State()
    editing_skills = State()
    editing_companies = State()


class AddVacancyStates(StatesGroup):
    waiting_input_type = State()
    waiting_manual_title = State()
    waiting_manual_company = State()
    waiting_url = State()
    waiting_hh_query = State()


class ManualApplicationStates(StatesGroup):
    waiting_title = State()
    waiting_company = State()
    waiting_stage = State()
    waiting_url = State()


class MockInterviewStates(StatesGroup):
    choosing_vacancy = State()
    in_progress = State()
    waiting_answer = State()


class QuickSearchStates(StatesGroup):
    editing_city = State()


class ProfileEditStates(StatesGroup):
    editing_gpa = State()
    editing_language = State()
    editing_experience = State()
    editing_salary = State()


class RoastBookingStates(StatesGroup):
    choosing_type    = State()
    choosing_slot    = State()
    uploading_resume = State()


class BroadcastStates(StatesGroup):
    choosing_audience = State()
    entering_filter   = State()
    entering_text     = State()
    adding_button_text = State()
    adding_button_url  = State()
    uploading_file    = State()
    confirming        = State()
