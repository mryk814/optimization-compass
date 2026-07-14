.PHONY: install serve test lint format typecheck verify dataset-stage check

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

dataset-stage:
	uv run python scripts/rebuild_dataset.py --stage

check: lint typecheck test verify dataset-stage
