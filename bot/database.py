import os
import asyncio
import aiopg
import logging
from bot.utils import logger

logger = logging.getLogger("CodeAssistantBot")

# Global variable for the connection pool
_pool = None

async def init_db_pool():
    """Initialize and return the global aiopg connection pool."""
    global _pool
    dsn = (
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')} "
        f"host={os.getenv('DB_HOST')} "
        f"port={os.getenv('DB_PORT')}"
    )
    _pool = await aiopg.create_pool(dsn)
    return _pool

async def get_db_pool():
    """Return the global aiopg connection pool, initializing it if necessary."""
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool

async def init_db():
    """Initialize the database and create necessary tables."""
    logger.info("Initializing the database.")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    preferences TEXT
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    due_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS weather_preferences (
                    user_id INTEGER PRIMARY KEY,
                    location TEXT NOT NULL,
                    time TEXT DEFAULT '08:00',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            await conn.commit()
    logger.info("Database initialized successfully.")

async def get_or_create_user(telegram_id, username, first_name, last_name):
    """Check if a user exists, otherwise create a new one."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            user = await cur.fetchone()
            if not user:
                await cur.execute("""
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES (%s, %s, %s, %s)
                """, (telegram_id, username, first_name, last_name))
                await conn.commit()
                logger.info(f"New user created: {first_name} {last_name} ({username})")
            else:
                logger.info(f"User exists: {first_name} {last_name} ({username})")

async def get_user_id(telegram_id):
    """Fetch the user ID from the database based on the Telegram ID."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
            result = await cur.fetchone()
    if result:
        return result[0]
    return None

async def add_project_to_db(user_id: int, project_name: str, description: str = None) -> bool:
    """Add a new project for a user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO projects (name, description, user_id) VALUES (%s, %s, %s)",
                    (project_name, description, user_id)
                )
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding project: {e}")
                return False

async def get_projects_from_db(user_id: int):
    """Fetch all projects for a specific user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT name, description FROM projects WHERE user_id = %s", (user_id,))
            projects = await cur.fetchall()
    return projects

async def delete_project_from_db(user_id: int, project_name: str) -> bool:
    """Delete a specific project for a user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM projects WHERE name = %s AND user_id = %s", (project_name, user_id))
            deleted = cur.rowcount > 0
            await conn.commit()
    return deleted

async def get_tasks_from_db(user_id: int):
    """Retrieve all tasks for a specific user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, description, status, due_date FROM tasks WHERE user_id = %s ORDER BY id ASC",
                (user_id,)
            )
            tasks = await cur.fetchall()
    return tasks

async def add_task_to_db(user_id: int, description: str, due_date: str = None) -> bool:
    """Add a new task for a user."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO tasks (user_id, description, due_date, status) VALUES (%s, %s, %s, %s)",
                    (user_id, description, due_date, "Pending")
                )
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding task: {e}")
                return False

async def update_task(task_id: int, status: str) -> bool:
    """Update a task's status in the database asynchronously."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
                await conn.commit()
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Error updating task: {e}")
                return False

async def delete_task(task_id: int) -> bool:
    """Delete a task from the database asynchronously."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
                await conn.commit()
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Error deleting task: {e}")
                return False

async def save_weather_preference(user_id, location, time='08:00'):
    """Save or update user weather preferences."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO weather_preferences (user_id, location, time)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET location = %s, time = %s
            """, (user_id, location, time, location, time))
            await conn.commit()

async def get_weather_preference(user_id):
    """Retrieve the user's weather preferences."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT location, time FROM weather_preferences WHERE user_id = %s", (user_id,))
            result = await cur.fetchone()
    return result
