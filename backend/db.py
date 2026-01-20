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
        _migrate_legacy_tables()
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
        db_session.add(Setting(global_limit=0))
        db_session.commit()


def _migrate_legacy_tables() -> None:
    _migrate_legacy_recommendations_table()
    _migrate_legacy_comments_table()
    _migrate_legacy_settings_tables()


def _migrate_legacy_recommendations_table() -> None:
    inspector = inspect(ENGINE)

    # If table doesn't exist, skip
    if "recommendations" not in inspector.get_table_names():
        return

    # If not legacy schema, skip
    columns = {col["name"] for col in inspector.get_columns("recommendations")}
    if "userId" not in columns:
        return

    # Ensure expected columns are present
    expected_columns = {"userId", "itemId", "username"}
    missing_columns = expected_columns - columns
    if missing_columns:
        raise ValueError(
            "Missing expected columns in legacy recommendations table: "
            f"{missing_columns}"
        )

    logger.info("Migrating recommendations table to snake_case columns")
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE recommendations_new (
                    user_id TEXT,
                    item_id TEXT,
                    username TEXT,
                    PRIMARY KEY (user_id, item_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO recommendations_new (user_id, item_id, username)
                SELECT userId, itemId, username
                FROM recommendations
                """
            )
        )
        conn.execute(text("DROP TABLE recommendations"))
        conn.execute(
            text("ALTER TABLE recommendations_new RENAME TO recommendations")
        )


def _migrate_legacy_comments_table() -> None:
    inspector = inspect(ENGINE)

    # If table doesn't exist, skip
    if "comments" not in inspector.get_table_names():
        return

    # If not legacy schema, skip
    columns = {col["name"] for col in inspector.get_columns("comments")}
    if "userId" not in columns:
        return

    # Ensure expected columns are present
    expected_columns = {"userId", "itemId", "username", "comment"}
    missing_columns = expected_columns - columns
    if missing_columns:
        raise ValueError(
            "Missing expected columns in legacy comments table: "
            f"{missing_columns}"
        )

    logger.info("Migrating comments table to snake_case columns")
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE comments_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    item_id TEXT,
                    username TEXT,
                    comment TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO comments_new (id, user_id, item_id, username, comment)
                SELECT id, userId, itemId, username, comment
                FROM comments
                """
            )
        )
        conn.execute(text("DROP TABLE comments"))
        conn.execute(text("ALTER TABLE comments_new RENAME TO comments"))


def _migrate_legacy_settings_tables() -> None:
    inspector = inspect(ENGINE)

    # If table doesn't exist, skip
    if "settings" not in inspector.get_table_names():
        return

    # If not legacy schema, skip
    columns = {col["name"] for col in inspector.get_columns("settings")}
    if "userId" not in columns:
        return

    # Ensure expected columns are present
    expected_columns = {"userId", "globalLimit", "perUserLimit"}
    missing_columns = expected_columns - columns
    if missing_columns:
        raise ValueError(
            "Missing expected columns in legacy settings table: "
            f"{missing_columns}"
        )

    logger.info("Migrating settings table to split global/user settings")
    with ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE settings_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    global_limit INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_settings (
                    user_id TEXT PRIMARY KEY,
                    user_limit INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO settings_new (global_limit)
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
                INSERT INTO user_settings (user_id, user_limit)
                SELECT userId, perUserLimit
                FROM settings
                WHERE userId IS NOT NULL
                """
            )
        )
        conn.execute(text("DROP TABLE settings"))
        conn.execute(text("ALTER TABLE settings_new RENAME TO settings"))
