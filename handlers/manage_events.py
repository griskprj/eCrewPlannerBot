from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite

from keyboards.inline import (
    events_management_keyboard, 
    event_actions_keyboard,
    confirm_keyboard,
    main_menu_keyboard,
    back_to_group_keyboard
)
from utils import format_date_preview
from filters import AdminFilter

router = Router()

@router.callback_query(F.data.startswith('manage_events:'), AdminFilter())
async def manage_events(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Show events list of group """
    group_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        """SELECT event_id, title, date, time, status,
                  (SELECT COUNT(*) FROM registrations WHERE event_id = events.event_id) as registrations_count
           FROM events 
           WHERE group_id = ? 
           ORDER BY 
               CASE status 
                   WHEN 'created' THEN 1
                   WHEN 'published' THEN 2
                   ELSE 3
               END,
               event_id DESC""",
        (group_id,)
    )
    events = await cursor.fetchall()
    
    if not events:
        await callback.message.edit_text(
            "📭 В этой группе пока нет мероприятий",
            reply_markup=back_to_group_keyboard(group_id)
        )
        await callback.answer()
        return
    
    text = f"📋 <b>Мероприятия группы:</b>\n\n"

    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=events_management_keyboard(events, group_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith('select_event:'), AdminFilter())
async def select_event(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Show event actions """
    event_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        """SELECT e.*, g.group_title,
                  (SELECT COUNT(*) FROM registrations WHERE event_id = e.event_id) as reg_count
           FROM events e
           LEFT JOIN groups g ON e.group_id = g.group_id
           WHERE e.event_id = ?""",
        (event_id,)
    )
    event = await cursor.fetchone()
    
    if not event:
        await callback.answer('Мероприятие не найдено', show_alert=True)
        return
    
    event_dict = dict(event)
    
    cursor = await db.execute(
        "SELECT username FROM registrations WHERE event_id = ?",
        (event_id,)
    )
    registrations = await cursor.fetchall()
    
    preview = format_date_preview(event_dict, event_dict.get('creator_username'))
    preview += f"\n\n👥 <b>Записалось:</b> {event_dict['reg_count']} человек"
    
    if registrations:
        mentions = []
        for (username,) in registrations[:5]:
            if username:
                mentions.append(f"@{username}")
        if mentions:
            preview += f"\n   • " + ", ".join(mentions)
        if len(registrations) > 5:
            preview += f"\n   • и еще {len(registrations) - 5}"
    
    await callback.message.edit_text(
        preview,
        parse_mode="HTML",
        reply_markup=event_actions_keyboard(
            event_id,
            event_dict['status'],
            event_dict['group_id']
        )
    )
    await callback.answer()

@router.callback_query(F.data.startswith('edit_event:'), AdminFilter())
async def edit_event(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Edit event """
    event_id = int(callback.data.split(':')[1])
    
    await callback.answer('🚧 Редактирование пока в разработке', show_alert=True)

@router.callback_query(F.data.startswith('cancel_event:'), AdminFilter())
async def cancel_event(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Cancel event """
    event_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        "SELECT status, title FROM events WHERE event_id = ?",
        (event_id,)
    )
    event = await cursor.fetchone()
    
    if not event:
        await callback.answer('Мероприятие не найдено', show_alert=True)
        return
    
    if event['status'] == 'cancelled':
        await callback.answer('Мероприятие уже отменено', show_alert=True)
        return
    
    await db.execute(
        "UPDATE events SET status = 'cancelled' WHERE event_id = ?",
        (event_id,)
    )
    await db.commit()
    
    try:
        await callback.bot.send_message(
            chat_id=event['group_id'],
            text=f"❌ Мероприятие **{event['title']}** отменено!",
            reply_markup=event_actions_keyboard(
                event_id
            )
        )
    except:
        pass
    
    await callback.answer('✅ Мероприятие отменено')
    
    await manage_events(callback, db)

@router.callback_query(F.data.startswith('finish_event:'), AdminFilter())
async def finish_event(callback: CallbackQuery, db: aiosqlite.Connection):
    """Завершает мероприятие"""
    event_id = int(callback.data.split(':')[1])
    
    await db.execute(
        "UPDATE events SET status = 'finished' WHERE event_id = ?",
        (event_id,)
    )
    await db.commit()
    
    await callback.answer('✅ Мероприятие завершено')
    await manage_events(callback, db)

@router.callback_query(F.data.startswith('delete_event:'), AdminFilter())
async def delete_event(callback: CallbackQuery, db: aiosqlite.Connection):
    """Удаляет мероприятие (с подтверждением)"""
    event_id = int(callback.data.split(':')[1])
    
    await callback.message.edit_text(
        "⚠️ <b>Точно удалить мероприятие?</b>\n"
        "Это действие нельзя отменить. Все записи будут удалены.",
        parse_mode="HTML",
        reply_markup=confirm_keyboard(
            confirm_data=f'confirm_delete_event:{event_id}',
            cancel_data=f'select_event:{event_id}'
        )
    )
    await callback.answer()

@router.callback_query(F.data.startswith('confirm_delete_event:'), AdminFilter())
async def confirm_delete_event(callback: CallbackQuery, db: aiosqlite.Connection):
    """Подтверждение удаления"""
    event_id = int(callback.data.split(':')[1])
    
    await db.execute("DELETE FROM registrations WHERE event_id = ?", (event_id,))
    await db.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
    await db.commit()
    
    await callback.answer('✅ Мероприятие удалено')
    
    await callback.message.edit_text(
        "Мероприятие удалено. Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data.startswith('export_registrations:'), AdminFilter())
async def export_registrations(callback: CallbackQuery, db: aiosqlite.Connection):
    """Экспорт списка записавшихся"""
    event_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        """SELECT r.user_id, r.username, r.registered_at, e.title
           FROM registrations r
           JOIN events e ON r.event_id = e.event_id
           WHERE r.event_id = ?
           ORDER BY r.registered_at""",
        (event_id,)
    )
    registrations = await cursor.fetchall()
    
    if not registrations:
        await callback.answer('Нет записавшихся', show_alert=True)
        return
    
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['User ID', 'Username', 'Registered At'])
    
    for reg in registrations:
        writer.writerow([reg['user_id'], reg['username'], reg['registered_at']])
    
    from aiogram.types import FSInputFile
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(output.getvalue())
        f.flush()
        
        await callback.message.answer_document(
            FSInputFile(f.name),
            caption=f"📊 Список записавшихся на {registrations[0]['title']}"
        )
    
    await callback.answer()