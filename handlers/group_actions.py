from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import aiosqlite

from handlers.create_event import CreateEvent
from handlers.send_message import SendMessage
from keyboards.inline import (
    cancel_keyboard, skip_cancel_keyboard, confirm_keyboard, 
    actions_keyboard,
    main_menu_keyboard
)
from filters import AdminFilter
from utils import format_date_preview

router = Router()



@router.callback_query(F.data.startswith('group:'), AdminFilter())
async def group_selected(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Select action for group """
    group_id = int(callback.data.split(':')[1])
    from keyboards.inline import actions_keyboard
    await callback.message.edit_text(
        'Выберите действие:',
        reply_markup=actions_keyboard(group_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith('create_event:'), AdminFilter())
async def start_create_event(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    """ Create event step 1 """
    group_id = int(callback.data.split(':')[1])
    await state.set_state(CreateEvent.title)
    await state.update_data(group_id=group_id)
    await callback.message.edit_text(
        "Введите название мероприятия (или нажмите 'Отмена')",
        reply_markup=cancel_keyboard(back_callback=f'group:{group_id}')
    )
    await callback.answer()


@router.message(CreateEvent.title, AdminFilter())
async def process_title(message: Message, state: FSMContext):
    """ Create event step 2 """
    title = message.text.strip()
    if not title:
        await message.answer('Название не может быть пустым. Попробуйте снова:')
        return
    
    data = await state.get_data()
    group_id = data.get('group_id')

    await state.update_data(title=title)
    await state.set_state(CreateEvent.date)
    await message.answer(
        "Введите дату (например, 13.03.2026) или нажмите 'Пропустить':",
        reply_markup=skip_cancel_keyboard(back_callback=f'group:{group_id}')
    )

@router.message(CreateEvent.date, AdminFilter())
async def process_date(message: Message, state: FSMContext):
    """ Create event step 3 """
    date = message.text.strip()
    data = await state.get_data()
    group_id = data.get('group_id')

    await state.update_data(date=date)
    await state.set_state(CreateEvent.time)
    await message.answer(
        "Введите время (например, 18:00 МСК):",
        reply_markup=cancel_keyboard(back_callback=f'group:{group_id}')
    )

@router.message(CreateEvent.time, AdminFilter())
async def process_time(message: Message, state: FSMContext):
    """ Create event step 4 """
    time = message.text.strip()
    data = await state.get_data()
    group_id = data.get('group_id')

    await state.update_data(time=time)
    await state.set_state(CreateEvent.place)
    await message.answer(
        "Введите место проведения (или нажмите 'Пропустить'):",
        reply_markup=skip_cancel_keyboard(back_callback=f'group:{group_id}')
    )

@router.message(CreateEvent.place, AdminFilter())
async def process_place(message: Message, state: FSMContext):
    """ Create event step 5 """
    place = message.text.strip()
    data = await state.get_data()
    group_id = data.get('group_id')
    
    await state.update_data(place=place)
    await state.set_state(CreateEvent.description)
    await message.answer(
        "Введите описание (или нажмите 'Пропустить'):",
        reply_markup=skip_cancel_keyboard(back_callback=f'group:{group_id}')
    )

@router.message(CreateEvent.description, AdminFilter())
async def process_description(message: Message, state: FSMContext):
    """ Create event step 6 """
    description = message.text.strip()
    await state.update_data(description=description)

    data = await state.get_data()
    group_id = data.get('group_id')
    preview = format_date_preview(data, message.from_user.username)

    await state.set_state(CreateEvent.confirm)
    await message.answer(
        preview,
        reply_markup=confirm_keyboard(
            confirm_data='confirm_event',
            cancel_data='cancel',
            back_callback=f'group:{group_id}'
        )
    )


@router.callback_query(F.data == 'cancel', AdminFilter())
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        'Действие отменено.',
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == 'skip', AdminFilter())
async def skip_step(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    group_id = data.get('group_id')

    if current_state == CreateEvent.date.state:
        await state.update_data(date=None)
        await state.set_state(CreateEvent.time)
        await callback.message.edit_text(
            'Введите время (например, 20:00 МСК):',
            reply_markup=cancel_keyboard(back_callback=f'group:{group_id}')
        )
    elif current_state == CreateEvent.place.state:
        await state.update_data(place=None)
        await state.set_state(CreateEvent.description)
        await callback.message.edit_text(
            'Введите описание:',
            reply_markup=skip_cancel_keyboard(back_callback=f'group:{group_id}')
        )
    elif current_state == CreateEvent.description.state:
        data = await state.get_data()
        data['description'] = None
        await state.update_data(description=None)
        preview = format_date_preview(data, callback.from_user.username)
        await state.set_state(CreateEvent.confirm)
        await callback.message.edit_text(
            preview,
            reply_markup=confirm_keyboard(
                confirm_data='confirm_event',
                cancel_data='cancel',
                back_callback=f'group:{group_id}'
            )
        )
    else:
        await callback.answer('Нельзя пропустить этот шаг', show_alert=True)
        return
    
    await callback.answer()


@router.callback_query(F.data == 'confirm_event', StateFilter(CreateEvent.confirm), AdminFilter())
async def confirm_event(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    data = await state.get_data()
    group_id = data.get('group_id')

    await db.execute(
        """
        INSERT INTO events
        (group_id, creator_id, creator_username, title, date, time, place, description, status)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data['group_id'],
            callback.from_user.id,
            callback.from_user.username,
            data['title'],
            data.get('date'),
            data.get('time'),
            data.get('place'),
            data.get('description'),
            'created'
        )
    )
    await db.commit()

    await state.clear()
    await callback.message.edit_text(
        "✅ Мероприятие успешно создано!",
        reply_markup=actions_keyboard(group_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith('send_message:'), AdminFilter())
async def start_send_message(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(':')[1])
    await state.set_state(SendMessage.text)
    await state.update_data(group_id=group_id)
    await callback.message.edit_text(
        'Введите сообщение для отправки в группу:',
        reply_markup=cancel_keyboard(back_callback=f'group:{group_id}')
    )
    await callback.answer()


@router.message(SendMessage.text, AdminFilter())
async def process_send_message(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer('Сообщение не может быть пустым. Введите текст:')
        return
    
    data = await state.get_data()
    group_id = data['group_id']

    await message.bot.send_message(chat_id=group_id, text=text)

    await state.clear()
    await message.answer(
        '✅ Сообщение отправлено в группу!',
        reply_markup=actions_keyboard(group_id)
    )
