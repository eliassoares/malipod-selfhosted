.PHONY: install lint fix format typecheck security audit check test test-auth test-device test-subscriptions test-episodes test-lists run up down logs build verify verify-auth verify-device verify-subscriptions verify-episodes verify-lists clean help

install: ## Install dependencies and pre-commit hooks
	uv sync
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

lint: ## Run linter
	uv run ruff check .

fix: ## Run linter with auto-fix
	uv run ruff check . --fix

format: ## Run formatter
	uv run ruff format .

typecheck: ## Run type checker (strict)
	uv run mypy .

security: ## Run security scan (bandit)
	uv run bandit -r . -c pyproject.toml

audit: ## Run dependency vulnerability check
	uv run pip-audit --ignore-vuln GHSA-58qw-9mgm-455v

check: lint typecheck security audit ## Run all checks

test: ## Run automated tests with isolated SQLite configuration
	SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest

test-auth: ## Run only authentication and localization tests
	SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_user_validation.py tests/unit/test_auth_service.py tests/unit/test_localization.py tests/integration/test_auth_pages.py tests/integration/test_auth_sessions.py tests/integration/test_profile_page.py tests/contract/test_auth_api.py -q

test-device: ## Run only Device API tests
	SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_device_service.py tests/contract/test_device_api.py tests/integration/test_device_updates_api.py -q

test-subscriptions: ## Run only Subscriptions API tests
	SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_subscription_formats.py tests/unit/test_subscription_service.py tests/contract/test_subscriptions_api.py tests/integration/test_subscriptions_sync_api.py -q

test-episodes: ## Run only Episodes API tests and compatibility checks
	SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_episode_service.py tests/contract/test_episodes_api.py tests/integration/test_episodes_sync_api.py tests/unit/test_device_service.py tests/integration/test_device_updates_api.py -q

test-lists: ## Run only Podcast Lists API tests
	SECRET_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATABASE_URL=sqlite+aiosqlite:///./test.db TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db uv run pytest tests/unit/test_podcast_list_service.py tests/contract/test_lists_api.py tests/integration/test_lists_api_flow.py -q

run: ## Run the FastAPI application locally
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

build: ## Build the Docker image
	docker compose build

up: build ## Start the stack (app + postgres)
	docker compose up -d

down: ## Stop the stack
	docker compose down --remove-orphans

logs: ## Tail stack logs
	docker compose logs -f app db

verify: check test ## Run full local verification

verify-auth: check test-auth ## Run auth feature verification

verify-device: check test-device ## Run Device API verification

verify-subscriptions: check test-subscriptions ## Run Subscriptions API verification

verify-episodes: check test-episodes ## Run Episodes API verification

verify-lists: check test-lists ## Run Podcast Lists API verification

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
