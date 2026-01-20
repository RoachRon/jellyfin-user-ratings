from flask import Blueprint, jsonify, request
from sqlalchemy import delete, select

from backend.db import db_session
from backend.logger import logger
from backend.models import Comment, Setting, UserSetting

ADMIN_BP = Blueprint("admin", __name__, url_prefix="/admin")


@ADMIN_BP.route("/comments", methods=["GET"])
def get_all_comments():
    logger.debug("Received /admin/comments request")
    try:
        rows = db_session.scalars(select(Comment)).all()
        comments = [
            {
                "id": row.id,
                "userId": row.user_id,
                "itemId": row.item_id,
                "username": row.username,
                "comment": row.comment,
            }
            for row in rows
        ]
        logger.info("Retrieved %s comments for admin", len(comments))
        return jsonify(comments)
    except Exception as e:
        logger.error("Error in /admin/comments: %s", str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_admin_comment(comment_id):
    logger.debug("Received /admin/comments/%s DELETE request", comment_id)
    try:
        comment_row = db_session.get(Comment, comment_id)
        if comment_row is None:
            logger.warning("Comment not found: id=%s", comment_id)
            return jsonify({"error": "Comment not found"}), 404
        db_session.delete(comment_row)
        logger.info("Comment deleted by admin: id=%s", comment_id)
        return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /admin/comments/%s: %s", comment_id, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/comments/user/<user_id>", methods=["DELETE"])
def delete_comments_by_user(user_id):
    logger.debug("Received /admin/comments/user/%s DELETE request", user_id)
    try:
        result = db_session.execute(
            delete(Comment).where(Comment.user_id == user_id)
        )
        logger.info(
            "Comments deleted for user_id=%s, rows affected=%s",
            user_id,
            result.rowcount or 0,
        )
        return jsonify({"status": "comments deleted for user"})
    except Exception as e:
        logger.error("Error in /admin/comments/user/%s: %s", user_id, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/settings", methods=["GET"])
def get_settings():
    logger.debug("Received /admin/settings request")
    try:
        global_limit = (
            db_session.scalars(select(Setting.global_limit)).one_or_none() or 0
        )
        user_limits = {
            row.user_id: row.user_limit
            for row in db_session.scalars(select(UserSetting)).all()
        }
        logger.info(
            "Settings retrieved: global_limit=%s, userLimits=%s",
            global_limit,
            user_limits,
        )
        return jsonify(
            {
                "globalLimit": global_limit,
                "userLimits": user_limits,
            }
        )
    except Exception as e:
        logger.error("Error in /admin/settings: %s", str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/settings", methods=["POST"])
def save_settings():
    logger.debug("Received /admin/settings POST request")
    try:
        data = request.get_json()
        global_limit = data.get("globalLimit", 0)
        user_id = data.get("userId")
        per_user_limit = data.get("perUserLimit", 0)

        db_session.execute(delete(Setting))
        db_session.add(Setting(global_limit=global_limit))
        if user_id:
            db_session.execute(
                delete(UserSetting).where(UserSetting.user_id == user_id)
            )
            db_session.add(
                UserSetting(user_id=user_id, user_limit=per_user_limit)
            )
        logger.info(
            "Settings saved: global_limit=%s, user_id=%s, per_user_limit=%s",
            global_limit,
            user_id,
            per_user_limit,
        )
        return jsonify({"status": "settings saved"})
    except Exception as e:
        logger.error("Error in /admin/settings: %s", str(e))
        return jsonify({"error": str(e)}), 500
