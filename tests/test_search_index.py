from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import optimization_compass.site_export as site_export
from optimization_compass.content_models import load_content
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
    tmp_path: Path, repository: KnowledgeRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_root = Path(__file__).parents[1]
    content_directory = tmp_path / "content"
    shutil.copytree(repository_root / "content", content_directory)
    shutil.copytree(repository_root / "site/public/media", tmp_path / "site/public/media")
    draft = (content_directory / "concepts/convexity.md").read_text(encoding="utf-8")
    draft = draft.replace(
        "content_id: concept.convexity",
        "content_id: concept.test-draft-exclusion",
        1,
    ).replace("status: published", "status: draft", 1)
    (content_directory / "concepts/test-draft-exclusion.md").write_text(
        draft,
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(site_export, "CONTENT_DIRECTORY", content_directory)

    export_site_data(tmp_path, repository)
    index = SearchIndex.model_validate_json((tmp_path / "search-index.json").read_bytes())
    retrieval = RetrievalExport.model_validate_json(
        (tmp_path / "retrieval-documents.json").read_bytes()
    )
    entity_links = json.loads((tmp_path / "entity-links.json").read_bytes())
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
    draft_ids = {
        page.content_id for page in load_content(content_directory) if page.status == "draft"
    }
    assert draft_ids == {"concept.test-draft-exclusion"}
    assert not draft_ids & {
        document.entity_id for document in index.documents if document.entity_type == "content"
    }
    assert not any(
        chunk.document_id in {f"content:{content_id}" for content_id in draft_ids}
        for chunk in retrieval.chunks
    )
    assert not draft_ids & {
        item["entity_id"] for item in entity_links["entities"] if item["entity_type"] == "content"
    }


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
