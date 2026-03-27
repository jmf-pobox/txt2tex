.PHONY: lint format format-check type type-pyright test test-cov check check-cov build clean

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

type:
	uv run mypy src/txt2tex tests

type-pyright:
	uv run pyright

test:
	uv run pytest $(ARGS)

test-cov:
	uv run pytest --cov=src/txt2tex --cov-report=term-missing --cov-report=html $(ARGS)

check: lint format-check type type-pyright test

check-cov: lint format-check type type-pyright test-cov

build:
	uv build
	uvx twine check dist/*

clean:
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
