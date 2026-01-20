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
                "userId": row.userId,
                "itemId": row.itemId,
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


@ADMIN_BP.route("/comments/<int:commentId>", methods=["DELETE"])
def delete_admin_comment(commentId):
    logger.debug("Received /admin/comments/%s DELETE request", commentId)
    try:
        comment_row = db_session.get(Comment, commentId)
        if comment_row is None:
            logger.warning("Comment not found: id=%s", commentId)
            return jsonify({"error": "Comment not found"}), 404
        db_session.delete(comment_row)
        logger.info("Comment deleted by admin: id=%s", commentId)
        return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /admin/comments/%s: %s", commentId, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/comments/user/<userId>", methods=["DELETE"])
def delete_comments_by_user(userId):
    logger.debug("Received /admin/comments/user/%s DELETE request", userId)
    try:
        result = db_session.execute(
            delete(Comment).where(Comment.userId == userId)
        )
        logger.info(
            "Comments deleted for userId=%s, rows affected=%s",
            userId,
            result.rowcount or 0,
        )
        return jsonify({"status": "comments deleted for user"})
    except Exception as e:
        logger.error("Error in /admin/comments/user/%s: %s", userId, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/settings", methods=["GET"])
def get_settings():
    logger.debug("Received /admin/settings request")
    try:
        globalLimit = (
            db_session.scalars(select(Setting.globalLimit)).one_or_none() or 0
        )
        userLimits = {
            row.userId: row.limit
            for row in db_session.scalars(select(UserSetting)).all()
        }
        logger.info(
            "Settings retrieved: globalLimit=%s, userLimits=%s",
            globalLimit,
            userLimits,
        )
        return jsonify(
            {
                "globalLimit": globalLimit,
                "userLimits": userLimits,
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
        globalLimit = data.get("globalLimit", 0)
        userId = data.get("userId")
        perUserLimit = data.get("perUserLimit", 0)

        db_session.execute(delete(Setting))
        db_session.add(Setting(globalLimit=globalLimit))
        if userId:
            db_session.execute(
                delete(UserSetting).where(UserSetting.userId == userId)
            )
            db_session.add(UserSetting(userId=userId, limit=perUserLimit))
        logger.info(
            "Settings saved: globalLimit=%s, userId=%s, perUserLimit=%s",
            globalLimit,
            userId,
            perUserLimit,
        )
        return jsonify({"status": "settings saved"})
    except Exception as e:
        logger.error("Error in /admin/settings: %s", str(e))
        return jsonify({"error": str(e)}), 500
