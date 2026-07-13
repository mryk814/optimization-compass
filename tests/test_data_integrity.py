from optimization_compass.db import KnowledgeRepository


def test_knowledge_base_integrity(repository: KnowledgeRepository) -> None:
    result = repository.verify()
    assert result["ok"] is True
    assert result["foreign_key_violations"] == 0
    assert result["failed_release_checks"] == 0
    assert result["total_release_checks"] >= 12
