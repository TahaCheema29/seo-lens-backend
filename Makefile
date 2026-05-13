# Makefile for SEO Lens Backend

.PHONY: help install dev run test clean docker-up docker-down docker-logs docker-build

help:
	@echo "Available commands:"
	@echo ""
	@echo "  Development (Local):"
	@echo "    make install        - Install dependencies"
	@echo "    make dev            - Run development server"
	@echo "    make test           - Run tests"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up      - Build & start all services"
	@echo "    make docker-down    - Stop all services"
	@echo "    make docker-logs    - View logs (follow mode)"
	@echo "    make docker-build   - Rebuild images"
	@echo ""
	@echo "  Database (Docker):"
	@echo "    make docker-migrate        - Apply migrations (for new team members)"
	@echo "    make docker-migrate-create - Create new migration (after model changes)"
	@echo "    make docker-migrate-init   - Initialize from scratch"
	@echo "    make docker-db-tables      - List database tables"
	@echo "    make docker-db-shell       - Open database shell"
	@echo "    make docker-db-reset        - Reset database"
	@echo ""
	@echo "  Database (Local - without Docker):"
	@echo "    make migrate        - Run migrations"
	@echo "    make create-migrate - Create new migration"
	@echo "    make init-db        - Initialize database"

install:
	pip install -r requirements.txt
	playwright install chromium

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

# Database Commands (LOCAL - for development without Docker)
migrate:
	python -m scripts.migrate migrate

create-migrate:
	python -m scripts.migrate create "$(MSG)"

init-db:
	python -m scripts.migrate init
	python -m scripts.migrate create "initial migration"
	python -m scripts.migrate migrate

# Database Commands (DOCKER - for Docker environment)
# Use this when: Cloning repo, pulling new migrations, or fresh start
docker-migrate:
	docker compose exec app alembic upgrade head

# Use this when: You changed models and need NEW migration file
docker-migrate-create:
	docker compose exec app alembic revision --autogenerate -m "$(MSG)"

# Use this when: Fresh project, no migration files exist
docker-migrate-init:
	docker compose exec app sh -c "alembic revision --autogenerate -m 'initial' && alembic upgrade head"

# Database utilities
docker-db-shell:
	docker compose exec postgres psql -U postgres -d seo_lens

docker-db-tables:
	docker compose exec postgres psql -U postgres -d seo_lens -c "\dt"

# Reset database (drop all tables and re-run migrations)
docker-db-reset:
	docker compose exec app alembic downgrade base
	docker compose exec app alembic upgrade head

docker-up:
	cp .env.docker .env.local 2>/dev/null || true
	docker-compose up -d --build
	@echo ""
	@echo "✅ Services starting..."
	@echo "   App: http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis: localhost:6379"
	@echo ""
	@echo "📋 View logs: make docker-logs"
	@echo "🛑 Stop services: make docker-down"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build --no-cache

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache