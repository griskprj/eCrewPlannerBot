from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import aiosqlite
import logging

from keyboards.inline import creator_notification_keyboard, event_actions_keyboard
from filters import AdminFilter

router = Router()


@router.callback_query(F.data.startswith('register:'))
async def register_on_event(callback: CallbackQuery, db: aiosqlite.Connection):
    event_id = int(callback.data.split(':')[1])
    user_id = callback.from_user.id
    username = callback.from_user.username
    user_mention = f"@{username}" if username else f"<a href='tg://user?id={user_id}'>Пользователь</a>"
    
    cursor = await db.execute(
        "SELECT 1 FROM registrations WHERE event_id = ? AND user_id = ?",
        (event_id, user_id)
    )
    if await cursor.fetchone():
        await callback.answer('Вы уже записаны на это мероприятие!', show_alert=True)
        return
    
    cursor = await db.execute(
        """SELECT e.title, e.creator_id, e.creator_username, e.group_id, g.group_title 
           FROM events e
           LEFT JOIN groups g ON e.group_id = g.group_id
           WHERE e.event_id = ?""",
        (event_id,)
    )
    event = await cursor.fetchone()
    if not event:
        await callback.answer('Мероприятие не найдено', show_alert=True)
        return
    
    await db.execute(
        "INSERT INTO registrations (event_id, user_id, username) VALUES (?, ?, ?)",
        (event_id, user_id, username)
    )
    await db.commit()
    
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"✅ Вы записаны на мероприятие \"{event['title']}\"",
            disable_notification=True
        )
    except Exception as e:
        logging.error(f"Не удалось отправить ЛС пользователю {user_id}: {e}")
    
    creator_id = event['creator_id']
    group_title = event['group_title'] or "группа"

    cursor = await db.execute(
        "SELECT COUNT(*) FROM registrations WHERE event_id = ?",
        (event_id,)
    )
    count = await cursor.fetchone()
    total_count = count[0]
    
    notification_text = (
        f"📝 Новая запись на мероприятие!\n\n"
        f"Мероприятие: {event['title']}\n"
        f"Группа: {group_title}\n"
        f"Участник: {user_mention}\n"
        f"Всего записей: {total_count}"
    )
    
    try:
        await callback.bot.send_message(
            chat_id=creator_id,
            text=notification_text,
            reply_markup=creator_notification_keyboard(event_id)
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление создателю {creator_id}: {e}")
    
    await callback.answer('Вы записаны!')


@router.callback_query(F.data.startswith('list_registrations:'), AdminFilter())
async def list_registrations(callback: CallbackQuery, db: aiosqlite.Connection):
    event_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        """SELECT e.title, e.status, e.group_id 
           FROM events e
           WHERE e.event_id = ?""",
        (event_id,)
    )
    event_row = await cursor.fetchone()
    if not event_row:
        await callback.answer('Мероприятие не найдено', show_alert=True)
        return

    event_title = event_row['title']
    event_status = event_row['status']
    group_id = event_row['group_id']

    cursor = await db.execute(
        "SELECT user_id, username FROM registrations WHERE event_id = ? ORDER BY registered_at",
        (event_id,)
    )
    users = await cursor.fetchall()

    if not users:
        await callback.answer('❌ На это мероприятие еще никто не записался', show_alert=True)
        return
    
    text = f"👥 Список записавшихся на \"{event_title}\":\n\n"

    for i, (user_id, username) in enumerate(users, 1):
        if username:
            text += f'{i}. @{username}\n'
        else:
            text += f"{i}. <a href='tg://user?id={user_id}'>Пользователь</a>\n"
    
    text += f"\nВсего: {len(users)}"

    keyboard = event_actions_keyboard(event_id, event_status, group_id)

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

    await callback.answer()
