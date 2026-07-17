from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Self, cast
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from optimization_compass.db import KnowledgeRepository, split_ids
from optimization_compass.entity_links import EntityLinkIndex, LinkedEntity

SearchIntent = Literal[
    "classify_problem",
    "understand_method",
    "find_implementation",
    "compare_visualize",
    "check_evidence",
    "find_case",
]
SearchEntityType = Literal[
    "case",
    "comparison",
    "content",
    "feature",
    "feature_value",
    "glossary",
    "implementation",
    "journey",
    "method",
    "problem",
    "scenario",
    "source",
    "trace",
    "view",
]
SearchField = Literal["canonical_label", "alias", "title", "summary", "keyword", "related"]

FIELD_WEIGHTS: dict[SearchField, int] = {
    "canonical_label": 120,
    "alias": 105,
    "title": 90,
    "summary": 45,
    "keyword": 55,
    "related": 30,
}

INTENT_BY_TYPE: dict[SearchEntityType, tuple[SearchIntent, ...]] = {
    "case": ("find_case", "classify_problem"),
    "comparison": ("compare_visualize",),
    "content": ("understand_method",),
    "feature": ("classify_problem",),
    "feature_value": ("classify_problem",),
    "glossary": ("understand_method", "classify_problem"),
    "implementation": ("find_implementation",),
    "journey": ("find_case", "understand_method", "compare_visualize"),
    "method": ("understand_method",),
    "problem": ("classify_problem",),
    "scenario": ("compare_visualize", "understand_method"),
    "source": ("check_evidence",),
    "trace": ("compare_visualize", "understand_method"),
    "view": ("classify_problem", "compare_visualize"),
}

_PUNCTUATION = re.compile(r"[\s\-_‐‑‒–—―/・,、。:：;；()（）\[\]{}]+", re.UNICODE)
_CJK_RUN = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]+", re.UNICODE)
_WORD = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*", re.UNICODE)
_STOP_TOKENS = {
    "あり",
    "いる",
    "から",
    "こと",
    "した",
    "する",
    "たい",
    "でき",
    "です",
    "とは",
    "ない",
    "ます",
    "まで",
    "もの",
    "最適",
    "適化",
    "手法",
    "方法",
    "問題",
}
_HTML_TAG = re.compile(r"<[^>]+>")
_CONTENT_SECTION = re.compile(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>(.*?)(?=<h2 id=|\Z)', re.DOTALL)
_CANONICAL_ROUTE = re.compile(
    r"^/(?:compare|gallery|learn|map|methods|search|sources|theater|traces)(?:[/?]|$)"
)


class SearchContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SearchFields(SearchContractModel):
    canonical_label: list[str] = Field(default_factory=list)
    alias: list[str] = Field(default_factory=list)
    title: list[str] = Field(default_factory=list)
    summary: list[str] = Field(default_factory=list)
    keyword: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)


class SearchDocument(SearchContractModel):
    document_id: str = Field(min_length=3)
    entity_type: SearchEntityType
    entity_id: str = Field(min_length=1)
    canonical_route: str = Field(min_length=1)
    external_url: str | None = None
    title_ja: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    summary: str = ""
    intents: list[SearchIntent] = Field(min_length=1)
    domains: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    related_document_ids: list[str] = Field(default_factory=list)
    last_reviewed: str | None = None
    content_status: str = "published"
    search_visibility: Literal["public"] = "public"
    fields: SearchFields
    tokens: SearchFields

    @field_validator("canonical_route")
    @classmethod
    def validate_route(cls, value: str) -> str:
        if value.startswith("//") or "#" in value or _CANONICAL_ROUTE.match(value) is None:
            raise ValueError("canonical_route must target a registered HashRouter route family")
        return value


class SearchIndex(SearchContractModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    normalization: dict[str, str]
    ranking_policy: dict[SearchField, int]
    documents: list[SearchDocument]

    @model_validator(mode="after")
    def validate_documents(self) -> Self:
        ids = [document.document_id for document in self.documents]
        if ids != sorted(ids):
            raise ValueError("search documents must be sorted by document_id")
        if len(ids) != len(set(ids)):
            raise ValueError("search document IDs must be unique")
        known = set(ids)
        for document in self.documents:
            missing = set(document.related_document_ids) - known
            if missing:
                raise ValueError(
                    f"search document {document.document_id} has dangling relations: "
                    + ", ".join(sorted(missing))
                )
        return self


class RetrievalChunk(SearchContractModel):
    chunk_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    relation_context: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    dataset_version: str = Field(min_length=1)
    license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    attribution: str = Field(min_length=1)
    authority: Literal["canonical", "generated_from_canonical"]


class RetrievalExport(SearchContractModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    chunking_policy: dict[str, str]
    chunks: list[RetrievalChunk]

    @model_validator(mode="after")
    def validate_chunks(self) -> Self:
        ids = [chunk.chunk_id for chunk in self.chunks]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise ValueError("retrieval chunk IDs must be unique and sorted")
        return self


class SearchHit(SearchContractModel):
    document_id: str
    score: int
    matched_fields: list[SearchField]


def normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _PUNCTUATION.sub(" ", normalized).strip()


def lexical_tokens(value: str) -> list[str]:
    normalized = normalize_search_text(value)
    tokens = set(_WORD.findall(normalized))
    tokens.update(part for part in normalized.split() if len(part) > 1)
    for run in _CJK_RUN.findall(normalized):
        if len(run) == 1:
            tokens.add(run)
        else:
            tokens.update(run[index : index + 2] for index in range(len(run) - 1))
    return sorted(tokens - _STOP_TOKENS)


def search_documents(
    index: SearchIndex,
    query: str,
    *,
    entity_types: set[SearchEntityType] | None = None,
    intents: set[SearchIntent] | None = None,
) -> list[SearchHit]:
    normalized_query = normalize_search_text(query)
    query_tokens = set(lexical_tokens(query))
    if not normalized_query:
        return []
    hits: list[SearchHit] = []
    for document in index.documents:
        if entity_types and document.entity_type not in entity_types:
            continue
        if intents and not intents.intersection(document.intents):
            continue
        score = 0
        matched: list[SearchField] = []
        for field, weight in FIELD_WEIGHTS.items():
            values = getattr(document.fields, field)
            tokens = set(getattr(document.tokens, field))
            normalized_values = [normalize_search_text(value) for value in values]
            field_score = 0
            if normalized_query in normalized_values:
                field_score = {
                    "canonical_label": 6_000,
                    "alias": 5_500,
                    "title": 5_000,
                }.get(field, 4_000) + weight
            elif len(normalized_query) >= 3 and any(
                value.startswith(normalized_query) for value in normalized_values
            ):
                field_score = 2_500 + weight
            elif len(normalized_query) >= 3 and any(
                normalized_query in value for value in normalized_values
            ):
                field_score = 1_000 + weight
            else:
                overlap = len(query_tokens.intersection(tokens))
                if overlap:
                    field_score = weight + min(overlap, 6) * 4
            if field_score:
                score += field_score
                matched.append(field)
        if score:
            hits.append(
                SearchHit(document_id=document.document_id, score=score, matched_fields=matched)
            )
    type_priority = {
        "method": 0,
        "problem": 1,
        "case": 2,
        "implementation": 3,
        "journey": 4,
        "content": 5,
        "glossary": 6,
        "comparison": 7,
        "scenario": 8,
        "trace": 9,
        "source": 10,
        "feature": 11,
        "feature_value": 12,
        "view": 13,
    }
    document_type = {document.document_id: document.entity_type for document in index.documents}
    return sorted(
        hits,
        key=lambda hit: (
            -hit.score,
            type_priority[document_type[hit.document_id]],
            hit.document_id,
        ),
    )


def build_search_artifacts(
    repository: KnowledgeRepository,
    *,
    dataset_version: str,
    generated_at: datetime,
    entity_links: EntityLinkIndex,
    learning_graph: dict[str, Any],
    content_index: dict[str, Any],
    gallery_index: dict[str, Any],
    comparison_index: dict[str, Any],
    scenario_index: dict[str, Any],
    source_index: dict[str, Any],
) -> tuple[SearchIndex, RetrievalExport]:
    aliases = _aliases_by_target(learning_graph)
    metadata = _repository_metadata(repository)
    metadata.update(
        _artifact_metadata(
            content_index, gallery_index, comparison_index, scenario_index, source_index
        )
    )
    source_keys = {str(source["source_id"]) for source in source_index["sources"]}
    entity_keys = {(entity.entity_type, entity.entity_id) for entity in entity_links.entities}
    documents: list[SearchDocument] = []
    for entity in entity_links.entities:
        key = (entity.entity_type, entity.entity_id)
        alias = aliases.get(key, {})
        item = metadata.get(key, {})
        related_ids = sorted(
            f"{relation.target_type}:{relation.target_id}"
            for relation in entity.relations
            if (relation.target_type, relation.target_id) in entity_keys
        )
        source_ids = sorted(
            set(item.get("source_ids", []))
            | {
                relation.target_id
                for relation in entity.relations
                if relation.target_type == "source"
            }
        )
        missing_sources = set(source_ids) - source_keys
        if missing_sources:
            raise ValueError(
                f"search document {entity.entity_type}:{entity.entity_id} has missing sources: "
                + ", ".join(sorted(missing_sources))
            )
        document = _linked_document(
            entity,
            dataset_version=dataset_version,
            alias=alias,
            item=item,
            source_ids=source_ids,
            related_ids=related_ids,
        )
        documents.append(document)

    for row in repository.fetch_all("SELECT * FROM glossary ORDER BY term_id"):
        source_ids = sorted(split_ids(str(row.get("source_ids") or "")))
        missing_sources = set(source_ids) - source_keys
        if missing_sources:
            raise ValueError(f"glossary term {row['term_id']} has missing sources")
        fields = SearchFields(
            canonical_label=[str(row["term_ja"]), str(row["term_en"])],
            title=[str(row["term_ja"]), str(row["term_en"])],
            summary=[str(row.get("definition") or "")],
            keyword=[str(row.get("common_confusion") or "")],
            related=split_ids(str(row.get("related_entity_ids") or "")),
        )
        documents.append(
            SearchDocument(
                document_id=f"glossary:{row['term_id']}",
                entity_type="glossary",
                entity_id=str(row["term_id"]),
                canonical_route=f"/search?entity={quote(f'glossary:{row["term_id"]}', safe='')}",
                title_ja=str(row["term_ja"]),
                title_en=str(row["term_en"]),
                summary=str(row.get("definition") or ""),
                intents=list(INTENT_BY_TYPE["glossary"]),
                source_ids=source_ids,
                related_document_ids=[],
                last_reviewed=str(row.get("last_verified") or "") or None,
                fields=fields,
                tokens=_tokenize_fields(fields),
            )
        )

    search_index = SearchIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        normalization={
            "unicode": "NFKC",
            "case": "casefold",
            "punctuation": "space",
            "japanese": "character-bigram",
        },
        ranking_policy=FIELD_WEIGHTS,
        documents=sorted(documents, key=lambda document: document.document_id),
    )
    retrieval = _build_retrieval_export(
        search_index,
        content_index=content_index,
        generated_at=generated_at,
    )
    return search_index, retrieval


def load_benchmark_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("contract_version") != "1.0.0" or not isinstance(payload.get("queries"), list):
        raise ValueError("search benchmark fixture is invalid")
    return list(payload["queries"])


def evaluate_search_benchmark(index: SearchIndex, cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    top1 = top3 = recalled = zero_results = 0
    relevance_cases = 0
    for case in cases:
        entity_types = {
            cast(SearchEntityType, str(value)) for value in case.get("entity_types", [])
        } or None
        intents = {cast(SearchIntent, str(value)) for value in case.get("intents", [])} or None
        hits = search_documents(
            index,
            str(case["query"]),
            entity_types=entity_types,
            intents=intents,
        )
        hit_ids = [hit.document_id for hit in hits]
        expected = set(map(str, case["expected_document_ids"]))
        if expected:
            relevance_cases += 1
            top1 += bool(hit_ids and hit_ids[0] in expected)
            top3 += bool(expected.intersection(hit_ids[:3]))
            recalled += bool(expected.intersection(hit_ids))
        zero_results += not hit_ids
        rows.append(
            {
                "query_id": case["query_id"],
                "query": case["query"],
                "category": case["category"],
                "expected_document_ids": sorted(expected),
                "entity_types": sorted(entity_types or []),
                "intents": sorted(intents or []),
                "top_document_ids": hit_ids[:3],
                "result_count": len(hit_ids),
            }
        )
    count = len(cases)
    return {
        "contract_version": "1.0.0",
        "dataset_version": index.dataset_version,
        "query_count": count,
        "metrics": {
            "top_1_relevance": (top1 / relevance_cases if relevance_cases else 0),
            "top_3_relevance": (top3 / relevance_cases if relevance_cases else 0),
            "expected_entity_recall": (recalled / relevance_cases if relevance_cases else 0),
            "zero_result_rate": zero_results / count if count else 0,
        },
        "queries": rows,
    }


def _linked_document(
    entity: LinkedEntity,
    *,
    dataset_version: str,
    alias: dict[str, Any],
    item: dict[str, Any],
    source_ids: list[str],
    related_ids: list[str],
) -> SearchDocument:
    entity_type = entity.entity_type
    title_ja = str(alias.get("label_ja") or item.get("title_ja") or entity.label)
    title_en = str(alias.get("label_en") or item.get("title_en") or entity.label)
    aliases = _strings(
        alias,
        "abbreviations",
        "synonyms",
        "domain_terms",
        "misspellings",
        "deprecated_terms",
    ) + _split_values(str(item.get("aliases") or ""))
    keywords = _strings(item, "keywords")
    domains = sorted(set(_strings(item, "domains")))
    related_labels = _strings(item, "related_labels")
    summary = str(item.get("summary") or entity.summary or "")
    fields = SearchFields(
        canonical_label=_unique([title_ja, title_en, entity.entity_id]),
        alias=_unique(aliases),
        title=_unique([entity.label, title_ja, title_en]),
        summary=_unique([summary]),
        keyword=_unique(keywords + domains),
        related=_unique(related_labels),
    )
    route = (
        entity.canonical_url
        or f"/search?entity={quote(f'{entity_type}:{entity.entity_id}', safe='')}"
    )
    return SearchDocument(
        document_id=f"{entity_type}:{entity.entity_id}",
        entity_type=entity_type,
        entity_id=entity.entity_id,
        canonical_route=route,
        external_url=entity.external_url,
        title_ja=title_ja,
        title_en=title_en,
        summary=summary,
        intents=list(INTENT_BY_TYPE[entity_type]),
        domains=domains,
        source_ids=source_ids,
        related_document_ids=related_ids,
        last_reviewed=str(item.get("last_reviewed") or "") or None,
        content_status=str(item.get("content_status") or "published"),
        fields=fields,
        tokens=_tokenize_fields(fields),
    )


def _tokenize_fields(fields: SearchFields) -> SearchFields:
    return SearchFields(
        **{
            field: sorted(
                {token for value in getattr(fields, field) for token in lexical_tokens(value)}
            )
            for field in FIELD_WEIGHTS
        }
    )


def _aliases_by_target(graph: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    list_fields = (
        "abbreviations",
        "synonyms",
        "domain_terms",
        "misspellings",
        "deprecated_terms",
        "source_ids",
    )
    for alias in graph["aliases"]:
        key = (str(alias["target_type"]), str(alias["target_id"]))
        target = grouped.setdefault(
            key,
            {
                "label_ja": alias["label_ja"],
                "label_en": alias["label_en"],
                **{field: [] for field in list_fields},
            },
        )
        for field in list_fields:
            target[field] = _unique([*target[field], *alias.get(field, [])])
    return grouped


def _repository_metadata(repository: KnowledgeRepository) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    specs = (
        (
            "method",
            "methods",
            "method_id",
            "name_ja",
            "name_en",
            "summary",
            (
                "aliases",
                "problem_classes",
                "required_assumptions",
                "derivative_information",
                "variable_types",
                "constraint_support",
                "theoretical_guarantee",
                "optimality_certificate",
                "strengths",
                "typical_failures",
                "avoid_conditions",
                "first_choice_conditions",
            ),
            ("method_family_id",),
            "reference_source_ids",
        ),
        (
            "problem",
            "problem_archetypes",
            "problem_id",
            "name_ja",
            "name_en",
            "summary",
            ("canonical_form", "example_domains", "first_questions"),
            ("domain_group",),
            "source_ids",
        ),
        (
            "feature",
            "problem_features",
            "feature_id",
            "name_ja",
            "name_en",
            "definition",
            ("feature_code", "why_it_matters", "boundary_notes"),
            ("category",),
            "source_ids",
        ),
        (
            "implementation",
            "implementations",
            "implementation_id",
            "library_name",
            "solver_name",
            "notes",
            ("api_name", "method_selector", "problem_formats", "supported_method_ids"),
            ("language",),
            "source_ids",
        ),
    )
    for (
        entity_type,
        table,
        id_key,
        ja_key,
        en_key,
        summary_key,
        keyword_keys,
        domain_keys,
        source_key,
    ) in specs:
        for row in repository.fetch_all(f'SELECT * FROM "{table}" ORDER BY "{id_key}"'):
            result[(entity_type, str(row[id_key]))] = {
                "title_ja": str(row.get(ja_key) or row.get(en_key) or row[id_key]),
                "title_en": str(row.get(en_key) or row.get(ja_key) or row[id_key]),
                "summary": str(row.get(summary_key) or ""),
                "aliases": str(row.get("aliases") or ""),
                "keywords": [str(row.get(key) or "") for key in keyword_keys],
                "domains": [str(row.get(key) or "") for key in domain_keys],
                "source_ids": split_ids(str(row.get(source_key) or "")),
                "last_reviewed": row.get("last_verified"),
            }
    return result


def _artifact_metadata(
    content_index: dict[str, Any],
    gallery_index: dict[str, Any],
    comparison_index: dict[str, Any],
    scenario_index: dict[str, Any],
    source_index: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for page in content_index["pages"]:
        result[("content", str(page["content_id"]))] = {
            "title_ja": page["title_ja"],
            "title_en": page["title_en"],
            "summary": page["summary"],
            "keywords": [item["label"] for item in page.get("toc", [])],
            "domains": [page["kind"]],
            "source_ids": page["source_ids"],
            "last_reviewed": page["last_reviewed"],
            "content_status": page["status"],
        }
    for case in gallery_index["cases"]:
        result[("case", str(case["case_id"]))] = {
            "title_ja": case["title_ja"],
            "title_en": case["title_en"],
            "summary": case["question"],
            "keywords": [
                case.get("objective", ""),
                case.get("constraints", ""),
                case.get("decision_variables", ""),
                case.get("practical_notes", ""),
            ],
            "domains": [case.get("domain", "")],
            "source_ids": case["source_ids"],
            "last_reviewed": case["last_reviewed"],
            "content_status": case["status"],
        }
    for comparison in comparison_index["comparisons"]:
        renderer_families = sorted(
            {str(member["artifact"]["renderer_family"]) for member in comparison["members"]}
        )
        result[("comparison", str(comparison["comparison_id"]))] = {
            "title_ja": comparison["title_ja"],
            "title_en": comparison["title_en"],
            "summary": comparison.get("fairness_note", ""),
            "aliases": ";".join(comparison.get("aliases", [])),
            "keywords": [
                comparison.get("caveat", ""),
                comparison.get("formulation_summary", ""),
                comparison.get("comparison_question", ""),
                *comparison.get("fixed_factors", []),
                *comparison.get("changed_factors", []),
            ],
            "domains": [comparison.get("mode", ""), *renderer_families],
            "source_ids": comparison.get("source_ids", []),
            "last_reviewed": comparison.get("last_verified"),
        }
    for scenario in scenario_index["scenarios"]:
        item = {
            "title_ja": scenario["title_ja"],
            "title_en": scenario["title_en"],
            "summary": scenario["lesson"]["learning_objective"]["ja"],
            "keywords": [
                scenario["lesson"]["expected_phenomenon_ja"],
                scenario["lesson"]["static_summary"]["ja"],
                scenario["lesson"]["text_alternative"]["ja"],
            ],
            "domains": [scenario["purpose"], scenario["artifact"]["renderer_family"]],
            "source_ids": scenario["source_ids"],
            "last_reviewed": scenario["last_verified"],
        }
        for run in scenario["runs"]:
            result[("trace", str(run["artifact_id"]))] = item
        result[("scenario", str(scenario["scenario_id"]))] = item
    for source in source_index["sources"]:
        result[("source", str(source["source_id"]))] = {
            "title_ja": source["title"],
            "title_en": source["title"],
            "summary": source.get("supported_claim", ""),
            "keywords": [source.get("publisher", ""), source.get("source_type", "")],
            "domains": [source.get("source_quality", "")],
            "source_ids": [source["source_id"]],
            "last_reviewed": source.get("last_verified"),
        }
    return result


def _build_retrieval_export(
    index: SearchIndex,
    *,
    content_index: dict[str, Any],
    generated_at: datetime,
) -> RetrievalExport:
    content_by_id = {str(page["content_id"]): page for page in content_index["pages"]}
    chunks: list[RetrievalChunk] = []
    attribution = "Optimization Compass contributors"
    for document in index.documents:
        page = content_by_id.get(document.entity_id) if document.entity_type == "content" else None
        sections = (
            _content_sections(page) if page else [("overview", document.title_ja, document.summary)]
        )
        for section_id, title, text in sections:
            if not text.strip():
                continue
            chunks.append(
                RetrievalChunk(
                    chunk_id=f"{document.document_id}:{section_id}",
                    document_id=document.document_id,
                    title=title,
                    text=text.strip(),
                    relation_context=document.related_document_ids,
                    source_ids=document.source_ids,
                    dataset_version=index.dataset_version,
                    attribution=attribution,
                    authority="canonical"
                    if document.entity_type in {"content", "glossary"}
                    else "generated_from_canonical",
                )
            )
    return RetrievalExport(
        dataset_version=index.dataset_version,
        generated_at=generated_at,
        chunking_policy={
            "content": "stable h2 heading-aware sections",
            "structured_entity": "one compact overview chunk",
            "generated_frames": "excluded",
        },
        chunks=sorted(chunks, key=lambda chunk: chunk.chunk_id),
    )


def _content_sections(page: dict[str, Any]) -> list[tuple[str, str, str]]:
    html_text = str(page["html"])
    sections: list[tuple[str, str, str]] = []
    intro = html_text.split("<h2", 1)[0]
    intro_text = _plain_text(intro)
    if intro_text:
        sections.append(("overview", str(page["title_ja"]), intro_text))
    for match in _CONTENT_SECTION.finditer(html_text):
        sections.append((match.group(1), _plain_text(match.group(2)), _plain_text(match.group(3))))
    return sections or [("overview", str(page["title_ja"]), str(page["summary"]))]


def _plain_text(value: str) -> str:
    return " ".join(html.unescape(_HTML_TAG.sub(" ", value)).split())


def _strings(item: dict[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        raw = item.get(key, [])
        if isinstance(raw, list):
            values.extend(str(value) for value in raw if str(value).strip())
        elif str(raw).strip():
            values.extend(_split_values(str(raw)))
    return _unique(values)


def _split_values(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;|]", value) if part.strip()]


def _unique(values: list[str]) -> list[str]:
    return sorted({value.strip() for value in values if value.strip()})
