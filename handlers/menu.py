from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import aiosqlite

from keyboards.inline import main_menu_keyboard, groups_keyboard
from filters import AdminFilter

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message, db: aiosqlite.Connection):
    """ Handler for /start cmd """
    await message.answer(
        "👋 Добро пожаловать в бот для управления мероприятиями!\n\n"
        "Я помогу вам создавать и управлять мероприятиями в группах.",
        reply_markup=main_menu_keyboard()
    )

@router.message(Command('menu'), AdminFilter())
@router.callback_query(F.data == 'main_menu')
async def show_main_menu(update: Message | CallbackQuery, db: aiosqlite.Connection):
    """ Show main menu """
    text = '🏠 Главное меню\n\nВыберите действие:'

    if isinstance(update, CallbackQuery):
        await update.message.edit_text(text, reply_markup=main_menu_keyboard())
        await update.answer()
    else:
        await update.answer(text, reply_markup=main_menu_keyboard())

@router.callback_query(F.data == 'my_groups', AdminFilter())
async def show_my_groups(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Show user groups """
    cursor = await db.execute(
        "SELECT group_id, group_title FROM groups ORDER BY group_title"
    )
    groups = await cursor.fetchall()

    if not groups:
        await callback.message.edit_text(
            "📭 У вас пока нет групп.\n\n"
            "Добавьте бота в группу и сделайте администратором, чтобы начать работу.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    text = "📋 Выберите группу:"
    await callback.message.edit_text(
        text,
        reply_markup=groups_keyboard(groups)
    )
    await callback.answer()

@router.callback_query(F.data == 'my_events', AdminFilter())
async def show_my_events(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Show all user events """
    cursor = await db.execute(
        """
        SELECT e.event_id, e.title, e.status, g.group_title,
            (SELECT COUNT(*) FROM registrations WHERE event_id = e.event_id) as reg_count
        FROM events e
        JOIN groups g ON e.group_id = g.group_id
        WHERE e.creator_id = ?
        ORDER BY e.event_id DESC
        LIMIT 10
        """,
        (callback.from_user.id,)
    )
    events = await cursor.fetchall()

    if not events:
        await callback.message.edit_text(
            "📭 У вас пока нет мероприятий.\n\n"
            "Выберите группу и создайте мероприятие!",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    text = "📊 Ваши последние мероприятия:\n\n"
    for event_id, title, status, group_title, reg_count in events:
        status_emoji = {
            'created': '📝',
            'published': '📢',
            'cancelled': '❌',
            'finished': '✅'
        }.get(status, '📌')
        
        text += f"{status_emoji} <b>{title}</b>\n"
        text += f"   Группа: {group_title}\n"
        text += f"   Записей: {reg_count}\n"
        text += f"   ID: <code>{event_id}</code>\n\n"

    from keyboards.inline import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for event_id, title, status, _, _ in events[:5]:
        builder.button(text=f"📌 {title[:20]}", callback_data=f'select_event:{event_id}')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=builder.as_markup()
    )
    await callback.answer()
