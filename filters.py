from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union
import aiosqlite

class AdminFilter(BaseFilter):
    async def __call__(self, obj: Union[Message, CallbackQuery], db: aiosqlite.Connection) -> bool:
        user_id = obj.from_user.id
        cursor = await db.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row is not None
