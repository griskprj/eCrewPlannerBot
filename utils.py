def format_date_preview(data: dict, creator_username: str = None) -> str:
    lines = []
    lines.append(data['title'])
    if creator_username:
        lines.append(f"Хост: @{creator_username}")
    if data.get('date'):
        lines.append(f"Дата: {data['date']}")
    if data.get('time'):
        lines.append(f"Время: {data['time']}")
    if data.get('place'):
        lines.append(f"Место: {data['place']}")
    if data.get('description'):
        lines.append(f"Описание: {data['description']}")
    return "\n".join(lines)
