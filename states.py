from aiogram.dispatcher.filters.state import State, StatesGroup


# Registration
class Registration(StatesGroup):
    get_name_state = State()
    get_number_state = State()


# Test process
class TestProcess(StatesGroup):
    waiting_for_level = State()
    waiting_for_answer = State()

