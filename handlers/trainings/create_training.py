from aiogram.fsm.state import StatesGroup, State

class CreateTraining(StatesGroup):
    group_id = State()  # Store group_id during creation
    recipient = State()  # Who receives training
    instructor = State()  # Who conducts training
    title = State()
    date = State()
    time = State()
    flight = State()
    description = State()
    confirm = State()  # Confirmation state