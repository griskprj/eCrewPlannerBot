from aiogram import Router
from aiogram.types import ChatMemberUpdated
import aiosqlite
import logging

router = Router()

@router.my_chat_member()
async def handle_my_chat_member(update: ChatMemberUpdated, db: aiosqlite.Connection):
    if update.chat.type in ("group", "supergroup"):
        if update.old_chat_member.status in ("left", "kicked") and update.new_chat_member.status in ("member", "administrator"):
            group_id = update.chat.id
            group_title = update.chat.title or "Без названия"
            
            await db.execute(
                "INSERT OR IGNORE INTO groups (group_id, group_title) VALUES (?, ?)",
                (group_id, group_title)
            )
            await db.commit()
        
        try:
            await update.bot.send_message(
                chat_id=group_id,
                text=(
                    f"👋 Всем привет! Я бот для управления мероприятиями.\n\n"
                    f"Чтобы начать работу, отправьте мне команду /start в личные сообщения.\n"
                    f"Я уже добавил эту группу в вашу базу данных!"
                )
            )
        except Exception as e:
            logging.error(f"Не удалось отправить приветствие в группу {group_id}: {e}")
