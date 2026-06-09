.PHONY: dev db-only migrate backend frontend lint test

# Start everything
dev:
	docker compose up

# Only the database (useful when running backend natively)
db-only:
	docker compose up db

# Run Alembic migrations
migrate:
	cd backend && uv run alembic upgrade head

# Run backend locally (without Docker)
backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

# Run frontend locally
frontend:
	cd frontend && npm run dev

# Lint backend
lint:
	cd backend && uv run ruff check . && uv run mypy app

# Run all tests
test:
	cd backend && uv run pytest tests/ -v

# Reset DB volumes (destructive!)
db-reset:
	docker compose down -v
	docker compose up db -d
