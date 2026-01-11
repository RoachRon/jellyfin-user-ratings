FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src/
COPY web/ /app/web/

# Allow importing the python package from /app/src
ENV PYTHONPATH=/app/src

# Default envs (all overridable)
ENV BACKEND_PORT=8099 \
    DB_PATH=/data/recommendations.db \
    BACKEND_PATH=/updoot \
    UPDOOT_SRC=/updoot/assets/updoot.js \
    VERSION=1

EXPOSE 8099

CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${BACKEND_PORT} updoot_service.backendupdoot:app"]

