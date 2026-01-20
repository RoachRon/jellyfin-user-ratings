import os
import sqlite3

from backend.logger import logger
from backend.settings import settings


def init_db():
    logger.debug("Initializing database at %s", settings.db_path)
    try:
        os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
        with sqlite3.connect(settings.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """CREATE TABLE IF NOT EXISTS recommendations
                         (userId TEXT, itemId TEXT, username TEXT)"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS comments
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, userId TEXT, itemId TEXT, username TEXT, comment TEXT)"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS settings
                         (globalLimit INTEGER, userId TEXT, perUserLimit INTEGER)"""
            )
            c.execute(
                "INSERT OR IGNORE INTO settings (globalLimit, userId, perUserLimit) VALUES (0, NULL, NULL)"
            )
            conn.commit()
        logger.info(
            "Database initialized successfully at %s", settings.db_path
        )
    except sqlite3.OperationalError as e:
        logger.error("Failed to initialize database: %s", str(e))
        raise


def get_db():
    logger.debug("Connecting to database")
    try:
        conn = sqlite3.connect(settings.db_path)
        conn.row_factory = sqlite3.Row
        logger.debug("Database connection established")
        return conn
    except sqlite3.OperationalError as e:
        logger.error("Failed to connect to database: %s", str(e))
        raise
