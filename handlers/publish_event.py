from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import aiosqlite
import logging

from filters import AdminFilter
from keyboards.inline import events_list_keyboard, registration_keyboard, back_to_group_keyboard, main_menu_keyboard
from utils import format_date_preview

router = Router()


@router.message(Command('events'), AdminFilter())
async def cmd_events(message: Message, db: aiosqlite.Connection):
    cursor = await db.execute("SELECT group_id, group_title FROM groups")
    groups = await cursor.fetchall()
    
    if not groups:
        await message.answer(
            "Нет доступных групп",
            reply_markup=main_menu_keyboard()
        )
        return
    
    from keyboards.inline import groups_keyboard
    await message.answer(
        'Выберите группу для публикации мероприятия:',
        reply_markup=groups_keyboard(groups, action='publish')
    )


@router.callback_query(F.data.startswith('publish:'), AdminFilter())
async def select_group_for_publish(callback: CallbackQuery, db: aiosqlite.Connection):
    group_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        "SELECT event_id, title FROM events WHERE group_id = ? AND status = 'created'",
        (group_id,)
    )
    events = await cursor.fetchall()
    
    if not events:
        await callback.message.edit_text(
            f'Нет мероприятий для этой группы',
            reply_markup=back_to_group_keyboard(group_id)
        )
        return
    
    await callback.message.edit_text(
        'Выберите мероприятие для публикации:',
        reply_markup=events_list_keyboard(events, back_callback=f'group:{group_id}')
    )
    await callback.answer()


@router.callback_query(F.data.startswith('publish_event:'), AdminFilter())
async def publish_event(callback: CallbackQuery, db: aiosqlite.Connection):
    event_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        """SELECT event_id, group_id, creator_username, title, date, time, place, description
            FROM events WHERE event_id = ?""",
        (event_id,)
    )
    event = await cursor.fetchone()
    if not event:
        await callback.answer('Мероприятие не найдено', show_alert=True)
        return
    
    data = dict(event)
    text = format_date_preview(data, data.get('creator_username'))

    await callback.bot.send_message(
        chat_id=data['group_id'],
        text=text,
        reply_markup=registration_keyboard(event_id)
    )

    await db.execute(
        "UPDATE events SET status = 'published' WHERE event_id = ?",
        (event_id,)
    )
    await db.commit()

    await callback.message.edit_text(
        '✅ Мероприятие опубликовано!',
        reply_markup=back_to_group_keyboard(data['group_id'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith('remind_event:'), AdminFilter())
async def remind_event(callback: CallbackQuery, db: aiosqlite.Connection):
    event_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        """SELECT e.title, e.date, e.time, e.place, e.description, 
                  e.group_id, e.creator_username,
                  g.group_title
           FROM events e
           LEFT JOIN groups g ON e.group_id = g.group_id
           WHERE e.event_id = ?""",
        (event_id,)
    )
    event_row = await cursor.fetchone()
    
    if not event_row:
        await callback.answer('Мероприятие не найдено', show_alert=True)
        return
    
    event = dict(event_row)
    group_id = event['group_id']
    
    cursor = await db.execute(
        "SELECT username, user_id FROM registrations WHERE event_id = ?",
        (event_id,)
    )
    registrations = await cursor.fetchall()
    
    reminder_text = (
        f"🔔 <b>НАПОМИНАНИЕ О МЕРОПРИЯТИИ</b> 🔔\n\n"
        f"📌 <b>{event['title']}</b>\n"
    )
    
    if event.get('date'):
        reminder_text += f"📅 Дата: {event['date']}\n"
    if event.get('time'):
        reminder_text += f"⏰ Время: {event['time']}\n"
    if event.get('place'):
        reminder_text += f"📍 Место: {event['place']}\n"
    if event.get('description'):
        reminder_text += f"ℹ️ Описание: {event['description']}\n"
    
    if registrations:
        reminder_text += "\n<b>Записались:</b>\n"
        mentions = []
        for username, user_id in registrations:
            if username:
                mentions.append(f"@{username}")
            else:
                mentions.append(f"<a href='tg://user?id={user_id}'>Участник</a>")
        
        for i in range(0, len(mentions), 5):
            reminder_text += " • " + " • ".join(mentions[i:i+5]) + "\n"
        
        reminder_text += f"\nВсего: {len(registrations)} человек"
    else:
        reminder_text += "\n❌ Пока никто не записался"
    
    from keyboards.inline import registration_keyboard
    
    try:
        await callback.bot.send_message(
            chat_id=group_id,
            text=reminder_text,
            parse_mode="HTML",
            reply_markup=registration_keyboard(event_id)
        )
        await callback.answer('✅ Напоминание отправлено в группу!')
    except Exception as e:
        logging.error(f"Не удалось отправить напоминание в группу {group_id}: {e}")
        await callback.answer('❌ Ошибка при отправке в группу', show_alert=True)
