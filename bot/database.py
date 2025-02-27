import os
import asyncpg
import logging
from bot.utils import logger

logger = logging.getLogger("CodeAssistantBot")

_pool = None

async def init_db_pool():
    """Initialize and return the global asyncpg connection pool."""
    global _pool
    dsn = f"postgres://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    _pool = await asyncpg.create_pool(dsn)
    return _pool

async def get_db_pool():
    """Return the global asyncpg connection pool, initializing it if necessary."""
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool

async def init_db():
    """Initialize the database and create necessary tables."""
    logger.info("Initializing the database.")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # DDL statements are auto-committed if not in an explicit transaction.
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                preferences TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_preferences (
                user_id INTEGER PRIMARY KEY,
                location TEXT NOT NULL,
                time TEXT DEFAULT '08:00',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
    logger.info("Database initialized successfully.")

async def get_or_create_user(telegram_id, username, first_name, last_name):
    """Check if a user exists; otherwise, create a new one."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        if not user:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
            """, telegram_id, username, first_name, last_name)
            logger.info(f"New user created: {first_name} {last_name} ({username})")
        else:
            logger.info(f"User exists: {first_name} {last_name} ({username})")

async def get_user_id(telegram_id):
    """Fetch the user ID from the database based on the Telegram ID."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM users WHERE telegram_id = $1", telegram_id)
        if row:
            return row["id"]
    return None

async def add_project_to_db(user_id: int, project_name: str, description: str = None) -> bool:
    """Add a new project for a user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO projects (name, description, user_id)
                VALUES ($1, $2, $3)
            """, project_name, description, user_id)
            return True
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            return False

async def get_projects_from_db(user_id: int):
    """Fetch all projects for a specific user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT name, description FROM projects WHERE user_id = $1", user_id)
    return rows

async def delete_project_from_db(user_id: int, project_name: str) -> bool:
    """Delete a specific project for a user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM projects WHERE name = $1 AND user_id = $2", project_name, user_id)
        # asyncpg returns a string like "DELETE n"
        return result.startswith("DELETE")

async def get_tasks_from_db(user_id: int):
    """Retrieve all tasks for a specific user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, description, status, due_date
            FROM tasks WHERE user_id = $1
            ORDER BY id ASC
        """, user_id)
    return rows

async def add_task_to_db(user_id: int, description: str, due_date: str = None) -> bool:
    """Add a new task for a user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO tasks (user_id, description, due_date, status)
                VALUES ($1, $2, $3, $4)
            """, user_id, description, due_date, "Pending")
            return True
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return False

async def update_task(task_id: int, status: str) -> bool:
    """Update a task's status asynchronously."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.execute("UPDATE tasks SET status = $1 WHERE id = $2", status, task_id)
            return result.startswith("UPDATE")
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False

async def delete_task(task_id: int) -> bool:
    """Delete a task asynchronously."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.execute("DELETE FROM tasks WHERE id = $1", task_id)
            return result.startswith("DELETE")
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False

async def save_weather_preference(user_id, location, time='08:00'):
    """Save or update user weather preferences."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO weather_preferences (user_id, location, time)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET location = $2, time = $3
        """, user_id, location, time)

async def get_weather_preference(user_id):
    """Retrieve the user's weather preferences."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT location, time FROM weather_preferences WHERE user_id = $1", user_id)
    return row
