from aiogram.fsm.state import StatesGroup, State

class SendMessage(StatesGroup):
    text = State()
