from flask import Blueprint, jsonify, request

from backend.db import get_db
from backend.helpers import get_jellyfin_username
from backend.logger import logger

RECOMMENDATIONS_BP = Blueprint(
    "recommendations", __name__, url_prefix="/recommendations"
)


@RECOMMENDATIONS_BP.route("/", methods=["POST"])
def add_recommendation():
    logger.debug("Received /recommendations request")
    try:
        data = request.get_json()
        user_id = data.get("userId")
        item_id = data.get("itemId")
        if not user_id or not item_id:
            logger.error(
                "Missing user_id or item_id in recommendations request"
            )
            return jsonify({"error": "Missing userId or itemId"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT globalLimit FROM settings WHERE ROWID = 1")
            global_limit = c.fetchone()
            global_limit = global_limit["globalLimit"] if global_limit else 0
            if global_limit > 0:
                c.execute("SELECT COUNT(*) as count FROM recommendations")
                total = c.fetchone()["count"]
                if total >= global_limit:
                    logger.warning(
                        "Global recommendation limit reached: %s/%s",
                        total,
                        global_limit,
                    )
                    return (
                        jsonify(
                            {"error": "Global recommendation limit reached"}
                        ),
                        403,
                    )

            c.execute(
                "SELECT perUserLimit FROM settings WHERE userId = ?",
                (user_id,),
            )
            user_limit = c.fetchone()
            user_limit = user_limit["perUserLimit"] if user_limit else 0
            if user_limit > 0:
                c.execute(
                    "SELECT COUNT(*) as count FROM recommendations WHERE userId = ?",
                    (user_id,),
                )
                user_count = c.fetchone()["count"]
                if user_count >= user_limit:
                    logger.warning(
                        "User %s recommendation limit reached: %s/%s",
                        user_id,
                        user_count,
                        user_limit,
                    )
                    return (
                        jsonify(
                            {"error": "User recommendation limit reached"}
                        ),
                        403,
                    )

            c.execute(
                "SELECT * FROM recommendations WHERE userId = ? AND itemId = ?",
                (user_id, item_id),
            )
            existing = c.fetchone()
            username = get_jellyfin_username(user_id)
            if existing:
                c.execute(
                    "DELETE FROM recommendations WHERE userId = ? AND itemId = ?",
                    (user_id, item_id),
                )
                conn.commit()
                logger.info(
                    "Unrecommended: user_id=%s, item_id=%s", user_id, item_id
                )
                return jsonify({"status": "unrecommended"})
            else:
                c.execute(
                    "INSERT INTO recommendations (userId, itemId, username) VALUES (?, ?, ?)",
                    (user_id, item_id, username),
                )
                conn.commit()
                logger.info(
                    "Recommended: user_id=%s, item_id=%s, username=%s",
                    user_id,
                    item_id,
                    username,
                )
                return jsonify({"status": "recommended"})
    except Exception as e:
        logger.error("Error in /recommendations: %s", str(e))
        return jsonify({"error": str(e)}), 500


@RECOMMENDATIONS_BP.route("/", methods=["GET"])
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


@RECOMMENDATIONS_BP.route("/<item_id>", methods=["GET"])
def get_recommendations_for_item(item_id):
    logger.debug("Received /recommendations/%s request", item_id)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT userId, itemId, username FROM recommendations WHERE itemId = ?",
                (item_id,),
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
                "Retrieved %s recommendations for item_id=%s",
                len(recommendations),
                item_id,
            )
            return jsonify(recommendations)
    except Exception as e:
        logger.error("Error in /recommendations/%s: %s", item_id, str(e))
        return jsonify({"error": str(e)}), 500
