from flask import Flask

from backend.settings import settings

APP = Flask(__name__)

# pylint: disable=wrong-import-position
import backend.util.request_hooks
from backend.routes.admin import ADMIN_BP
from backend.routes.assets import ASSETS_BP
from backend.routes.comments import COMMENTS_BP
from backend.routes.recommendations import RECOMMENDATIONS_BP

# pylint: enable=wrong-import-position


def register_blueprint(bp):
    combined_prefix = settings.app_root_path + (bp.url_prefix or "")
    APP.register_blueprint(bp, url_prefix=combined_prefix)


register_blueprint(ADMIN_BP)
register_blueprint(ASSETS_BP)
register_blueprint(COMMENTS_BP)
register_blueprint(RECOMMENDATIONS_BP)
