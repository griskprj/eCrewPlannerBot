from aiogram import Router, F
from aiogram.types import CallbackQuery
from dotenv import load_dotenv
import aiosqlite
import logging
import os

from keyboards.inline import (
    trainings_management_keyboard,
    training_actions_keyboard,
    confirm_keyboard,
    main_menu_keyboard,
    back_to_group_keyboard
)
from utils import format_training_preview
from filters import AdminFilter

load_dotenv()

router = Router()
TRAININGS_TOPIC_ID = os.getenv('TRAININGS_TOPIC_ID')

@router.callback_query(F.data.startswith('manage_trainings:'), AdminFilter())
async def manage_trainings(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Show trainings list of group """
    group_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        """
        SELECT training_id, title, status
        FROM trainings
        WHERE group_id = ?
        ORDER BY 
            CASE status
                WHEN 'created' THEN 1
                WHEN 'active' THEN 2
                WHEN 'pass' THEN 3
                WHEN 'cancelled' THEN 4
                ELSE 5
            END,
            training_id DESC
        """,
        (group_id,)
    )
    trainings = await cursor.fetchall()

    if not trainings:
        await callback.message.edit_text(
            "📭 В этой группе пока нет тренингов",
            reply_markup=back_to_group_keyboard(group_id)
        )
        await callback.answer()
        return

    text = f"🎓 <b>Тренинги группы:</b>\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=trainings_management_keyboard(trainings, group_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith('select_training:'), AdminFilter())
async def select_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Show training actions """
    training_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        """
        SELECT t.*, g.group_title
        FROM trainings t
        LEFT JOIN groups g ON t.group_id = g.group_id
        WHERE t.training_id = ?
        """,
        (training_id,)
    )
    training = await cursor.fetchone()

    if not training:
        await callback.answer('Тренинг не найден', show_alert=True)
        return
    
    training_dict = dict(training)
    preview = format_training_preview(training_dict)

    await callback.message.edit_text(
        preview,
        parse_mode='HTML',
        reply_markup=training_actions_keyboard(
            training_id,
            training_dict['status'],
            training_dict['group_id']
        )
    )
    await callback.answer()

@router.callback_query(F.data.startswith('edit_training:'), AdminFilter())
async def edit_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Edit training """
    training_id = int(callback.data.split(':')[1])
    
    await callback.answer('🚧 Редактирование пока в разработке', show_alert=True)

@router.callback_query(F.data.startswith('cancel_training:'), AdminFilter())
async def cancel_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Cancel training """
    training_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        "SELECT status, title, recipient_id, recipient_username FROM trainings WHERE training_id = ?",
        (training_id,)
    )
    training = await cursor.fetchone()
    
    if not training:
        await callback.answer('Тренинг не найден', show_alert=True)
        return
    
    if training['status'] == 'cancelled':
        await callback.answer('Тренинг уже отменен', show_alert=True)
        return
    
    await db.execute(
        "UPDATE trainings SET status = 'cancelled' WHERE training_id = ?",
        (training_id,)
    )
    await db.commit()

    # Try to notify recipient
    try:
        if training['recipient_id']:
            await callback.bot.send_message(
                chat_id=training['recipient_id'],
                text=f"❌ Тренинг **{training['title']}** отменен!"
            )
        elif training['recipient_username']:
            await callback.bot.send_message(
                chat_id=f"@{training['recipient_username']}",
                text=f"❌ Тренинг **{training['title']}** отменен!"
            )
    except Exception as e:
        logging.error(f"Failed to notify recipient: {e}")
    
    await callback.answer('✅ Тренинг отменен')
    
    # Refresh the view
    await manage_trainings(callback, db)

@router.callback_query(F.data.startswith('pass_training:'), AdminFilter())
async def pass_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Mark training as passed """
    training_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        "SELECT group_id, status, title, recipient_id, recipient_username FROM trainings WHERE training_id = ?",
        (training_id,)
    )
    training = await cursor.fetchone()
    
    if training['status'] == 'pass':
        await callback.answer('Тренинг уже сдан', show_alert=True)
        return
    
    await db.execute(
        "UPDATE trainings SET status = 'pass' WHERE training_id = ?",
        (training_id,)
    )
    await db.commit()

    # Try to notify recipient
    try:
        await callback.bot.send_message(
            chat_id=training['group_id'],
            message_thread_id=TRAININGS_TOPIC_ID,
            parse_mode='HTML',
            text=f"✅ Тренинг <b>{training['title']}</b> завершен. Статус - <b>ЗАЧЕТ!</b> \n\n Экзаменуемый <b>{'@' + training['recipient_username'] if training['recipient_username'] else ''}</b>, Вам в личные сообщения будет направлен отчет с результатами тренинга."
        )
    except Exception as e:
        logging.error(f"Failed to notify recipient: {e}")
    
    await callback.answer('✅ Тренинг завершен. Статус - зачет')

@router.callback_query(F.data.startswith('not_pass_training:'), AdminFilter())
async def not_pass_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Mark training as not passed """
    training_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        "SELECT group_id, status, title, recipient_id, recipient_username FROM trainings WHERE training_id = ?",
        (training_id,)
    )
    training = await cursor.fetchone()
    
    if training['status'] == 'not_pass':
        await callback.answer('Статус уже не сдан', show_alert=True)
        return
    
    await db.execute(
        "UPDATE trainings SET status = 'not_pass' WHERE training_id = ?",
        (training_id,)
    )
    await db.commit()

    # Try to notify recipient
    try:
        await callback.bot.send_message(
            chat_id=training['group_id'],
            message_thread_id=TRAININGS_TOPIC_ID,
            parse_mode='HTML',
            text=f"❌ Тренинг <b>{training['title']}</b> завершен. Статус - <b>НЕЗАЧЕТ!</b> \n\n Экзаменуемый <b>{'@' + training['recipient_username'] if training['recipient_username'] else ''}</b>, Вам в личные сообщения будет направлен отчет с результатами тренинга."
        )
    except Exception as e:
        logging.error(f"Failed to notify recipient: {e}")
    
    await callback.answer('✅ Тренинг завершен. Статус - незачет')
    
    # Refresh the view
    await manage_trainings(callback, db)

@router.callback_query(F.data.startswith('delete_training:'), AdminFilter())
async def delete_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Delete training (with confirm) """
    training_id = int(callback.data.split(':')[1])
    
    await callback.message.edit_text(
        "⚠️ <b>Точно удалить тренинг?</b>\n"
        "Это действие нельзя отменить.",
        parse_mode="HTML",
        reply_markup=confirm_keyboard(
            confirm_data=f'confirm_delete_training:{training_id}',
            cancel_data=f'select_training:{training_id}'
        )
    )
    await callback.answer()

@router.callback_query(F.data.startswith('confirm_delete_training:'), AdminFilter())
async def confirm_delete_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Confirm delete training """
    training_id = int(callback.data.split(':')[1])
    
    await db.execute("DELETE FROM trainings WHERE training_id = ?", (training_id,))
    await db.commit()
    
    await callback.answer('✅ Тренинг удален')
    
    await callback.message.edit_text(
        "Тренинг удален. Выберите действие:",
        reply_markup=main_menu_keyboard()
    )
