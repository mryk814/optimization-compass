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

# Validation tiers from AGENTS.md / docs/adding-knowledge.md.
# tier-a: prose or existing-content correction
# tier-b: Gallery, comparison, relations, or canonical data using existing contracts
# tier-c: executable problem, scenario, generator, renderer, schema, or release change
tier-a:
	uv run python scripts/verify_content.py
	uv run python scripts/verify_licensing.py
	npm --prefix site test -- --run

tier-b:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src
	uv run pytest
	uv run optimization-compass verify-data
	uv run python scripts/verify_content.py
	uv run python scripts/verify_licensing.py
	uv run python scripts/rebuild_dataset.py --stage
	npm --prefix site run parity
	npm --prefix site test -- --run
	npm --prefix site run build

tier-c: tier-b
	npm --prefix site run typecheck
	npm --prefix site run test:e2e
