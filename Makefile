.PHONY: install serve test lint format typecheck verify dataset-stage check tier-a tier-b tier-c

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

# Validation tiers delegate to the shared cross-platform authority
# (src/optimization_compass/validation_tasks.py); do not list commands here.
tier-a:
	uv run optimization-compass validate tier-a

tier-b:
	uv run optimization-compass validate tier-b

tier-c:
	uv run optimization-compass validate tier-c
