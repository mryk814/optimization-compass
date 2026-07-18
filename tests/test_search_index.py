from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.db import KnowledgeRepository
from optimization_compass.search_index import (
    RetrievalExport,
    SearchIndex,
    evaluate_search_benchmark,
    lexical_tokens,
    load_benchmark_cases,
    search_documents,
)
from optimization_compass.site_export import export_site_data


def test_search_normalization_handles_width_punctuation_and_japanese() -> None:
    assert {"cp", "sat", "論理", "理制", "制約"} <= set(lexical_tokens("ＣＰ－ＳＡＴ 論理制約"))


def test_exported_search_and_retrieval_contracts_are_closed(
    tmp_path: Path, repository: KnowledgeRepository
) -> None:
    export_site_data(tmp_path, repository)
    index = SearchIndex.model_validate_json((tmp_path / "search-index.json").read_bytes())
    retrieval = RetrievalExport.model_validate_json(
        (tmp_path / "retrieval-documents.json").read_bytes()
    )
    entity_types = {document.entity_type for document in index.documents}
    assert {
        "method",
        "problem",
        "implementation",
        "content",
        "case",
        "trace",
        "comparison",
        "source",
        "glossary",
        "failure",
    } <= entity_types
    assert len(index.documents) > 500
    assert (tmp_path / "search-index.json").stat().st_size < 2 * 1024 * 1024
    assert len(retrieval.chunks) > len(index.documents)
    failure_hits = search_documents(index, "noise", entity_types={"failure"})
    assert failure_hits[0].document_id == "failure:structured:FM003"
    assert all(chunk.source_ids for chunk in retrieval.chunks if chunk.authority == "canonical")
    assert any(
        chunk.document_id.startswith("content:") and not chunk.chunk_id.endswith(":overview")
        for chunk in retrieval.chunks
    )
    assert all("frame:" not in chunk.chunk_id for chunk in retrieval.chunks)


def test_alias_ranking_and_representative_benchmark(
    tmp_path: Path, repository: KnowledgeRepository
) -> None:
    export_site_data(tmp_path, repository)
    index = SearchIndex.model_validate_json((tmp_path / "search-index.json").read_bytes())
    hits = search_documents(index, "BO", entity_types={"method"})
    assert hits[0].document_id == "method:M_BAYESIAN_OPT_GP"
    assert "alias" in hits[0].matched_fields
    cases = load_benchmark_cases(Path("data/seeds/search_benchmark.json"))
    report = evaluate_search_benchmark(index, cases)
    assert sum(bool(case["expected_document_ids"]) for case in cases) == 10
    assert report["metrics"]["top_1_relevance"] == 0.8
    assert report["metrics"]["top_3_relevance"] == 1.0
    assert report["metrics"]["expected_entity_recall"] == 1.0
    assert report["metrics"]["zero_result_rate"] == 1 / len(cases)
    assert json.loads((tmp_path / "search-benchmark.json").read_bytes()) == report
