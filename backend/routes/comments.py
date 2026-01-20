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
        userId = data.get("userId")
        itemId = data.get("itemId")
        comment = data.get("comment")
        if not userId or not itemId or not comment:
            logger.error(
                "Missing userId, itemId, or comment in add_comment request"
            )
            return (
                jsonify({"error": "Missing userId, itemId, or comment"}),
                400,
            )

        username = get_jellyfin_username(userId)
        db_session.add(
            Comment(
                userId=userId,
                itemId=itemId,
                username=username,
                comment=comment,
            )
        )
        logger.info(
            "Comment added: userId=%s, itemId=%s, username=%s",
            userId,
            itemId,
            username,
        )
        return jsonify({"status": "comment added"})
    except Exception as e:
        logger.error("Error in /comments: %s", str(e))
        return jsonify({"error": str(e)}), 500


@COMMENTS_BP.route("/<itemId>", methods=["GET"])
def get_comments_for_item(itemId):
    logger.debug("Received /comments/%s request", itemId)
    try:
        comment_rows = db_session.scalars(
            select(Comment).where(Comment.itemId == itemId)
        )
        comments = [
            {
                "id": row.id,
                "userId": row.userId,
                "itemId": row.itemId,
                "username": row.username,
                "comment": row.comment,
            }
            for row in comment_rows
        ]
        logger.info(
            "Retrieved %s comments for itemId=%s", len(comments), itemId
        )
        return jsonify(comments)
    except Exception as e:
        logger.error("Error in /comments/%s: %s", itemId, str(e))
        return jsonify({"error": str(e)}), 500


@COMMENTS_BP.route("/<int:commentId>", methods=["PUT"])
def edit_comment(commentId):
    logger.debug("Received /comments/%s PUT request", commentId)
    try:
        data = request.get_json()
        userId = data.get("userId")
        comment = data.get("comment")
        if not userId or not comment:
            logger.error("Missing userId or comment in edit_comment request")
            return jsonify({"error": "Missing userId or comment"}), 400

        comment_row = db_session.get(Comment, commentId)
        if not comment_row:
            logger.warning("Comment not found: id=%s", commentId)
            return jsonify({"error": "Comment not found"}), 404
        if (
            comment_row.userId != userId
            and userId not in settings.admin_user_ids
        ):
            logger.warning(
                "Unauthorized edit attempt: userId=%s, commentId=%s",
                userId,
                commentId,
            )
            return jsonify({"error": "Unauthorized"}), 403

        comment_row.comment = comment
        logger.info(
            "Comment edited: userId=%s, commentId=%s", userId, commentId
        )
        return jsonify({"status": "comment edited"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", commentId, str(e))
        return jsonify({"error": str(e)}), 500


@COMMENTS_BP.route("/<int:commentId>", methods=["DELETE"])
def delete_comment(commentId):
    logger.debug("Received /comments/%s DELETE request", commentId)
    try:
        data = request.get_json()
        userId = data.get("userId")
        if not userId:
            logger.error("Missing userId in delete_comment request")
            return jsonify({"error": "Missing userId"}), 400

        comment_row = db_session.get(Comment, commentId)
        if not comment_row:
            logger.warning("Comment not found: id=%s", commentId)
            return jsonify({"error": "Comment not found"}), 404
        if (
            comment_row.userId != userId
            and userId not in settings.admin_user_ids
        ):
            logger.warning(
                "Unauthorized delete attempt: userId=%s, commentId=%s",
                userId,
                commentId,
            )
            return jsonify({"error": "Unauthorized"}), 403

        session.delete(comment_row)
        logger.info(
            "Comment deleted: userId=%s, commentId=%s", userId, commentId
        )
        return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", commentId, str(e))
        return jsonify({"error": str(e)}), 500
