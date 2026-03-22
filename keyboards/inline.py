from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    builder.button(text='📋 Мои группы', callback_data='my_groups')
    builder.button(text='📊 Мои мероприятия', callback_data='my_events')
    builder.adjust(1)
    return builder.as_markup()

def groups_keyboard(groups, action='group'):
    builder = InlineKeyboardBuilder()
    for group_id, title in groups:
        builder.button(text=title, callback_data=f'{action}:{group_id}')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)
    return builder.as_markup()

def actions_keyboard(group_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text='📝 Создать мероприятие', callback_data=f'create_event:{group_id}')
    builder.button(text='📝 Управление мероприятиями', callback_data=f'manage_events:{group_id}')
    builder.button(text='🎓 Назначить тренинг', callback_data=f'create_training_group:{group_id}')
    builder.button(text='🎓 Управление тренингами', callback_data=f'manage_trainings:{group_id}')
    builder.button(text='✉️ Отправить сообщение', callback_data=f'send_message:{group_id}')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)
    return builder.as_markup()

def cancel_keyboard(back_callback=None):
    builder = InlineKeyboardBuilder()
    if back_callback:
        builder.button(text='🔙 Назад', callback_data=back_callback)
    builder.button(text='❌ Отменить', callback_data='cancel')
    builder.adjust(2 if back_callback else 1)
    return builder.as_markup()

def skip_cancel_keyboard(back_callback=None):
    builder = InlineKeyboardBuilder()
    builder.button(text='⏭ Пропустить', callback_data='skip')
    if back_callback:
        builder.button(text='🔙 Назад', callback_data=back_callback)
    builder.button(text='❌ Отменить', callback_data='cancel')
    builder.adjust(2)
    return builder.as_markup()

def confirm_keyboard(confirm_data='confirm_event', cancel_data='cancel', back_callback=None):
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Подтвердить', callback_data=confirm_data)
    if back_callback:
        builder.button(text='🔙 Назад', callback_data=back_callback)
    builder.button(text='❌ Отменить', callback_data=cancel_data)
    builder.adjust(2)
    return builder.as_markup()

def confirm_training_keyboard(confirm_data='confirm_delete_training', cancel_data='select_training', back_callback=None):
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Подтвердить', callback_data=confirm_data)
    if back_callback:
        builder.button(text='🔙 Назад', callback_data=back_callback)
    builder.button(text='❌ Отменить', callback_data=cancel_data)
    builder.adjust(2)
    return builder.as_markup()

def events_list_keyboard(events, back_callback=None):
    builder = InlineKeyboardBuilder()
    for event_id, title in events:
        builder.button(text=title, callback_data=f'publish_event:{event_id}')
    if back_callback:
        builder.button(text='🔙 Назад', callback_data=back_callback)
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)
    return builder.as_markup()

def trainings_list_keyboard(trainings: list, back_callback: str = None, action: str = 'publish_training'):
    """Create keyboard with trainings list"""
    buttons = []
    
    for training in trainings:
        buttons.append([
            InlineKeyboardButton(
                text=f"📚 {training['title']}",
                callback_data=f"{action}:{training['training_id']}"
            )
        ])
    
    if back_callback:
        buttons.append([
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=back_callback
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_keyboard(confirm_data: str = 'confirm_create', cancel_data: str = 'cancel_create'):
    """Create confirmation keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data)
        ]
    ])

def registration_keyboard(event_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Записаться', callback_data=f'register:{event_id}')
    return builder.as_markup()

def creator_notification_keyboard(event_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text='👥 Список записавшихся', callback_data=f'list_registrations:{event_id}')
    builder.button(text='📢 Напомнить', callback_data=f'remind_event:{event_id}')
    builder.adjust(1)
    return builder.as_markup()

def events_management_keyboard(events, group_id=None):
    """Клавиатура со списком мероприятий для управления"""
    builder = InlineKeyboardBuilder()
    
    for event in events:
        event_id, title, _, _, status, reg_count = event
        
        emoji = {
            'created': '📝',
            'published': '📢',
            'cancelled': '❌',
            'finished': '✅'
        }.get(status, '📌')
        
        button_text = f"{emoji} {title[:30]} ({reg_count})"
        builder.button(text=button_text, callback_data=f'select_event:{event_id}')
    
    if group_id:
        builder.button(text='🔙 К действиям с группой', callback_data=f'group:{group_id}')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)
    return builder.as_markup()

def event_actions_keyboard(event_id: int, status: str, group_id: int = None):
    """Клавиатура действий для конкретного мероприятия"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text='👥 Список записавшихся', callback_data=f'list_registrations:{event_id}')
    builder.button(text='📢 Напомнить в группу', callback_data=f'remind_event:{event_id}')
    builder.button(text='📊 Экспорт в CSV', callback_data=f'export_registrations:{event_id}')
    
    if status == 'created':
        builder.button(text='📢 Опубликовать', callback_data=f'publish_event:{event_id}')
        builder.button(text='✏️ Редактировать', callback_data=f'edit_event:{event_id}')
    elif status == 'published':
        builder.button(text='✅ Завершить', callback_data=f'finish_event:{event_id}')
    
    if status != 'cancelled':
        builder.button(text='❌ Отменить', callback_data=f'cancel_event:{event_id}')
    builder.button(text='🗑 Удалить', callback_data=f'delete_event:{event_id}')
    
    builder.button(text='🔙 К списку мероприятий', callback_data=f'manage_events:{group_id}' if group_id else 'back_to_events_list')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    
    builder.adjust(1)
    return builder.as_markup()

def trainings_management_keyboard(trainings, group_id=None):
    """Клавиатура со списком тренингов для управления"""
    builder = InlineKeyboardBuilder()
    
    for training in trainings:
        training_id, title, status = training
        
        emoji = {
            'created': '📝',
            'active': '📢',
            'cancelled': '❌',
            'not_pass': '⛔',
            'pass': '✅'
        }.get(status, '📌')
        
        button_text = f"{emoji} {(title or '')[:30]}"
        builder.button(text=button_text, callback_data=f'select_training:{training_id}')
    
    if group_id:
        builder.button(text='🔙 К действиям с группой', callback_data=f'group:{group_id}')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)
    return builder.as_markup()

def training_actions_keyboard(training_id: int, status: str, group_id: int = None):
    """Клавиатура действий для конкретного тренинга"""
    builder = InlineKeyboardBuilder()
    
    if status == 'created':
        builder.button(text='📢 Назначить', callback_data=f'publish_training:{training_id}')
        builder.button(text='✏️ Редактировать', callback_data=f'edit_training:{training_id}')
    elif status == 'active' and (status != 'pass' or status != 'not_pass'):
        builder.button(text='✅ Сдан', callback_data=f'pass_training:{training_id}')
        builder.button(text='⛔ Не сдан', callback_data=f'not_pass_training:{training_id}')
    
    if status != 'cancelled':
        builder.button(text='❌ Отменить', callback_data=f'cancel_:{training_id}')
    builder.button(text='🗑 Удалить', callback_data=f'delete_training:{training_id}')
    
    builder.button(text='🔙 К списку тренингов', callback_data=f'manage_trainings:{group_id}' if group_id else 'back_to_trainings_list')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    
    builder.adjust(1)
    return builder.as_markup()

def back_to_group_keyboard(group_id: int):
    """Кнопка возврата к действиям с группой"""
    builder = InlineKeyboardBuilder()
    builder.button(text='🔙 К действиям с группой', callback_data=f'group:{group_id}')
    builder.button(text='🏠 Главное меню', callback_data='main_menu')
    builder.adjust(1)
    return builder.as_markup()