.PHONY: install serve test lint format typecheck verify check

install:
	uv sync --all-extras

serve:
	uv run optimization-compass serve

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

verify:
	uv run optimization-compass verify-data

check: lint typecheck test verify
