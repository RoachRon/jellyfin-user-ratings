from socket import error as socket_error

from sqlalchemy.exc import SQLAlchemyError

from backend import APP
from backend.db import db_session
from backend.logger import logger


@APP.teardown_request
def run_request_teardown(exception=None):
    if exception and not isinstance(exception, socket_error):
        logger.exception("Backend exception: %s", exception)
    try:
        db_session.commit()
    except SQLAlchemyError as db_exc:
        db_session.rollback()
        logger.exception(
            "Database session rolled back due to exception: %s", db_exc
        )


@APP.teardown_appcontext
def run_app_teardown(_exception=None):
    db_session.remove()
