from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiosqlite
import logging

from filters import AdminFilter
from keyboards.inline import (
    groups_keyboard,
    back_to_group_keyboard,
    confirm_keyboard,
    main_menu_keyboard
)
from keyboards.inline import cancel_keyboard
from handlers.trainings.create_training import CreateTraining
from utils import format_training_preview

router = Router()

@router.message(Command('new_training'), AdminFilter())
async def cmd_new_training(message: Message, db: aiosqlite.Connection, state: FSMContext):
    """Start training creation process"""
    cursor = await db.execute("SELECT group_id, group_title FROM groups")
    groups = await cursor.fetchall()
    
    if not groups:
        await message.answer(
            "❌ Нет доступных групп.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await state.set_state(CreateTraining.group_id)
    await message.answer(
        "📋 <b>Создание нового тренинга</b>\n\n"
        "Выберите группу, в которой будет проводиться тренинг:",
        parse_mode="HTML",
        reply_markup=groups_keyboard(groups, action='create_training_group')
    )

@router.callback_query(F.data.startswith('create_training_group:'), AdminFilter())
async def process_training_group(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    """Process group selection"""
    group_id = int(callback.data.split(':')[1])
    print('GROUP ID IN CREATE TR', group_id)
    await state.update_data(group_id=group_id)
    
    # Get group title for later use
    cursor = await db.execute("SELECT group_title FROM groups WHERE group_id = ?", (group_id,))
    group = await cursor.fetchone()
    if group:
        await state.update_data(group_title=group['group_title'])
    
    await state.set_state(CreateTraining.recipient)
    await callback.message.edit_text(
        "👤 <b>Кто получает тренинг?</b>\n\n"
        "Отправьте username получателя (без @) или ID пользователя:",
        parse_mode="HTML",
        reply_markup=None
    )
    await callback.answer()

@router.message(CreateTraining.recipient, AdminFilter())
async def process_recipient(message: Message, state: FSMContext):
    """Process recipient selection"""
    recipient_input = message.text.strip()
    
    # Try to extract user_id or username
    if recipient_input.isdigit():
        recipient_id = int(recipient_input)
        recipient_username = ''
    else:
        recipient_id = None
        recipient_username = recipient_input.replace('@', '')
    
    await state.update_data(
        recipient_id=recipient_id,
        recipient_username=recipient_username,
        recipient_input=recipient_input
    )
    
    await state.set_state(CreateTraining.instructor)
    await message.answer(
        "👨‍🏫 <b>Кто проводит тренинг?</b>\n\n"
        "Отправьте username инструктора (без @) или ID пользователя:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.message(CreateTraining.instructor, AdminFilter())
async def process_instructor(message: Message, state: FSMContext):
    """Process instructor selection"""
    instructor_input = message.text.strip()
    
    if instructor_input.isdigit():
        instructor_id = int(instructor_input)
        instructor_username = None
    else:
        instructor_id = None
        instructor_username = instructor_input.replace('@', '')
    
    await state.update_data(
        instructor_id=instructor_id,
        instructor_username=instructor_username,
        instructor_input=instructor_input
    )
    
    await state.set_state(CreateTraining.title)
    await message.answer(
        "📝 <b>Название тренинга</b>\n\n"
        "Введите название тренинга:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.message(CreateTraining.title, AdminFilter())
async def process_title(message: Message, state: FSMContext):
    """Process training title"""
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTraining.date)
    await message.answer(
        "📅 <b>Дата тренинга</b>\n\n"
        "Введите дату в формате ДД.ММ.ГГГГ:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.message(CreateTraining.date, AdminFilter())
async def process_date(message: Message, state: FSMContext):
    """Process training date"""
    date = message.text.strip()
    if date.lower() == 'пропустить':
        date = None
    
    await state.update_data(date=date)
    await state.set_state(CreateTraining.time)
    await message.answer(
        "⏰ <b>Время тренинга</b>\n\n"
        "Введите время в формате ЧЧ:ММ:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.message(CreateTraining.time, AdminFilter())
async def process_time(message: Message, state: FSMContext):
    """Process training time"""
    time = message.text.strip()
    if time.lower() == 'пропустить':
        time = None
    
    await state.update_data(time=time)
    await state.set_state(CreateTraining.flight)
    await message.answer(
        "📍 <b>Рейс проведения</b>\n\n"
        "Введите рейс проведения:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.message(CreateTraining.flight, AdminFilter())
async def process_place(message: Message, state: FSMContext):
    """Process training flight"""
    flight = message.text.strip()
    if flight.lower() == 'пропустить':
        flight = None
    
    await state.update_data(flight=flight)
    await state.set_state(CreateTraining.description)
    await message.answer(
        "📖 <b>Описание тренинга</b>\n\n"
        "Введите описание:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.message(CreateTraining.description, AdminFilter())
async def process_description(message: Message, state: FSMContext, db: aiosqlite.Connection):
    """Process training description and show confirmation"""
    description = message.text.strip()
    if description.lower() == 'пропустить':
        description = None
    
    await state.update_data(description=description, creator_id=message.from_user.id, creator_username=message.from_user.username)
    
    # Get all data
    data = await state.get_data()
    
    # Show preview
    preview = format_training_preview(data)
    
    await state.set_state(CreateTraining.confirm)
    await message.answer(
        f"<b>📋 Предварительный просмотр тренинга:</b>\n\n{preview}\n\n"
        "✅ Подтвердите создание тренинга или ❌ отмените:",
        parse_mode="HTML",
        reply_markup=confirm_keyboard()
    )

@router.callback_query(F.data == 'confirm_create', CreateTraining.confirm)
async def confirm_training(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    """Save training to database"""
    data = await state.get_data()
    
    try:
        # Insert training into database
        cursor = await db.execute("""
            INSERT INTO trainings (
                group_id, creator_id, creator_username,
                recipient_id, recipient_username,
                instructor_id, instructor_username,
                title, date, time, place, description, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['group_id'],
            data['creator_id'],
            data['creator_username'],
            data.get('recipient_id'),
            data.get('recipient_username'),
            data.get('instructor_id'),
            data.get('instructor_username'),
            data['title'],
            data.get('date'),
            data.get('time'),
            data.get('flight'),
            data.get('description'),
            'created'
        ))
        
        await db.commit()
        training_id = cursor.lastrowid
        
        await callback.message.edit_text(
            f"✅ <b>Тренинг успешно создан!</b>\n\n"
            f"ID тренинга: {training_id}\n"
            f"Статус: создан (ожидает публикации)",
            parse_mode="HTML",
            reply_markup=back_to_group_keyboard(data['group_id'])
        )
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error creating training: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при создании тренинга. Попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data == 'cancel_create', CreateTraining.confirm)
async def cancel_training_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel training creation"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание тренинга отменено.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()
