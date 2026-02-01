.PHONY: help dev-docker dev-docker-down dev-flask init-db

help:
	@echo "Targets:"
	@echo "  dev-docker       Start Jellyfin + Caddy (Docker)"
	@echo "  dev-docker-down  Stop Jellyfin + Caddy (Docker)"
	@echo "  dev-flask        Run Flask in debug mode (host)"
	@echo "  init-db          Initialize the SQLite DB"

dev-docker:
	docker compose -f docker-compose.local.yml up -d

dev-docker-down:
	docker compose -f docker-compose.local.yml down

init-db:
	python -c "from backend.db import init_db; init_db()"

dev-flask: init-db
	poetry run python -m flask --app backend run --host 0.0.0.0 --port 8099 --debug
