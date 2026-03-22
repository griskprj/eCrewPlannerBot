from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from dotenv import load_dotenv
import aiosqlite
import logging
import os

from filters import AdminFilter
from keyboards.inline import (
    trainings_list_keyboard,
    back_to_group_keyboard,
    main_menu_keyboard,
    groups_keyboard
)
from utils import format_training_preview

router = Router()
load_dotenv()

TRAININGS_TOPIC_ID = os.getenv('TRAININGS_TOPIC_ID')

@router.message(Command('publish_training'), AdminFilter())
async def cmd_publish_training(message: Message, db: aiosqlite.Connection):
    """Start training publishing process"""
    cursor = await db.execute("SELECT group_id, group_title FROM groups")
    groups = await cursor.fetchall()
    
    if not groups:
        await message.answer(
            "❌ Нет доступных групп",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await message.answer(
        '📢 <b>Публикация тренинга</b>\n\nВыберите группу:',
        parse_mode='HTML',
        reply_markup=groups_keyboard(groups, action='publish_training_choose')
    )

@router.callback_query(F.data.startswith('publish_training_choose:'), AdminFilter())
async def select_group_for_publish(callback: CallbackQuery, db: aiosqlite.Connection):
    """Show trainings for selected group"""
    group_id = int(callback.data.split(':')[1])
    
    cursor = await db.execute(
        "SELECT training_id, title FROM trainings WHERE group_id = ? AND status = 'created'",
        (group_id,)
    )
    trainings = await cursor.fetchall()
    
    if not trainings:
        await callback.message.edit_text(
            '❌ Нет тренингов со статусом "created" для этой группы',
            reply_markup=back_to_group_keyboard(group_id)
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        '📋 Выберите тренинг для публикации:',
        parse_mode='HTML',
        reply_markup=trainings_list_keyboard(trainings, back_callback=f'group:{group_id}', action='publish_training')
    )
    await callback.answer()

@router.callback_query(F.data.startswith('publish_training:'), AdminFilter())
async def publish_training(callback: CallbackQuery, db: aiosqlite.Connection):
    """Publish selected training"""
    training_id = int(callback.data.split(':')[1])

    cursor = await db.execute(
        """SELECT training_id, group_id, instructor_username, instructor_id,
                  recipient_username, recipient_id, title, date, time, place, description
           FROM trainings WHERE training_id = ?""",
        (training_id,)
    )
    training = await cursor.fetchone()
    
    if not training:
        await callback.answer('Тренинг не найден', show_alert=True)
        return
    
    data = dict(training)
    print(data)
    text = format_training_preview(data)
    group_id = training['group_id']
    message_thread_id = TRAININGS_TOPIC_ID
    print('Groupd ID: ', group_id)
    print('Topic ID: ', message_thread_id)

    
    try:
        await callback.bot.send_message(
            chat_id=group_id,
            message_thread_id=message_thread_id,
            text=text,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Failed to send training to recipient: {e}")
        await callback.answer('⚠️ Не удалось отправить тренинг в группу', show_alert=True)
        return

    # Update status
    await db.execute(
        "UPDATE trainings SET status = 'active' WHERE training_id = ?",
        (training_id,)
    )
    await db.commit()

    await callback.message.edit_text(
        '✅ Тренинг успешно опубликован и отправлен в группу!',
        parse_mode='HTML',
        reply_markup=back_to_group_keyboard(data['group_id'])
    )
    await callback.answer()