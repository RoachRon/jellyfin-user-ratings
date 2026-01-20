from flask import Blueprint, jsonify, request
from sqlalchemy import select

from backend.db import db_session
from backend.helpers import get_jellyfin_username
from backend.logger import logger
from backend.models import Comment
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
        db_session.add(
            Comment(
                user_id=user_id,
                item_id=item_id,
                username=username,
                comment=comment,
            )
        )
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
        comment_rows = db_session.scalars(
            select(Comment).where(Comment.item_id == item_id)
        )
        comments = [
            {
                "id": row.id,
                "userId": row.user_id,
                "itemId": row.item_id,
                "username": row.username,
                "comment": row.comment,
            }
            for row in comment_rows
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

        comment_row = db_session.get(Comment, comment_id)
        if not comment_row:
            logger.warning("Comment not found: id=%s", comment_id)
            return jsonify({"error": "Comment not found"}), 404
        if (
            comment_row.user_id != user_id
            and user_id not in settings.admin_user_ids
        ):
            logger.warning(
                "Unauthorized edit attempt: user_id=%s, comment_id=%s",
                user_id,
                comment_id,
            )
            return jsonify({"error": "Unauthorized"}), 403

        comment_row.comment = comment
        logger.info(
            "Comment edited: user_id=%s, comment_id=%s", user_id, comment_id
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

        comment_row = db_session.get(Comment, comment_id)
        if not comment_row:
            logger.warning("Comment not found: id=%s", comment_id)
            return jsonify({"error": "Comment not found"}), 404
        if (
            comment_row.user_id != user_id
            and user_id not in settings.admin_user_ids
        ):
            logger.warning(
                "Unauthorized delete attempt: user_id=%s, comment_id=%s",
                user_id,
                comment_id,
            )
            return jsonify({"error": "Unauthorized"}), 403

        db_session.delete(comment_row)
        logger.info(
            "Comment deleted: user_id=%s, comment_id=%s", user_id, comment_id
        )
        return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", comment_id, str(e))
        return jsonify({"error": str(e)}), 500
