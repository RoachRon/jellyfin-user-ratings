#!/bin/sh
set -e

python -c "from backend.db import init_db; init_db()"
exec gunicorn --bind 0.0.0.0:${PORT} backend:APP
