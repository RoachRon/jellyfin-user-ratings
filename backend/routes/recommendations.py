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
        userId = data.get("userId")
        itemId = data.get("itemId")
        if not userId or not itemId:
            logger.error("Missing userId or itemId in recommendations request")
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


@RECOMMENDATIONS_BP.route("/<itemId>", methods=["GET"])
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
