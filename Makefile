.PHONY: help install install-dev sync lock test test-cov test-fast lint format clean runserver migrate makemigrations shell superuser collectstatic docker-up docker-down docker-logs docker-build docker-ps celery celery-beat celery-flower seaweedfs-auth

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make sync             - Sync dependencies from lock file"
	@echo "  make lock             - Lock dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make test-fast        - Run tests in parallel"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo "  make clean            - Clean temporary files"
	@echo "  make runserver        - Run Django development server"
	@echo "  make migrate          - Run database migrations"
	@echo "  make makemigrations   - Create new migrations"
	@echo "  make shell            - Open Django shell"
	@echo "  make superuser        - Create Django superuser"
	@echo "  make collectstatic    - Collect static files"
	@echo "  make docker-up        - Start Docker services"
	@echo "  make docker-down      - Stop Docker services"
	@echo "  make docker-logs      - View Docker logs"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-ps        - Show Docker container status"
	@echo "  make celery           - Run Celery worker"
	@echo "  make celery-beat      - Run Celery beat scheduler"
	@echo "  make celery-flower    - Run Flower (Celery monitoring)"
	@echo "  make seaweedfs-auth   - Create SeaweedFS S3 access keys"

# Installation
install:
	uv sync --no-dev

install-dev:
	uv sync

sync:
	uv sync

lock:
	uv lock

# Testing
test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=html --cov-report=term

test-fast:
	uv run pytest -n auto

# Code quality
lint:
	@echo "Running linters..."
	@if command -v ruff > /dev/null; then \
		uv run ruff check app/; \
	else \
		echo "ruff not installed, skipping..."; \
	fi
	@if command -v mypy > /dev/null; then \
		uv run mypy app/ || true; \
	else \
		echo "mypy not installed, skipping..."; \
	fi

format:
	@echo "Formatting code..."
	@if command -v ruff > /dev/null; then \
		uv run ruff format app/; \
	else \
		echo "ruff not installed, skipping..."; \
	fi
	@if command -v black > /dev/null; then \
		uv run black app/ || true; \
	else \
		echo "black not installed, skipping..."; \
	fi

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf .mypy_cache
	rm -rf .ruff_cache

# Django commands
runserver:
	uv run python app/manage.py runserver

migrate:
	uv run python app/manage.py migrate

makemigrations:
	uv run python app/manage.py makemigrations

shell:
	uv run python app/manage.py shell

superuser:
	uv run python app/manage.py createsuperuser

collectstatic:
	uv run python app/manage.py collectstatic --noinput

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

docker-ps:
	docker-compose ps

# Docker VPS specific
docker-up-vps:
	docker-compose -f docker-compose.vps.yml up -d

docker-down-vps:
	docker-compose -f docker-compose.vps.yml down

docker-logs-vps:
	docker-compose -f docker-compose.vps.yml logs -f

# Docker GPU specific
docker-up-gpu:
	docker-compose -f docker-compose.gpu.yml up -d

docker-down-gpu:
	docker-compose -f docker-compose.gpu.yml down

docker-logs-gpu:
	docker-compose -f docker-compose.gpu.yml logs -f

# Celery commands
celery:
	uv run celery -A config.celery worker --loglevel=info

celery-beat:
	uv run celery -A config.celery beat --loglevel=info

celery-flower:
	uv run celery -A config.celery flower

# SeaweedFS commands
seaweedfs-auth:
	@echo "Creating SeaweedFS S3 access keys..."
	@uv run python scripts/setup_seaweedfs_auth.py --endpoint ${ENDPOINT:-http://localhost:8333} --output-format env
