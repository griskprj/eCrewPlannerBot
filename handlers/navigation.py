from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite

from keyboards.inline import main_menu_keyboard, groups_keyboard, actions_keyboard
from filters import AdminFilter

router = Router()


@router.callback_query(F.data == 'back_to_actions', AdminFilter())
async def back_to_actions(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Back to group choosing """
    cursor = await db.execute(
        "SELECT group_id, group_title FROM groups ORDER BY group_title"
    )
    groups = await cursor.fetchall()

    if groups:
        await callback.message.edit_text(
            'Выберите группу:',
            reply_markup=groups_keyboard(groups)
        )
    else:
        await callback.message.edit_text(
            'Нет доступных груп',
            reply_markup=main_menu_keyboard()
        )
    await callback.answer()

@router.callback_query(F.data.startswith('back_to_group:'), AdminFilter())
async def bac_to_group(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Back to group actions """
    group_id = int(callback.data.split(':')[1])

    await callback.message.edit_text(
        'Выберите действие:',
        reply_markup=actions_keyboard(group_id)
    )
    await callback.answer()

@router.callback_query(F.data == 'back_to_events_list', AdminFilter())
async def back_to_events_list(callback: CallbackQuery, db: aiosqlite.Connection):
    """ Back to events list """
    await callback.answer('Используйте навигацию через группу', show_alert=True)
