from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from backend.db import db_session
from backend.helpers import get_jellyfin_username
from backend.logger import logger
from backend.models import Recommendation, Setting, UserSetting

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

        globalLimit = (
            db_session.scalars(select(Setting.globalLimit)).one_or_none() or 0
        )
        if globalLimit > 0:
            total = db_session.scalar(
                select(func.count()).select_from(Recommendation)
            )
            if total >= globalLimit:
                logger.warning(
                    "Global recommendation limit reached: %s/%s",
                    total,
                    globalLimit,
                )
                return (
                    jsonify({"error": "Global recommendation limit reached"}),
                    403,
                )

        userLimit = (
            db_session.scalars(
                select(UserSetting.limit).where(UserSetting.userId == userId)
            ).one_or_none()
            or 0
        )
        if userLimit > 0:
            userCount = db_session.scalar(
                select(func.count())
                .select_from(Recommendation)
                .where(Recommendation.userId == userId)
            )
            if userCount >= userLimit:
                logger.warning(
                    "User %s recommendation limit reached: %s/%s",
                    userId,
                    userCount,
                    userLimit,
                )
                return (
                    jsonify({"error": "User recommendation limit reached"}),
                    403,
                )

        existing = db_session.get(Recommendation, (userId, itemId))
        username = get_jellyfin_username(userId)
        if existing:
            db_session.delete(existing)
            logger.info("Unrecommended: userId=%s, itemId=%s", userId, itemId)
            return jsonify({"status": "unrecommended"})
        else:
            db_session.add(
                Recommendation(userId=userId, itemId=itemId, username=username)
            )
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
        rows = db_session.scalars(select(Recommendation)).all()
        recommendations = [
            {
                "userId": row.userId,
                "itemId": row.itemId,
                "username": row.username,
            }
            for row in rows
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
        rows = db_session.scalars(
            select(Recommendation).where(Recommendation.itemId == itemId)
        ).all()
        recommendations = [
            {
                "userId": row.userId,
                "itemId": row.itemId,
                "username": row.username,
            }
            for row in rows
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
