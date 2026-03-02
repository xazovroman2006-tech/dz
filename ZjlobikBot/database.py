import aiosqlite

DB_NAME = "Moderation.db"

async def init_db():
    """Инициализация базы данных и создание необходимых таблиц"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица для хранения предупреждений (варнов)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                user_id INTEGER,
                chat_id INTEGER,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )""")
        
        # Новая таблица для кэширования связи username -> user_id
        # Это позволит боту находить ID пользователя по его тегу @username
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                user_id INTEGER
            )""")
        
        await db.commit()

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С КЭШЕМ ПОЛЬЗОВАТЕЛЕЙ ---

async def update_user_cache(username: str, user_id: int):
    """Обновляет или добавляет ID пользователя в кэш по его юзернейму"""
    if not username:
        return
    async with aiosqlite.connect(DB_NAME) as db:
        # Сохраняем username в нижнем регистре для удобства поиска
        await db.execute('INSERT OR REPLACE INTO users (username, user_id) VALUES (?, ?)', 
                         (username.lower(), user_id))
        await db.commit()

async def get_user_id_from_cache(username: str):
    """Пытается найти цифровой ID пользователя в базе по его @username"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id FROM users WHERE username = ?', 
                             (username.lower(),)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ПРЕДУПРЕЖДЕНИЯМИ (ВАРНАМИ) ---

async def add_warn(user_id: int, chat_id: int):
    """Добавляет предупреждение пользователю и возвращает их новое количество"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO warnings (user_id, chat_id, count) 
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, chat_id) 
            DO UPDATE SET count = count + 1
        ''', (user_id, chat_id))
        
        async with db.execute('SELECT count FROM warnings WHERE user_id = ? AND chat_id = ?', 
                             (user_id, chat_id)) as cursor:
            row = await cursor.fetchone()
            await db.commit()
            return row[0] if row else 0

async def get_warns(user_id: int, chat_id: int):
    """Возвращает текущее количество предупреждений пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT count FROM warnings WHERE user_id = ? AND chat_id = ?', 
                             (user_id, chat_id)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def clear_warns(user_id: int, chat_id: int):
    """Полностью очищает все предупреждения пользователя в конкретном чате"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM warnings WHERE user_id = ? AND chat_id = ?', 
                        (user_id, chat_id))
        await db.commit()