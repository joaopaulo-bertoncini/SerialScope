.PHONY: help install test lint format clean docker-build docker-run

help:
	@echo "Debug Studio - Makefile Commands"
	@echo ""
	@echo "  make install      - Install dependencies and package"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

test:
	PYTHONPATH="" pytest --cov=serialscope --cov-report=term-missing

lint:
	ruff check serialscope tests
	mypy serialscope --ignore-missing-imports || true

format:
	black serialscope tests
	ruff check --fix serialscope tests

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
