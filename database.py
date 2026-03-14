import os
import aiosqlite
import logging
from dotenv import load_dotenv

load_dotenv()
DB_PATH = 'bot_database.db'
ADMINS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))

async def init_db():
    """ Create table if not exists """
    async with aiosqlite.connect(DB_PATH) as db:
        # admins table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        ''')
        # groups table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_title TEXT
            )
        ''')
        # events table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                creator_username TEXT,
                title TEXT NOT NULL,
                date TEXT,
                time TEXT,
                place TEXT,
                description TEXT,
                status TEXT DEFAULT 'created', -- created, publised,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(group_id)
             )
        ''')
        # registrations on event table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(event_id),
                UNIQUE(event_id, user_id)
            )
        ''')
        await db.execute("DELETE FROM admins")
        for admin_id in ADMINS:
            await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
        await db.commit()
        await db.commit()
    logging.info('Database initialized')

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        yield db
