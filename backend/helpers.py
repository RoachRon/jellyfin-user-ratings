import requests

from backend.logger import logger
from backend.settings import settings


def get_jellyfin_username(user_id):
    logger.debug("Fetching username for user_id: %s", user_id)
    try:
        url = f"{settings.jellyfin_url}/Users/{user_id}?api_key={settings.jellyfin_api_key}"
        response = requests.get(url)
        if response.ok:
            user_data = response.json()
            username = user_data.get("Name", f"User_{user_id[:8]}")
            logger.info(
                "Fetched username for user_id=%s: %s", user_id, username
            )
            return username
        else:
            logger.warning(
                "Failed to fetch username for user_id=%s: HTTP %s",
                user_id,
                response.status_code,
            )
            return f"User_{user_id[:8]}"
    except Exception as e:
        logger.error(
            "Error fetching username for user_id=%s: %s", user_id, str(e)
        )
        return f"User_{user_id[:8]}"
