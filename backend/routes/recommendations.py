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
        user_id = data.get("userId")
        item_id = data.get("itemId")
        if not user_id or not item_id:
            logger.error(
                "Missing user_id or item_id in recommendations request"
            )
            return jsonify({"error": "Missing userId or itemId"}), 400

        global_limit = (
            db_session.scalars(select(Setting.global_limit)).one_or_none() or 0
        )
        if global_limit > 0:
            total = db_session.scalar(
                select(func.count()).select_from(Recommendation)
            )
            if total >= global_limit:
                logger.warning(
                    "Global recommendation limit reached: %s/%s",
                    total,
                    global_limit,
                )
                return (
                    jsonify({"error": "Global recommendation limit reached"}),
                    403,
                )

        user_limit = (
            db_session.scalars(
                select(UserSetting.user_limit).where(
                    UserSetting.user_id == user_id
                )
            ).one_or_none()
            or 0
        )
        if user_limit > 0:
            user_count = db_session.scalar(
                select(func.count())
                .select_from(Recommendation)
                .where(Recommendation.user_id == user_id)
            )
            if user_count >= user_limit:
                logger.warning(
                    "User %s recommendation limit reached: %s/%s",
                    user_id,
                    user_count,
                    user_limit,
                )
                return (
                    jsonify({"error": "User recommendation limit reached"}),
                    403,
                )

        existing = db_session.get(Recommendation, (user_id, item_id))
        username = get_jellyfin_username(user_id)
        if existing:
            db_session.delete(existing)
            logger.info(
                "Unrecommended: user_id=%s, item_id=%s", user_id, item_id
            )
            return jsonify({"status": "unrecommended"})
        else:
            db_session.add(
                Recommendation(
                    user_id=user_id, item_id=item_id, username=username
                )
            )
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
        rows = db_session.scalars(select(Recommendation)).all()
        recommendations = [
            {
                "userId": row.user_id,
                "itemId": row.item_id,
                "username": row.username,
            }
            for row in rows
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
        rows = db_session.scalars(
            select(Recommendation).where(Recommendation.item_id == item_id)
        ).all()
        recommendations = [
            {
                "userId": row.user_id,
                "itemId": row.item_id,
                "username": row.username,
            }
            for row in rows
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
