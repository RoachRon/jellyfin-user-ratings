import os

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import scoped_session, sessionmaker

from backend.logger import logger
from backend.models import Base, Setting
from backend.settings import settings

DB_URL = f"sqlite+pysqlite:///{settings.db_path}"
ENGINE = create_engine(DB_URL, future=True)
db_session = scoped_session(
    sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)
)


def init_db():
    logger.debug("Initializing database at %s", settings.db_path)
    try:
        os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
        _migrate_settings_tables()
        Base.metadata.create_all(ENGINE)
        _ensure_global_settings_row()
        logger.info(
            "Database initialized successfully at %s", settings.db_path
        )
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e))
        raise


def _ensure_global_settings_row() -> None:
    existing = db_session.scalars(select(Setting)).first()
    if existing is None:
        db_session.add(Setting(globalLimit=0))
        db_session.commit()


def _migrate_settings_tables() -> None:
    inspector = inspect(ENGINE)
    if "settings" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("settings")}
    if "userId" not in columns and "perUserLimit" not in columns:
        return
    logger.info("Migrating settings table to split global/user settings")
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE settings_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    globalLimit INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_settings (
                    userId TEXT PRIMARY KEY,
                    limit INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO settings_new (globalLimit)
                SELECT globalLimit
                FROM settings
                WHERE userId IS NULL
                LIMIT 1
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO user_settings (userId, limit)
                SELECT userId, perUserLimit
                FROM settings
                WHERE userId IS NOT NULL
                """
            )
        )
        conn.execute(text("DROP TABLE settings"))
        conn.execute(text("ALTER TABLE settings_new RENAME TO settings"))
