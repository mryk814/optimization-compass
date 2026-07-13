from __future__ import annotations

from pathlib import Path

import pytest

from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine


@pytest.fixture(scope="session")
def database_path() -> Path:
    return Path(__file__).parents[1] / "src/optimization_compass/resources/knowledge.sqlite"


@pytest.fixture()
def repository(database_path: Path) -> KnowledgeRepository:
    return KnowledgeRepository(database_path)


@pytest.fixture()
def engine(repository: KnowledgeRepository) -> RecommendationEngine:
    return RecommendationEngine(repository)
