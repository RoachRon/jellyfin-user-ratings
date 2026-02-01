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


@ADMIN_BP.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_admin_comment(comment_id):
    logger.debug("Received /admin/comments/%s DELETE request", comment_id)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            if c.rowcount == 0:
                logger.warning("Comment not found: id=%s", comment_id)
                return jsonify({"error": "Comment not found"}), 404
            conn.commit()
            logger.info("Comment deleted by admin: id=%s", comment_id)
            return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /admin/comments/%s: %s", comment_id, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/comments/user/<user_id>", methods=["DELETE"])
def delete_comments_by_user(user_id):
    logger.debug("Received /admin/comments/user/%s DELETE request", user_id)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM comments WHERE userId = ?", (user_id,))
            logger.info(
                "Comments deleted for user_id=%s, rows affected=%s",
                user_id,
                c.rowcount,
            )
            conn.commit()
            return jsonify({"status": "comments deleted for user"})
    except Exception as e:
        logger.error("Error in /admin/comments/user/%s: %s", user_id, str(e))
        return jsonify({"error": str(e)}), 500


@ADMIN_BP.route("/settings", methods=["GET"])
def get_settings():
    logger.debug("Received /admin/settings request")
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT globalLimit FROM settings WHERE ROWID = 1")
            global_limit = c.fetchone()
            c.execute(
                "SELECT userId, perUserLimit FROM settings WHERE userId IS NOT NULL"
            )
            user_limits = {
                row["userId"]: row["perUserLimit"] for row in c.fetchall()
            }
            logger.info(
                "Settings retrieved: global_limit=%s, user_limits=%s",
                global_limit["globalLimit"] if global_limit else 0,
                user_limits,
            )
            return jsonify(
                {
                    "globalLimit": (
                        global_limit["globalLimit"] if global_limit else 0
                    ),
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

        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM settings WHERE ROWID = 1")
            c.execute(
                "INSERT INTO settings (globalLimit, userId, perUserLimit) VALUES (?, NULL, NULL)",
                (global_limit,),
            )
            if user_id:
                c.execute("DELETE FROM settings WHERE userId = ?", (user_id,))
                c.execute(
                    "INSERT INTO settings (globalLimit, userId, perUserLimit) VALUES (NULL, ?, ?)",
                    (user_id, per_user_limit),
                )
            conn.commit()
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
