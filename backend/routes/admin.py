from flask import Blueprint, jsonify, request

from backend.db import get_db
from backend.logger import logger

ADMIN_BP = Blueprint("admin", __name__, url_prefix="/admin")


@ADMIN_BP.route("/comments", methods=["GET"])
def get_all_comments():
    logger.debug("Received /admin/comments request")
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, userId, itemId, username, comment FROM comments"
            )
            comments = [
                {
                    "id": row["id"],
                    "userId": row["userId"],
                    "itemId": row["itemId"],
                    "username": row["username"],
                    "comment": row["comment"],
                }
                for row in c.fetchall()
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
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM comments WHERE id = ?", (commentId,))
            if c.rowcount == 0:
                logger.warning("Comment not found: id=%s", commentId)
                return jsonify({"error": "Comment not found"}), 404
            conn.commit()
            logger.info("Comment deleted by admin: id=%s", commentId)
            return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /admin/comments/%s: %s", commentId, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/comments/user/<userId>", methods=["DELETE"])
def delete_comments_by_user(userId):
    logger.debug("Received /admin/comments/user/%s DELETE request", userId)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM comments WHERE userId = ?", (userId,))
            logger.info(
                "Comments deleted for userId=%s, rows affected=%s",
                userId,
                c.rowcount,
            )
            conn.commit()
            return jsonify({"status": "comments deleted for user"})
    except Exception as e:
        logger.error("Error in /admin/comments/user/%s: %s", userId, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/settings", methods=["GET"])
def get_settings():
    logger.debug("Received /admin/settings request")
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT globalLimit FROM settings WHERE ROWID = 1")
            globalLimit = c.fetchone()
            c.execute(
                "SELECT userId, perUserLimit FROM settings WHERE userId IS NOT NULL"
            )
            userLimits = {
                row["userId"]: row["perUserLimit"] for row in c.fetchall()
            }
            logger.info(
                "Settings retrieved: globalLimit=%s, userLimits=%s",
                globalLimit["globalLimit"] if globalLimit else 0,
                userLimits,
            )
            return jsonify(
                {
                    "globalLimit": (
                        globalLimit["globalLimit"] if globalLimit else 0
                    ),
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

        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM settings WHERE ROWID = 1")
            c.execute(
                "INSERT INTO settings (globalLimit, userId, perUserLimit) VALUES (?, NULL, NULL)",
                (globalLimit,),
            )
            if userId:
                c.execute("DELETE FROM settings WHERE userId = ?", (userId,))
                c.execute(
                    "INSERT INTO settings (globalLimit, userId, perUserLimit) VALUES (NULL, ?, ?)",
                    (userId, perUserLimit),
                )
            conn.commit()
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
