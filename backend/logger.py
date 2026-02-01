import logging
import sys

from backend.settings import settings

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
LOG_FILE = "./flask-app.log"


def _configure_logging() -> None:
    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(LOG_FILE, mode="a")

    logging.basicConfig(
        level=settings.log_level,
        format=LOG_FORMAT,
        handlers=[stream_handler, file_handler],
    )


_configure_logging()
logger = logging.getLogger(__name__)
