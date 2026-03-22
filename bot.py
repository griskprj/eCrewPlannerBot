import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, get_db
from middlewares import DbSessionMiddleware
import aiosqlite

from handlers import menu, navigation, group_actions, chat_member
from handlers.events import manage_events, register_to_event, publish_event
from handlers.trainings import manage_trainings, publish_training, create_training_handlers

async def main():
    await init_db()

    async with aiosqlite.connect('bot_database.db') as db:
        for admin_id in ADMIN_IDS:
            await db.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            await db.commit()
        
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(menu.router)
    dp.include_router(navigation.router)
    dp.include_router(group_actions.router)
    dp.include_router(manage_events.router)
    dp.include_router(register_to_event.router)
    dp.include_router(publish_event.router)
    dp.include_router(chat_member.router)
    dp.include_router(create_training_handlers.router)
    dp.include_router(manage_trainings.router)
    dp.include_router(publish_training.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
