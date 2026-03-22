from aiogram.fsm.state import StatesGroup, State

class CreateEvent(StatesGroup):
    title = State()
    date = State()
    time = State()
    place = State()
    description = State()
    confirm = State()
