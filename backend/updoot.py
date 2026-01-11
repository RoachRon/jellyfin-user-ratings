import logging
import os
import sqlite3

import requests
from flask import Flask, jsonify, request

from backend.settings import settings

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    filename="./flask-app.log",
    filemode="a",
)
logger = logging.getLogger(__name__)


def init_db():
    logger.debug("Initializing database at %s", settings.db_path)
    try:
        os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
        with sqlite3.connect(settings.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """CREATE TABLE IF NOT EXISTS recommendations
                         (userId TEXT, itemId TEXT, username TEXT)"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS comments
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, userId TEXT, itemId TEXT, username TEXT, comment TEXT)"""
            )
            c.execute(
                """CREATE TABLE IF NOT EXISTS settings
                         (globalLimit INTEGER, userId TEXT, perUserLimit INTEGER)"""
            )
            c.execute(
                "INSERT OR IGNORE INTO settings (globalLimit, userId, perUserLimit) VALUES (0, NULL, NULL)"
            )
            conn.commit()
        logger.info(
            "Database initialized successfully at %s", settings.db_path
        )
    except sqlite3.OperationalError as e:
        logger.error("Failed to initialize database: %s", str(e))
        raise


def get_db():
    logger.debug("Connecting to database")
    try:
        conn = sqlite3.connect(settings.db_path)
        conn.row_factory = sqlite3.Row
        logger.debug("Database connection established")
        return conn
    except sqlite3.OperationalError as e:
        logger.error("Failed to connect to database: %s", str(e))
        raise


def get_jellyfin_username(userId):
    logger.debug("Fetching username for userId: %s", userId)
    try:
        url = f"{settings.jellyfin_url}/Users/{userId}?api_key={settings.jellyfin_api_key}"
        response = requests.get(url)
        if response.ok:
            user_data = response.json()
            username = user_data.get("Name", f"User_{userId[:8]}")
            logger.info("Fetched username for userId=%s: %s", userId, username)
            return username
        else:
            logger.warning(
                "Failed to fetch username for userId=%s: HTTP %s",
                userId,
                response.status_code,
            )
            return f"User_{userId[:8]}"
    except Exception as e:
        logger.error(
            "Error fetching username for userId=%s: %s", userId, str(e)
        )
        return f"User_{userId[:8]}"


@app.route("/updoot/recommend", methods=["POST"])
def recommend():
    logger.debug("Received /recommend request")
    try:
        data = request.get_json()
        userId = data.get("userId")
        itemId = data.get("itemId")
        if not userId or not itemId:
            logger.error("Missing userId or itemId in recommend request")
            return jsonify({"error": "Missing userId or itemId"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT globalLimit FROM settings WHERE ROWID = 1")
            globalLimit = c.fetchone()
            globalLimit = globalLimit["globalLimit"] if globalLimit else 0
            if globalLimit > 0:
                c.execute("SELECT COUNT(*) as count FROM recommendations")
                total = c.fetchone()["count"]
                if total >= globalLimit:
                    logger.warning(
                        "Global recommendation limit reached: %s/%s",
                        total,
                        globalLimit,
                    )
                    return (
                        jsonify(
                            {"error": "Global recommendation limit reached"}
                        ),
                        403,
                    )

            c.execute(
                "SELECT perUserLimit FROM settings WHERE userId = ?", (userId,)
            )
            userLimit = c.fetchone()
            userLimit = userLimit["perUserLimit"] if userLimit else 0
            if userLimit > 0:
                c.execute(
                    "SELECT COUNT(*) as count FROM recommendations WHERE userId = ?",
                    (userId,),
                )
                userCount = c.fetchone()["count"]
                if userCount >= userLimit:
                    logger.warning(
                        "User %s recommendation limit reached: %s/%s",
                        userId,
                        userCount,
                        userLimit,
                    )
                    return (
                        jsonify(
                            {"error": "User recommendation limit reached"}
                        ),
                        403,
                    )

            c.execute(
                "SELECT * FROM recommendations WHERE userId = ? AND itemId = ?",
                (userId, itemId),
            )
            existing = c.fetchone()
            username = get_jellyfin_username(userId)
            if existing:
                c.execute(
                    "DELETE FROM recommendations WHERE userId = ? AND itemId = ?",
                    (userId, itemId),
                )
                conn.commit()
                logger.info(
                    "Unrecommended: userId=%s, itemId=%s", userId, itemId
                )
                return jsonify({"status": "unrecommended"})
            else:
                c.execute(
                    "INSERT INTO recommendations (userId, itemId, username) VALUES (?, ?, ?)",
                    (userId, itemId, username),
                )
                conn.commit()
                logger.info(
                    "Recommended: userId=%s, itemId=%s, username=%s",
                    userId,
                    itemId,
                    username,
                )
                return jsonify({"status": "recommended"})
    except Exception as e:
        logger.error("Error in /recommend: %s", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/updoot/recommendations", methods=["GET"])
def get_recommendations():
    logger.debug("Received /recommendations request")
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT userId, itemId, username FROM recommendations")
            recommendations = [
                {
                    "userId": row["userId"],
                    "itemId": row["itemId"],
                    "username": row["username"],
                }
                for row in c.fetchall()
            ]
            logger.info("Retrieved %s recommendations", len(recommendations))
            return jsonify(recommendations)
    except Exception as e:
        logger.error("Error in /recommendations: %s", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/updoot/recommendations/<itemId>", methods=["GET"])
def get_recommendations_for_item(itemId):
    logger.debug("Received /recommendations/%s request", itemId)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT userId, itemId, username FROM recommendations WHERE itemId = ?",
                (itemId,),
            )
            recommendations = [
                {
                    "userId": row["userId"],
                    "itemId": row["itemId"],
                    "username": row["username"],
                }
                for row in c.fetchall()
            ]
            logger.info(
                "Retrieved %s recommendations for itemId=%s",
                len(recommendations),
                itemId,
            )
            return jsonify(recommendations)
    except Exception as e:
        logger.error("Error in /recommendations/%s: %s", itemId, str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/updoot/comments", methods=["POST"])
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
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO comments (userId, itemId, username, comment) VALUES (?, ?, ?, ?)",
                (userId, itemId, username, comment),
            )
            conn.commit()
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


@app.route("/updoot/comments/<itemId>", methods=["GET"])
def get_comments_for_item(itemId):
    logger.debug("Received /comments/%s request", itemId)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, userId, itemId, username, comment FROM comments WHERE itemId = ?",
                (itemId,),
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
                "Retrieved %s comments for itemId=%s", len(comments), itemId
            )
            return jsonify(comments)
    except Exception as e:
        logger.error("Error in /comments/%s: %s", itemId, str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/updoot/comments/<int:commentId>", methods=["PUT"])
def edit_comment(commentId):
    logger.debug("Received /comments/%s PUT request", commentId)
    try:
        data = request.get_json()
        userId = data.get("userId")
        comment = data.get("comment")
        if not userId or not comment:
            logger.error("Missing userId or comment in edit_comment request")
            return jsonify({"error": "Missing userId or comment"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT userId FROM comments WHERE id = ?", (commentId,))
            result = c.fetchone()
            if not result:
                logger.warning("Comment not found: id=%s", commentId)
                return jsonify({"error": "Comment not found"}), 404
            if (
                result["userId"] != userId
                and userId not in settings.admin_user_ids
            ):
                logger.warning(
                    "Unauthorized edit attempt: userId=%s, commentId=%s",
                    userId,
                    commentId,
                )
                return jsonify({"error": "Unauthorized"}), 403

            c.execute(
                "UPDATE comments SET comment = ? WHERE id = ?",
                (comment, commentId),
            )
            conn.commit()
            logger.info(
                "Comment edited: userId=%s, commentId=%s", userId, commentId
            )
            return jsonify({"status": "comment edited"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", commentId, str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/updoot/comments/<int:commentId>", methods=["DELETE"])
def delete_comment(commentId):
    logger.debug("Received /comments/%s DELETE request", commentId)
    try:
        data = request.get_json()
        userId = data.get("userId")
        if not userId:
            logger.error("Missing userId in delete_comment request")
            return jsonify({"error": "Missing userId"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT userId FROM comments WHERE id = ?", (commentId,))
            result = c.fetchone()
            if not result:
                logger.warning("Comment not found: id=%s", commentId)
                return jsonify({"error": "Comment not found"}), 404
            if (
                result["userId"] != userId
                and userId not in settings.admin_user_ids
            ):
                logger.warning(
                    "Unauthorized delete attempt: userId=%s, commentId=%s",
                    userId,
                    commentId,
                )
                return jsonify({"error": "Unauthorized"}), 403

            c.execute("DELETE FROM comments WHERE id = ?", (commentId,))
            conn.commit()
            logger.info(
                "Comment deleted: userId=%s, commentId=%s", userId, commentId
            )
            return jsonify({"status": "comment deleted"})
    except Exception as e:
        logger.error("Error in /comments/%s: %s", commentId, str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/updoot/admin/comments", methods=["GET"])
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


@app.route("/updoot/admin/comments/<int:commentId>", methods=["DELETE"])
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


@app.route("/updoot/admin/comments/user/<userId>", methods=["DELETE"])
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


@app.route("/updoot/admin/settings", methods=["GET"])
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


@app.route("/updoot/admin/settings", methods=["POST"])
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


if __name__ == "__main__":
    if not os.path.exists(settings.db_path):
        logger.info("Database not found, initializing")
        init_db()
    app.run(host="0.0.0.0", port=8099)
