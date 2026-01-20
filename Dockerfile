FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    DB_PATH=/data/recommendations.db \
    PORT=8099

WORKDIR /app

# Install Poetry and dependencies
RUN pip install pipx
RUN pipx install poetry==2.2.1
ENV PATH="/root/.local/bin:${PATH}"
COPY pyproject.toml poetry.lock /app/
RUN poetry install \
    --no-root \
    --only main \
    --no-interaction \
    --no-ansi

COPY backend/ /app/backend/
COPY frontend/src/ /app/frontend/src/

EXPOSE ${PORT}

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} backend:APP"]
