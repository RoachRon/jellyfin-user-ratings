import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    filename="./flask-app.log",
    filemode="a",
)
logger = logging.getLogger(__name__)
