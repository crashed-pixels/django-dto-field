SHELL:=/usr/bin/env bash

.PHONY: unit
unit:
	uv run pytest

.PHONY: typing
typing:
	uv run mypy src

.PHONY: lint
lint:
	uv run ruff check src tests
	uv run ruff check --select D100,D101,D104 src
	uv run ruff format --check src tests
	uv run flake8 src --select=WPS

.PHONY: format
format:
	uv run ruff check --fix src tests
	uv run ruff format src tests

.PHONY: test
test: unit

.PHONY: clean
clean: 
	rm -fr .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage

.PHONY: all-checks
all-checks: clean lint typing test
