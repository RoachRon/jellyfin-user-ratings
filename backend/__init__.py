import os

from flask import Flask

from backend.db import init_db
from backend.logger import logger
from backend.settings import settings

APP = Flask(__name__, root_path=settings.app_root_path)

# Init database if it doesn't exist
if not os.path.exists(settings.db_path):
    logger.info("Database not found, initializing")
    init_db()

# pylint: disable=wrong-import-position
from backend.routes.admin import ADMIN_BP
from backend.routes.assets import ASSETS_BP
from backend.routes.comments import COMMENTS_BP
from backend.routes.recommendations import RECOMMENDATIONS_BP

# pylint: enable=wrong-import-position

APP.register_blueprint(ADMIN_BP)
APP.register_blueprint(ASSETS_BP)
APP.register_blueprint(COMMENTS_BP)
APP.register_blueprint(RECOMMENDATIONS_BP)
