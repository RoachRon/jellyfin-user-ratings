from pathlib import Path

from flask import Blueprint, jsonify, url_for

from backend.logger import logger
from backend.settings import PROJECT_ROOT, settings

ASSETS_BP = Blueprint("assets", __name__, url_prefix="/assets")
UPDOOT_JS_PATH = Path(f"{PROJECT_ROOT}/frontend/src/updoot.js")


@ASSETS_BP.get("/config.json")
def updoot_config():
    """
    Serve runtime config for the Jellyfin injector/bootstrap script.

    Intentionally NOT cacheable: config should update immediately when env
    changes.
    """
    cfg = {
        "updootSrc": url_for(
            "assets.updoot_js", version=settings.cache_version
        ),
        "adminUserIds": settings.admin_user_ids,
    }

    resp = jsonify(cfg)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@ASSETS_BP.get("/updoot.<version>.js")
def updoot_js(version: str):  # pylint: disable=unused-argument
    """
    Serve the Jellyfin web mod script.
    """
    try:
        body = UPDOOT_JS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("updoot.js not found at %s", UPDOOT_JS_PATH)
        return (
            jsonify(
                {
                    "error": "updoot.js not found",
                    "path": str(UPDOOT_JS_PATH),
                }
            ),
            500,
        )

    return (
        body,
        200,
        {
            "Content-Type": "application/javascript; charset=utf-8",
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": settings.cache_version,
        },
    )
