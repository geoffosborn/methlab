.PHONY: dev dev-frontend dev-backend build migrate deploy lint test clean

# Development — run both services
dev:
	$(MAKE) -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend/apps/api && uv run uvicorn app.main:app --host 127.0.0.1 --port 8020 --reload

# Build frontend for production
build:
	cd frontend && npm ci && npm run build

# Run database migrations
migrate:
	cd backend && uv run python scripts/run_migrations.py

# Deploy to production
deploy:
	bash infra/deploy.sh

# Lint both stacks
lint:
	cd frontend && npx eslint .
	cd backend && uv run ruff check .

# Test both stacks
test:
	cd frontend && npm test
	cd backend && uv run pytest

# Docker dev stack
up:
	docker compose up -d

down:
	docker compose down

# Install dependencies for both
install:
	cd frontend && npm ci
	cd backend && uv sync

clean:
	cd frontend && rm -rf .next node_modules
	cd backend && rm -rf .venv
