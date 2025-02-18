import os
import psycopg2
import logging
from bot.utils import logger
from psycopg2 import sql

logger = logging.getLogger("CodeAssistantBot")

# Function to get database connection
def get_db_connection():
    """Establish a connection to the PostgreSQL database using environment variables."""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def init_db():
    """Initialize the database and create necessary tables."""
    logger.info("Initializing the database.")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the `users` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            preferences TEXT
        )
    """)

    # Create the `projects` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Create the `tasks` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Weather Preferences Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_preferences (
            user_id INTEGER PRIMARY KEY,
            location TEXT NOT NULL,
            time TEXT DEFAULT '08:00',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Database initialized successfully.")

def get_or_create_user(telegram_id, username, first_name, last_name):
    """Check if a user exists, otherwise create a new one."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
        """, (telegram_id, username, first_name, last_name))
        conn.commit()
        logger.info(f"New user created: {first_name} {last_name} ({username})")
    else:
        logger.info(f"User exists: {first_name} {last_name} ({username})")

    cursor.close()
    conn.close()

def get_user_id(telegram_id):
    """Fetch the user ID from the database based on the Telegram ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if result:
        return result[0]
    return None

def add_project_to_db(user_id: int, project_name: str, description: str = None) -> bool:
    """Add a new project for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO projects (name, description, user_id) VALUES (%s, %s, %s)",
            (project_name, description, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding project: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_projects_from_db(user_id: int):
    """Fetch all projects for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, description FROM projects WHERE user_id = %s", (user_id,))
    projects = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return projects

def delete_project_from_db(user_id: int, project_name: str) -> bool:
    """Delete a specific project for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM projects WHERE name = %s AND user_id = %s", (project_name, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    
    cursor.close()
    conn.close()
    return deleted

def get_tasks_from_db(user_id: int):
    """Retrieve all tasks for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, description, status, due_date FROM tasks WHERE user_id = %s ORDER BY id ASC",
        (user_id,)
    )
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()
    return tasks

def add_task_to_db(user_id: int, description: str, due_date: str = None) -> bool:
    """Add a new task for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO tasks (user_id, description, due_date, status) VALUES (%s, %s, %s, %s)",
            (user_id, description, due_date, "Pending")
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

async def update_task(task_id: int, status: str) -> bool:
    """Update a task's status in the database asynchronously."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

async def delete_task(task_id: int) -> bool:
    """Delete a task from the database asynchronously."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def save_weather_preference(user_id, location, time='08:00'):
    """Save or update user weather preferences."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO weather_preferences (user_id, location, time)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET location = %s, time = %s
    """, (user_id, location, time, location, time))
    conn.commit()

    cursor.close()
    conn.close()

def get_weather_preference(user_id):
    """Retrieve the user's weather preferences."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT location, time FROM weather_preferences WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result
