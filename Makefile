# RCD² Automation Makefile

.PHONY: help install run test lint clean docker-build docker-run

PYTHON := python3
VENV := venv
BIN := $(VENV)/bin

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Create venv and install dependencies
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e .[dev]

run: ## Run the FastAPI server locally
	RCD2_API_KEY=dev-key-123 $(BIN)/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

test: ## Run tests with coverage
	RCD2_API_KEY=dev-key-123 $(BIN)/pytest tests/ -v --cov=backend --cov-report=term-missing

lint: ## Run code quality checks (black, flake8, mypy, isort)
	$(BIN)/black backend/ tests/
	$(BIN)/isort backend/ tests/
	$(BIN)/flake8 backend/ tests/
	$(BIN)/mypy backend/

clean: ## Clean up build artifacts and cache
	rm -rf $(VENV)
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t rcd2:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --name rcd2-container --rm rcd2:latest

demo: ## Run the demo scenario script
	RCD2_API_KEY=dev-key-123 $(BIN)/python examples/demo_scenario.py
