from flask import Blueprint, jsonify, request

from backend.db import get_db
from backend.helpers import get_jellyfin_username
from backend.logger import logger
from backend.settings import settings

COMMENTS_BP = Blueprint("comments", __name__, url_prefix="/comments")


@COMMENTS_BP.route("/", methods=["POST"])
def add_comment():
    logger.debug("Received /comments request")
    try:
        data = request.get_json()
        user_id = data.get("userId")
        item_id = data.get("itemId")
        comment = data.get("comment")
        if not user_id or not item_id or not comment:
            logger.error(
                "Missing user_id, item_id, or comment in add_comment request"
            )
            return (
                jsonify({"error": "Missing userId, itemId, or comment"}),
                400,
            )

        username = get_jellyfin_username(user_id)
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO comments (userId, itemId, username, comment) VALUES (?, ?, ?, ?)",
                (user_id, item_id, username, comment),
            )
            conn.commit()
            logger.info(
                "Comment added: user_id=%s, item_id=%s, username=%s",
                user_id,
                item_id,
                username,
            )
            return jsonify({"status": "comment added"})
    except Exception as e:
        logger.error("Error in /comments: %s", str(e))
        return jsonify({"error": str(e)}), 500


@COMMENTS_BP.route("/<item_id>", methods=["GET"])
def get_comments_for_item(item_id):
    logger.debug("Received /comments/%s request", item_id)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, userId, itemId, username, comment FROM comments WHERE itemId = ?",
                (item_id,),
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
            logger.info(
                "Retrieved %s comments for item_id=%s", len(comments), item_id
            )
            return jsonify(comments)
    except Exception as e:
        logger.error("Error in /comments/%s: %s", item_id, str(e))
        return jsonify({"error": str(e)}), 500


@COMMENTS_BP.route("/<int:comment_id>", methods=["PUT"])
def edit_comment(comment_id):
    logger.debug("Received /comments/%s PUT request", comment_id)
    try:
        data = request.get_json()
        user_id = data.get("userId")
        comment = data.get("comment")
        if not user_id or not comment:
            logger.error("Missing user_id or comment in edit_comment request")
            return jsonify({"error": "Missing userId or comment"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT userId FROM comments WHERE id = ?", (comment_id,)
            )
            result = c.fetchone()
            if not result:
                logger.warning("Comment not found: id=%s", comment_id)
                return jsonify({"error": "Comment not found"}), 404
            if (
                result["userId"] != user_id
                and user_id not in settings.admin_user_ids
            ):
                logger.warning(
                    "Unauthorized edit attempt: user_id=%s, comment_id=%s",
                    user_id,
                    comment_id,
                )
                return jsonify({"error": "Unauthorized"}), 403

            c.execute(
                "UPDATE comments SET comment = ? WHERE id = ?",
                (comment, comment_id),
            )
            conn.commit()
            logger.info(
                "Comment edited: user_id=%s, comment_id=%s",
                user_id,
                comment_id,
            )
            return jsonify({"status": "comment edited"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", comment_id, str(e))
        return jsonify({"error": str(e)}), 500


@COMMENTS_BP.route("/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    logger.debug("Received /comments/%s DELETE request", comment_id)
    try:
        data = request.get_json()
        user_id = data.get("userId")
        if not user_id:
            logger.error("Missing user_id in delete_comment request")
            return jsonify({"error": "Missing userId"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT userId FROM comments WHERE id = ?", (comment_id,)
            )
            result = c.fetchone()
            if not result:
                logger.warning("Comment not found: id=%s", comment_id)
                return jsonify({"error": "Comment not found"}), 404
            if (
                result["userId"] != user_id
                and user_id not in settings.admin_user_ids
            ):
                logger.warning(
                    "Unauthorized delete attempt: user_id=%s, comment_id=%s",
                    user_id,
                    comment_id,
                )
                return jsonify({"error": "Unauthorized"}), 403

            c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            conn.commit()
            logger.info(
                "Comment deleted: user_id=%s, comment_id=%s",
                user_id,
                comment_id,
            )
            return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", comment_id, str(e))
        return jsonify({"error": str(e)}), 500
