import requests

from backend.logger import logger
from backend.settings import settings


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
