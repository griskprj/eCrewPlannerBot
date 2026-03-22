def format_date_preview(data: dict, creator_username: str = None) -> str:
    lines = []
    lines.append(data['title'])
    lines.append('\n')
    if creator_username:
        lines.append(f"<i>Хост:</i> @{creator_username}\n")
    if data.get('date'):
        lines.append(f"<i>Дата:</i> {data['date']}\n")
    if data.get('time'):
        lines.append(f"<i>Время:</i> {data['time']}\n")
    if data.get('place'):
        lines.append(f"<i>Маршрут:</i> {data['place']}\n")
    if data.get('description'):
        lines.append(f"<i>Описание:</i> {data['description']}\n")
    return "\n".join(lines)

def format_training_preview(data: dict) -> str:
    """Format training preview for display"""
    status_emoji = {
        'created': '📝',
        'active': '🔄',
        'pass': '✅',
        'cancelled': '❌'
    }
    
    status_text = {
        'created': 'Создан',
        'active': 'Активен',
        'pass': 'Зачет',
        'cancelled': 'Отменен'
    }
    
    preview = f"<b>🎓 {data.get('title', 'Без названия')}</b>\n\n"
    
    if data.get('date'):
        preview += f"<i>Дата:</i> {data['date']}\n"
    if data.get('time'):
        preview += f"<i>Время:</i> {data['time']}\n"
    if data.get('place'):
        preview += f"<i>Рейс:</i> {data['place']}\n"
    
    preview += f"\n <i>Получатель:</i> <b>@{data.get('recipient_username', 'Не указан') or data.get('recipient_id', 'Не указан')}</b>\n"
    preview += f"<i>Инструктор:</i> <b>@{data.get('instructor_username', 'Не указан') or data.get('instructor_id', 'Не указан')}</b>\n"
    
    if data.get('description'):
        preview += f"\n <i>Описание:</i> \n{data['description']}\n"
    
    if data.get('status'):
        emoji = status_emoji.get(data['status'], '📌')
        status = status_text.get(data['status'], data['status'])
        preview += f"\n{emoji} Статус: {status}"
    
    return preview
