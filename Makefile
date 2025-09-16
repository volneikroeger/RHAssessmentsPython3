.PHONY: help dev build up down logs shell migrate seed test lint fmt clean install

# Default target
help:
	@echo "Available targets:"
	@echo "  dev      - Start development environment"
	@echo "  build    - Build Docker images"
	@echo "  up       - Start all services"
	@echo "  down     - Stop all services"
	@echo "  logs     - Show logs"
	@echo "  shell    - Open Django shell"
	@echo "  migrate  - Run database migrations"
	@echo "  seed     - Run seed command"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting"
	@echo "  fmt      - Format code"
	@echo "  clean    - Clean up containers and volumes"
	@echo "  install  - Install dependencies with Poetry"

dev: up

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec web python app/manage.py shell

migrate:
	docker-compose exec web python app/manage.py migrate

seed:
	docker-compose exec web python app/manage.py seed_all

test:
	docker-compose exec web pytest app/tests/

lint:
	docker-compose exec web ruff check app/
	docker-compose exec web mypy app/

fmt:
	docker-compose exec web ruff format app/

clean:
	docker-compose down -v
	docker system prune -f

install:
	poetry install

# Local development (without Docker)
local-dev:
	cd app && python manage.py runserver

local-migrate:
	cd app && python manage.py migrate

local-seed:
	cd app && python manage.py seed_all

local-test:
	cd app && pytest tests/

local-lint:
	cd app && ruff check .
	cd app && mypy .

local-fmt:
	cd app && ruff format .

# Production commands
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

# Database backup/restore
backup-db:
	docker-compose exec db pg_dump -U postgres assessments_db > backup.sql

restore-db:
	docker-compose exec -T db psql -U postgres assessments_db < backup.sql