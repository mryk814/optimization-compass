from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, date, datetime, time
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from optimization_compass.comparisons import (
    load_comparison_seed,
    validate_comparison_benchmark_contexts,
)
from optimization_compass.constraint_geometry import (
    PROFILE_ID as SO3_PROFILE_ID,
)
from optimization_compass.constraint_geometry import (
    build_so3_scenario,
    generate_so3_traces,
)
from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.coverage import build_coverage_report, write_coverage_report
from optimization_compass.db import KnowledgeRepository
from optimization_compass.derived_media import write_derived_media
from optimization_compass.entity_links import build_entity_link_index
from optimization_compass.evidence import build_source_evidence_index
from optimization_compass.failure_discovery import build_failure_discovery_index
from optimization_compass.formulation_primer import build_formulation_primer_index
from optimization_compass.learning_graph import build_learning_graph_index
from optimization_compass.learning_journey_policy import load_learning_journey_asset_policy
from optimization_compass.learning_journeys import build_learning_journey_index
from optimization_compass.learning_slices import write_learning_slice_scenarios
from optimization_compass.metadata_models import ViewPresetSeed
from optimization_compass.nested_solve import (
    BILEVEL_EXACT_TRACE_ID,
    BILEVEL_PROFILE_ID,
    BILEVEL_RELAXED_TRACE_ID,
    HYBRID_CHATTERING_TRACE_ID,
    HYBRID_PROFILE_ID,
    build_nested_solve_scenario,
    generate_bilevel_regression_traces,
    generate_hybrid_chattering_trace,
)
from optimization_compass.parameter_estimation import (
    LBFGSB_SCENARIO_ID,
    LM_SCENARIO_ID,
    POOR_INITIALIZATION_SCENARIO_ID,
    PRIMARY_SCENARIO_ID,
    generate_parameter_estimation_traces,
)
from optimization_compass.portfolio_uncertainty import (
    CVAR_TRACE_ID,
    NOMINAL_TRACE_ID,
    build_portfolio_uncertainty_scenario,
    generate_portfolio_uncertainty_traces,
)
from optimization_compass.portfolio_uncertainty import (
    PROFILE_ID as PORTFOLIO_UNCERTAINTY_PROFILE_ID,
)
from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.release_catalog import (
    load_release_catalog,
    release_catalog_snapshot,
    validate_release_catalog,
)
from optimization_compass.release_identity import DatasetReleaseIdentity, canonical_identity_json
from optimization_compass.search_index import (
    build_search_artifacts,
    evaluate_search_benchmark,
    load_benchmark_cases,
)
from optimization_compass.search_tree import (
    SearchTreeArtifact,
    SearchTreeIndex,
    SearchTreeIndexEntry,
    generate_search_tree_artifact,
    render_search_tree_svg,
)
from optimization_compass.shape_optimization import (
    PROFILE_ID as SHAPE_OPTIMIZATION_PROFILE_ID,
)
from optimization_compass.shape_optimization import (
    TOPOLOGY_PROFILE_ID as SHAPE_TOPOLOGY_PROFILE_ID,
)
from optimization_compass.shape_optimization import (
    build_shape_optimization_scenario,
    generate_shape_optimization_traces,
)
from optimization_compass.simulation_constrained import (
    FAILURE_SCENARIO_ID as PDE_FAILURE_SCENARIO_ID,
)
from optimization_compass.simulation_constrained import (
    LOOSE_SCENARIO_ID as PDE_LOOSE_SCENARIO_ID,
)
from optimization_compass.simulation_constrained import (
    PROFILE_ID as SIMULATION_CONSTRAINED_PROFILE_ID,
)
from optimization_compass.simulation_constrained import (
    TIGHT_SCENARIO_ID as PDE_TIGHT_SCENARIO_ID,
)
from optimization_compass.simulation_constrained import (
    generate_simulation_constrained_traces,
)
from optimization_compass.surrogate_uncertainty import write_surrogate_scenarios
from optimization_compass.trace_models import (
    AlgorithmTrace,
    TraceFrame,
    TraceIndex,
    TraceIndexEntry,
    TraceMetric,
    TracePoint,
    TraceVector,
    canonical_trace_bytes,
)
from optimization_compass.traces import generate_gradient_bundle, generate_nelder_mead_trace
from optimization_compass.view_spec import (
    AnswerBinding,
    EntityReference,
    ManifestAsset,
    ManifestCoverageAsset,
    ManifestDerivedMediaAsset,
    ManifestLearningJourneyAsset,
    ManifestLicenseAsset,
    ManifestRecommendationAsset,
    ManifestTraceAsset,
    ManifestView,
    ManifestVisualizationScenarioAsset,
    SiteLicenseManifest,
    SiteManifest,
    ViewEdge,
    ViewEntity,
    ViewFilterGroup,
    ViewFilterPolicy,
    ViewNode,
    ViewSpec,
)
from optimization_compass.visualization_scenarios import (
    GuidedStory,
    GuidedStoryStep,
    KnownReferenceDisplay,
    LocalizedText,
    RendererFamily,
    VisualizationArtifact,
    VisualizationBudget,
    VisualizationExperiment,
    VisualizationInitialCondition,
    VisualizationLesson,
    VisualizationNarrationStep,
    VisualizationObservable,
    VisualizationRun,
    VisualizationScenario,
    VisualizationScenarioIndex,
    VisualizationSeed,
    VisualizationSignal,
    scenario_identity,
)

VIEW_VERSION: Literal["1.0.0"] = "1.0.0"
SITE_MANIFEST_VERSION: Literal["1.4.0"] = "1.4.0"
ROOT = Path(__file__).parents[2]
CONTENT_DIRECTORY = ROOT / "content"
GALLERY_SEED = ROOT / "data/seeds/site_gallery.json"
COMPARISON_SEED = ROOT / "data/seeds/site_comparisons.json"
SEARCH_BENCHMARK_SEED = ROOT / "data/seeds/search_benchmark.json"
VISUALIZATION_SCENARIO_PATH = "visualization-scenarios.json"
FORMULATION_PRIMER_TERMS_SEED = ROOT / "data/seeds/formulation_primer_terms.json"
LEARNING_JOURNEY_ASSET_POLICY_SEED = ROOT / "data/seeds/learning_journey_asset_policy.json"
RELEASE_CATALOG_PATH = ROOT / "data/releases/catalog.json"

# Keep these labels aligned with the existing browser copy contract in web.py.
ANSWER_LABELS_JA: dict[str, str] = {
    "continuous": "連続値（continuous）",
    "integer": "整数値（integer）",
    "binary": "0/1の二値（binary）",
    "categorical": "カテゴリ値（categorical）",
    "mixed": "混合型（mixed）",
    "structured_or_unknown": "構造化・複雑な型（structured or unknown）",
    "explicit_algebraic": "数式で表せる（explicit algebraic）",
    "residual_vector": "残差ベクトルで表せる（residual vector）",
    "automatic_differentiation_graph": (
        "自動微分グラフで表せる（automatic differentiation graph）"
    ),
    "simulation_only": "シミュレーションのみ（simulation only）",
    "experiment_only": "実験で評価する（experiment only）",
    "unknown": "わからない（unknown）",
    "linear": "線形（linear）",
    "quadratic": "二次（quadratic）",
    "sum_of_squares": "二乗和（sum of squares）",
    "general_nonlinear": "一般の非線形（general nonlinear）",
    "multiobjective": "多目的（multiobjective）",
    "equation_or_feasibility": "方程式・実行可能性問題（equation or feasibility）",
    "none": "制約なし（none）",
    "bounds": "上下限制約（bounds）",
    "nonlinear": "非線形制約（nonlinear）",
    "logical_or_combinatorial": "論理・組合せ制約（logical or combinatorial）",
    "conic_or_psd": "錐・半正定値制約（conic or PSD）",
    "dynamics_or_manifold": "力学系・多様体制約（dynamics or manifold）",
    "implicit_or_failure": "暗黙的・失敗する可能性あり（implicit or failure）",
    "analytic_gradient": "解析的な勾配（analytic gradient）",
    "autodiff": "自動微分（autodiff）",
    "jacobian_or_hvp": "Jacobian・HVP（Jacobian or HVP）",
    "numerical_difference_only": "数値差分のみ（numerical difference only）",
    "stochastic_gradient": "確率的勾配（stochastic gradient）",
    "unreliable_or_none": "信頼できない・利用不可（unreliable or none）",
    "not_differentiable": "微分できない（not differentiable）",
    "milliseconds_or_less": "ミリ秒以下（milliseconds or less）",
    "seconds": "秒（seconds）",
    "minutes": "分（minutes）",
    "hours_or_more": "時間以上（hours or more）",
    "deterministic_reliable": "決定的で信頼できる（deterministic reliable）",
    "small_noise": "小さなノイズ（small noise）",
    "large_noise": "大きなノイズ（large noise）",
    "random_seeded": "乱数によるがseed固定可能（random seeded）",
    "occasional_failure": "ときどき失敗する（occasional failure）",
    "frequent_failure": "頻繁に失敗する（frequent failure）",
    "timeout_possible": "タイムアウトの可能性あり（timeout possible）",
    "under_10": "10未満（under 10）",
    "10_to_100": "10〜100",
    "100_to_10000": "100〜10,000",
    "over_10000": "10,000超（over 10,000）",
    "huge_sparse_or_distributed": "巨大・疎・分散型（huge sparse or distributed）",
    "local_is_fine": "局所解で十分（local is fine）",
    "global_candidate_desired": "大域解の候補がほしい（global candidate desired）",
    "multiple_distinct_solutions": ("異なる解を複数探したい（multiple distinct solutions）"),
    "no_certificate_needed": "証明は不要（no certificate needed）",
    "gap_desired": "最適性gapがほしい（gap desired）",
    "global_proof_required": "大域最適性の証明が必要（global proof required）",
    "feasible_solution_first": "まず実行可能解がほしい（feasible solution first）",
    "approximation_guarantee": "近似保証がほしい（approximation guarantee）",
    "none_known": "特になし（none known）",
    "least_squares": "最小二乗（least squares）",
    "lp_qp_conic": "LP・QP・錐最適化（LP/QP/conic）",
    "graph_flow_path_matching": ("グラフ・フロー・経路・マッチング（graph/flow/path/matching）"),
    "scheduling_routing": "スケジューリング・経路計画（scheduling/routing）",
    "prox_separable": "近接可能・分離可能（prox/separable）",
    "optimal_control": "最適制御（optimal control）",
    "manifold": "多様体（manifold）",
    "stochastic_or_robust": "確率的・ロバスト（stochastic or robust）",
    "other": "その他（other）",
    "one_off": "一度だけ（one-off）",
    "repeated_similar": "似た問題を繰り返す（repeated similar）",
    "online_or_realtime": "オンライン・リアルタイム（online or realtime）",
    "parallel_evaluations": "評価を並列化できる（parallel evaluations）",
    "distributed": "分散実行できる（distributed）",
    "gpu_available": "GPUを使える（GPU available）",
    "warm_start_available": "warm startを使える（warm start available）",
}

ANSWER_LABELS_EN_WITHOUT_PARENTHETICAL = {
    "10_to_100": "10 to 100",
    "100_to_10000": "100 to 10,000",
}

RELATED_ENTITY_TYPES = {"method", "problem", "feature", "alternative"}


def export_site_data(
    output_dir: Path,
    repository: KnowledgeRepository,
    *,
    staged: bool = False,
) -> SiteManifest:
    release = repository.latest_release()
    release_identity = DatasetReleaseIdentity(
        schema_version=1,
        dataset_version=release["version"],
        release_date=release["release_date"],
        database_sha256=repository.database_sha256(),
    )
    catalog = load_release_catalog(RELEASE_CATALOG_PATH)
    if staged:
        release_catalog = release_catalog_snapshot(catalog, release_identity)
    else:
        validate_release_catalog(catalog, expected_current_identity=release_identity)
        release_catalog = catalog
    generated_at = datetime.combine(
        date.fromisoformat(release["release_date"]), time.min, tzinfo=UTC
    )
    questions = repository.atlas_questions()
    rules = repository.atlas_rules()
    alternatives = repository.atlas_alternatives()
    presets = repository.semantic_view_presets()
    if len(presets) < 4:
        raise ValueError("site export requires at least four semantic view presets")
    if len({preset.view_id for preset in presets}) != len(presets):
        raise ValueError("semantic view presets contain duplicate public view IDs")

    question_feature_ids = {str(question["mapped_feature_id"]) for question in questions}
    target_ids = _target_ids_by_type(rules)
    preset_feature_ids = {
        feature_id
        for preset in presets
        for group in preset.filter_policy.groups
        for feature_id in group.feature_ids
    }
    preset_method_ids = {
        method_id
        for preset in presets
        for group in preset.filter_policy.groups
        for method_id in group.method_ids
    }
    feature_ids = sorted(question_feature_ids | target_ids["feature"] | preset_feature_ids)
    method_ids = sorted(target_ids["method"] | preset_method_ids)
    features = repository.atlas_features(feature_ids)
    feature_values = repository.atlas_feature_values(feature_ids)
    methods = repository.atlas_methods(method_ids)
    problems = repository.atlas_problems(sorted(target_ids["problem"]))

    _require_all_ids(features, "feature_id", feature_ids, "feature")
    _require_all_ids(methods, "method_id", method_ids, "method")
    _require_all_ids(problems, "problem_id", sorted(target_ids["problem"]), "problem")
    _require_all_ids(
        alternatives,
        "alternative_id",
        sorted(target_ids["alternative"]),
        "alternative",
    )

    source_ids = sorted(
        {
            str(source_id)
            for row in [*questions, *rules, *features, *methods, *problems, *alternatives]
            for source_id in row["source_ids"]
        }
        | {source_id for preset in presets for source_id in preset.source_ids}
    )
    sources = repository.atlas_sources(source_ids)
    _require_all_ids(sources, "source_id", source_ids, "source")

    views: list[ViewSpec] = []
    for preset in presets:
        if preset.view_id == "problem-structure":
            views.append(
                _build_problem_structure(
                    preset=preset,
                    questions=questions,
                    rules=rules,
                    feature_values=feature_values,
                    dataset_version=release["version"],
                    generated_at=generated_at,
                    features=features,
                    methods=methods,
                    problems=problems,
                    alternatives=alternatives,
                    sources=sources,
                )
            )
        else:
            views.append(
                _build_grouped_semantic_view(
                    preset=preset,
                    dataset_version=release["version"],
                    generated_at=generated_at,
                    features=features,
                    methods=methods,
                    problems=problems,
                    alternatives=alternatives,
                    sources=sources,
                )
            )
    from optimization_compass.site_recommendation import build_site_data

    recommendation_data = build_site_data(repository)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "release.json").write_text(
        canonical_identity_json(release_identity), encoding="utf-8", newline="\n"
    )
    _write_json(output_dir / "release-catalog.json", release_catalog.as_json_object())
    _write_content_index(output_dir / "content.json", release["version"])
    _write_seeded_index(
        output_dir / "gallery.json",
        GALLERY_SEED,
        collection_field="cases",
        contract_version="2.0.0",
        dataset_version=release["version"],
    )
    comparison_seed = load_comparison_seed(COMPARISON_SEED, release["version"])
    _write_json(output_dir / "comparisons.json", comparison_seed)
    for view in views:
        _write_json(output_dir / f"views/{view.view_id}.json", view)
    _write_json(output_dir / "recommendation/site-data.json", recommendation_data)
    problem_catalog = repository.problem_catalog()
    _write_json(output_dir / "problems.json", problem_catalog)
    search_tree_index, search_tree_artifacts = _write_search_tree_artifacts(
        output_dir, dataset_version=release["version"]
    )
    trace_asset, trace_index, generated_traces = _write_dummy_trace(
        output_dir,
        dataset_version=release["version"],
        additional_traces=[artifact.trace for artifact in search_tree_artifacts],
    )
    surrogate_scenarios = write_surrogate_scenarios(output_dir, dataset_version=release["version"])
    learning_slice_scenarios, learning_slice_links = write_learning_slice_scenarios(
        output_dir, dataset_version=release["version"]
    )
    scenario_index = _build_visualization_scenario_index(
        generated_traces,
        surrogate_scenarios=surrogate_scenarios,
        learning_slice_scenarios=learning_slice_scenarios,
        dataset_version=release["version"],
    )
    validate_comparison_benchmark_contexts(
        comparison_seed,
        repository.benchmark_contexts(),
        scenario_index.scenarios,
        problem_definition_ids={
            definition.problem_definition_id for definition in problem_catalog.definitions
        },
        problem_instance_ids={
            instance.problem_instance_id for instance in problem_catalog.instances
        },
        traces=generated_traces,
    )
    _write_json(output_dir / VISUALIZATION_SCENARIO_PATH, scenario_index)
    gallery_index = json.loads((output_dir / "gallery.json").read_text(encoding="utf-8"))
    comparison_index = json.loads((output_dir / "comparisons.json").read_text(encoding="utf-8"))
    content_pages = [page for page in load_content(CONTENT_DIRECTORY) if page.status == "published"]
    journey_inventories = {
        "case": {str(item["case_id"]) for item in gallery_index["cases"]},
        "problem": {
            str(item["problem_id"])
            for item in repository.fetch_all("SELECT problem_id FROM problem_archetypes")
        },
        "scenario": {item.scenario_id for item in scenario_index.scenarios},
        "comparison": {str(item["comparison_id"]) for item in comparison_index["comparisons"]},
        "method": {
            str(item["method_id"]) for item in repository.fetch_all("SELECT method_id FROM methods")
        },
        "implementation": {
            str(item["implementation_id"])
            for item in repository.fetch_all("SELECT implementation_id FROM implementations")
        },
        "content": {page.content_id for page in content_pages},
        "source": {
            str(item["source_id"]) for item in repository.fetch_all("SELECT source_id FROM sources")
        },
    }
    asset_policy = load_learning_journey_asset_policy(
        LEARNING_JOURNEY_ASSET_POLICY_SEED,
        inventories={
            "scenario": journey_inventories["scenario"],
            "comparison": journey_inventories["comparison"],
            "visualization_artifact": {
                run.artifact_id for scenario in scenario_index.scenarios for run in scenario.runs
            },
            "content": journey_inventories["content"],
        },
    )
    source_index = build_source_evidence_index(
        repository,
        dataset_version=release["version"],
        generated_at=generated_at,
        generated_visualizations=learning_slice_links,
    )
    learning_journeys = build_learning_journey_index(
        dataset_version=release["version"],
        generated_at=generated_at,
        gallery_index=gallery_index,
        scenario_index=scenario_index,
        comparison_index=comparison_index,
        content_pages=content_pages,
        source_index=source_index,
        asset_policy=asset_policy,
        inventories=journey_inventories,
    )
    _write_json(output_dir / "learning-journeys.json", learning_journeys)
    failure_discovery = build_failure_discovery_index(
        repository,
        dataset_version=release["version"],
        generated_at=generated_at,
        gallery_index=gallery_index,
        learning_journeys=learning_journeys,
    )
    _write_json(output_dir / "failure-discovery.json", failure_discovery)
    formulation_primer = build_formulation_primer_index(
        dataset_version=release["version"],
        generated_at=generated_at,
        glossary_rows=[
            *repository.fetch_all("SELECT * FROM glossary ORDER BY term_id"),
            *json.loads(FORMULATION_PRIMER_TERMS_SEED.read_text(encoding="utf-8"))["terms"],
        ],
    )
    _write_json(output_dir / "formulation-primer.json", formulation_primer)
    media_scenario = next(
        scenario
        for scenario in scenario_index.scenarios
        if scenario.scenario_id == "SCENARIO_NM_QUADRATIC"
    )
    media_trace = next(
        trace for trace in generated_traces if trace.scenario_id == media_scenario.scenario_id
    )
    derived_media = write_derived_media(
        output_dir,
        scenario=media_scenario,
        trace=media_trace,
    )
    _write_json(output_dir / "media/manifest.json", derived_media)
    search_tree_routes = {
        entry.trace_id: f"/theater/search-tree/{entry.artifact_id}"
        for entry in search_tree_index.artifacts
    }
    search_tree_sources = {
        artifact.trace.trace_id: artifact.trace.source_ids for artifact in search_tree_artifacts
    }
    search_tree_views = {
        artifact.trace.trace_id: ["VIEW_PROBLEM_STRUCTURE", "VIEW_METHOD_MECHANISM"]
        for artifact in search_tree_artifacts
    }
    entity_links = build_entity_link_index(
        repository,
        dataset_version=release["version"],
        generated_at=generated_at,
        trace_index=trace_index,
        content_directory=CONTENT_DIRECTORY,
        gallery_path=output_dir / "gallery.json",
        comparison_path=output_dir / "comparisons.json",
        scenario_index=scenario_index,
        learning_journeys=learning_journeys,
        trace_routes=search_tree_routes,
        trace_source_ids=search_tree_sources,
        trace_view_ids=search_tree_views,
        visualization_entries=learning_slice_links,
    )
    _write_json(output_dir / "entity-links.json", entity_links)
    learning_graph = build_learning_graph_index(
        repository,
        dataset_version=release["version"],
        entity_links=entity_links,
        trace_index=trace_index,
    )
    _write_json(output_dir / "learning-graph.json", learning_graph)
    _write_json(output_dir / "sources.json", source_index)
    search_index, retrieval_documents = build_search_artifacts(
        repository,
        dataset_version=release["version"],
        generated_at=generated_at,
        entity_links=entity_links,
        learning_graph=learning_graph,
        content_index=json.loads((output_dir / "content.json").read_text(encoding="utf-8")),
        gallery_index=json.loads((output_dir / "gallery.json").read_text(encoding="utf-8")),
        comparison_index=json.loads((output_dir / "comparisons.json").read_text(encoding="utf-8")),
        scenario_index=scenario_index.model_dump(mode="json"),
        source_index=source_index.model_dump(mode="json"),
        failure_discovery_index=failure_discovery.model_dump(mode="json"),
    )
    _write_json(output_dir / "search-index.json", search_index, compact=True)
    _write_json(output_dir / "retrieval-documents.json", retrieval_documents)
    _write_json(
        output_dir / "search-benchmark.json",
        evaluate_search_benchmark(search_index, load_benchmark_cases(SEARCH_BENCHMARK_SEED)),
    )
    _write_json(
        output_dir / "implementation-claims.json",
        {
            "contract_version": "1.0.0",
            "dataset_version": release["version"],
            "claims": repository.implementation_claim_history(),
            "freshness": repository.implementation_claim_freshness(
                date.fromisoformat(release["release_date"])
            ),
        },
    )
    _write_json(
        output_dir / "benchmark-contexts.json",
        {
            "contract_version": "1.0.0",
            "dataset_version": release["version"],
            "contexts": repository.benchmark_contexts(),
            "ranking_policy": {
                "context_required": True,
                "missing_context_action": "ranking_forbidden",
            },
        },
    )
    _write_json(
        output_dir / "failure-modes.json",
        {
            "contract_version": "1.0.0",
            "dataset_version": release["version"],
            "failure_modes": repository.structured_failure_modes(),
        },
    )
    coverage = build_coverage_report(
        repository,
        output_dir,
        dataset_version=release["version"],
        generated_at=generated_at,
    )
    write_coverage_report(coverage, output_dir / "coverage.json", output_dir / "coverage.md")
    manifest = SiteManifest(
        version=SITE_MANIFEST_VERSION,
        dataset_version=release["version"],
        generated_at=generated_at,
        views=[
            ManifestView(
                view_id=view.view_id,
                version=VIEW_VERSION,
                path=f"views/{view.view_id}.json",
            )
            for view in views
        ],
        recommendation=ManifestRecommendationAsset(
            version="2.0.0", path="recommendation/site-data.json"
        ),
        traces=trace_asset,
        problems=ManifestAsset(version="1.0.0", path="problems.json"),
        learning_journeys=ManifestLearningJourneyAsset(
            version="1.1.0", path="learning-journeys.json"
        ),
        formulation_primer=ManifestAsset(version="1.0.0", path="formulation-primer.json"),
        visualization_scenarios=ManifestVisualizationScenarioAsset(
            version="1.2.0", path=VISUALIZATION_SCENARIO_PATH
        ),
        derived_media=ManifestDerivedMediaAsset(version="1.1.0", path="media/manifest.json"),
        entity_links=ManifestAsset(version="1.0.0", path="entity-links.json"),
        sources=ManifestAsset(version="1.0.0", path="sources.json"),
        implementation_claims=ManifestAsset(version="1.0.0", path="implementation-claims.json"),
        benchmark_contexts=ManifestAsset(version="1.0.0", path="benchmark-contexts.json"),
        failure_modes=ManifestAsset(version="1.0.0", path="failure-modes.json"),
        failure_discovery=ManifestAsset(version="1.0.0", path="failure-discovery.json"),
        release_catalog=ManifestAsset(version="1.0.0", path="release-catalog.json"),
        search_index=ManifestAsset(version="1.0.0", path="search-index.json"),
        retrieval_documents=ManifestAsset(version="1.0.0", path="retrieval-documents.json"),
        search_benchmark=ManifestAsset(version="1.0.0", path="search-benchmark.json"),
        coverage=ManifestCoverageAsset(
            version="1.0.0", path="coverage.json", report_path="coverage.md"
        ),
        licenses=SiteLicenseManifest(
            code=ManifestLicenseAsset(spdx_id="MIT", path="licenses/LICENSE.txt"),
            data=ManifestLicenseAsset(spdx_id="CC-BY-4.0", path="licenses/DATA_LICENSE.txt"),
            content=ManifestLicenseAsset(spdx_id="CC-BY-4.0", path="licenses/CONTENT_LICENSE.txt"),
            legal_code_path="licenses/CC-BY-4.0.txt",
            notice_path="licenses/NOTICE.txt",
            attribution=(
                "Optimization Compass, Copyright 2026 TAKUYA OTANI and Optimization Compass "
                "contributors"
            ),
        ),
    )

    _write_json(output_dir / "manifest.json", manifest)
    return manifest


def _generate_optimal_control_history_trace(*, dataset_version: str) -> AlgorithmTrace:
    values = [
        (1.00, 0.70, 0.42, 0.18, 4.80),
        (0.88, 0.76, 0.21, 0.13, 3.62),
        (0.79, 0.81, 0.11, 0.09, 2.74),
        (0.72, 0.86, 0.065, 0.06, 2.18),
        (0.67, 0.90, 0.038, 0.041, 1.91),
        (0.64, 0.93, 0.022, 0.029, 1.79),
        (0.62, 0.95, 0.014, 0.021, 1.73),
        (0.61, 0.96, 0.009, 0.016, 1.70),
        (0.60, 0.97, 0.006, 0.013, 1.68),
    ]
    frames = [
        TraceFrame(
            frame_index=index,
            iteration=index,
            oracle_evaluations=index,
            elapsed_steps=index,
            elapsed_time_ms=float(index * 120),
            event_type=(
                "initialize" if index == 0 else "update" if index < len(values) - 1 else "stop"
            ),
            decision="not_applicable" if index == 0 or index == len(values) - 1 else "accepted",
            explanation_key=(
                "initial_trajectory"
                if index == 0
                else "trajectory_update"
                if index < len(values) - 1
                else "mesh_result"
            ),
            event_label_ja=(
                "初期trajectory"
                if index == 0
                else "trajectoryを更新"
                if index < len(values) - 1
                else "固定meshで停止"
            ),
            event_label_en=(
                "Initial trajectory"
                if index == 0
                else "Update trajectory"
                if index < len(values) - 1
                else "Stop on fixed mesh"
            ),
            keyframe=index in {0, 4, len(values) - 1},
            points=[],
            vectors=[],
            metrics=[
                TraceMetric(
                    metric_id="state_norm",
                    label_ja="state norm",
                    label_en="state norm",
                    value=state,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="control_effort",
                    label_ja="control effort",
                    label_en="control effort",
                    value=control,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="dynamics_defect",
                    label_ja="dynamics defect",
                    label_en="dynamics defect",
                    value=defect,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="path_violation",
                    label_ja="path violation",
                    label_en="path violation",
                    value=violation,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="objective_value",
                    label_ja="目的関数値",
                    label_en="objective value",
                    value=objective,
                    unit=None,
                ),
            ],
            payload={
                "mesh_nodes": 20,
                "state": state,
                "control": control,
                "dynamics_defect": defect,
                "path_violation": violation,
            },
        )
        for index, (state, control, defect, violation, objective) in enumerate(values)
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id="optimal-control-ec020-history",
        method_id="M_DIRECT_COLLOCATION",
        profile_id="PROFILE_OPTIMAL_CONTROL_GENERIC",
        objective_id="INSTANCE_OPTIMAL_CONTROL_EC020",
        scenario_id="SCENARIO_OPTIMAL_CONTROL_EC020",
        generator_id="educational.optimal_control.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "trajectory_tracking_plus_control_effort", "mesh_nodes": 20},
        preset={
            "preset_id": "VIEW_OPTIMAL_CONTROL_HISTORY",
            "discretization": "direct_collocation",
        },
        parameters={"mesh_nodes": 20, "horizon": 2.0, "path_tolerance": 1e-4},
        initial_state={"point": [0.0, 0.0], "state_dimension": 2, "control_dimension": 1},
        seed={"status": "fixed", "value": 2026},
        evaluation_budget=len(values) - 1,
        stopping={"max_oracle_evaluations": len(values) - 1, "dynamics_defect_tolerance": 1e-3},
        environment={"runtime": "educational", "version": "1.0.0"},
        fairness_statement=(
            "固定mesh・初期trajectory・dynamics modelの教育用履歴であり、"
            "手法の一般性能を比較しない。"
        ),
        frames=frames,
        terminal_status="converged",
        terminal_summary_ja=(
            "固定mesh上のdiagnostic historyを完了しました。連続時間の可行性は別途検証します。"
        ),
        terminal_summary_en=(
            "The fixed-mesh diagnostic history completed; continuous-time feasibility "
            "requires separate validation."
        ),
        source_ids=["S042", "S043"],
    )


def _optimal_control_trace(
    *,
    dataset_version: str,
    trace_id: str,
    scenario_id: str,
    mesh_nodes: int,
    values: list[tuple[float, float, float, float, float, float, float]],
    terminal_summary_ja: str,
    terminal_summary_en: str,
) -> AlgorithmTrace:
    frames = [
        TraceFrame(
            frame_index=index,
            iteration=index,
            oracle_evaluations=index,
            elapsed_steps=index,
            elapsed_time_ms=float(index * 120),
            event_type="initialize"
            if index == 0
            else "update"
            if index < len(values) - 1
            else "stop",
            decision="not_applicable" if index == 0 or index == len(values) - 1 else "accepted",
            explanation_key="initial_trajectory"
            if index == 0
            else "trajectory_update"
            if index < len(values) - 1
            else "mesh_result",
            event_label_ja="初期trajectory"
            if index == 0
            else "trajectoryを更新"
            if index < len(values) - 1
            else "固定meshで停止",
            event_label_en="Initial trajectory"
            if index == 0
            else "Update trajectory"
            if index < len(values) - 1
            else "Stop on fixed mesh",
            keyframe=index in {0, 4, len(values) - 1},
            points=[],
            vectors=[],
            metrics=[
                TraceMetric(
                    metric_id="state_norm",
                    label_ja="state norm",
                    label_en="state norm",
                    value=state,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="control_effort",
                    label_ja="control effort",
                    label_en="control effort",
                    value=control,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="dynamics_defect",
                    label_ja="dynamics defect",
                    label_en="dynamics defect",
                    value=defect,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="path_violation",
                    label_ja="再構成path violation",
                    label_en="reconstructed path violation",
                    value=reconstructed_violation,
                    unit=None,
                ),
                TraceMetric(
                    metric_id="objective_value",
                    label_ja="目的関数値",
                    label_en="objective value",
                    value=objective,
                    unit=None,
                ),
            ],
            payload={
                "mesh_nodes": mesh_nodes,
                "state": state,
                "control": control,
                "dynamics_defect": defect,
                "node_path_violation": node_violation,
                "reconstructed_path_violation": reconstructed_violation,
                "terminal_error": terminal_error,
            },
        )
        for index, (
            state,
            control,
            defect,
            node_violation,
            reconstructed_violation,
            objective,
            terminal_error,
        ) in enumerate(values)
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="M_DIRECT_COLLOCATION",
        profile_id="PROFILE_OPTIMAL_CONTROL_GENERIC",
        objective_id="INSTANCE_PENDULUM_SWING_UP_EC020",
        scenario_id=scenario_id,
        generator_id="educational.optimal_control.v1",
        generator_version="1.1.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={
            "kind": "pendulum_terminal_error_plus_control_effort",
            "mesh_nodes": mesh_nodes,
        },
        preset={
            "preset_id": "VIEW_OPTIMAL_CONTROL_HISTORY",
            "discretization": "direct_collocation",
        },
        parameters={
            "mesh_nodes": mesh_nodes,
            "horizon_seconds": 2.0,
            "dynamics_model": "torque_limited_pendulum",
            "path_tolerance": 1e-4,
            "terminal_tolerance": 1e-3,
        },
        initial_state={"point": [0.0, 0.0], "state_dimension": 2, "control_dimension": 1},
        seed={"status": "fixed", "value": 2026},
        evaluation_budget=len(values) - 1,
        stopping={"max_oracle_evaluations": len(values) - 1, "dynamics_defect_tolerance": 1e-3},
        environment={"runtime": "educational", "version": "1.0.0"},
        fairness_statement=(
            "同じpendulum dynamics・2秒horizon・初期/終端/path制約・初期trajectory・"
            "8 evaluation予算・停止toleranceを使う教育用履歴であり、一般性能を比較しない。"
        ),
        frames=frames,
        terminal_status="converged",
        terminal_summary_ja=terminal_summary_ja,
        terminal_summary_en=terminal_summary_en,
        source_ids=["S042", "S050", "S102"],
    )


def _generate_optimal_control_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    coarse_values = [
        (3.60, 4.80, 0.42, 0.18, 0.24, 22.0, 1.10),
        (3.72, 5.20, 0.21, 0.10, 0.16, 14.0, 0.72),
        (3.85, 5.70, 0.11, 0.052, 0.10, 8.6, 0.42),
        (3.96, 6.10, 0.055, 0.021, 0.064, 5.0, 0.20),
        (4.02, 6.35, 0.021, 0.008, 0.041, 3.0, 0.082),
        (4.06, 6.50, 0.008, 0.002, 0.027, 2.2, 0.031),
        (4.08, 6.58, 0.003, 0.0007, 0.019, 1.9, 0.012),
        (4.09, 6.62, 0.0014, 0.0002, 0.015, 1.78, 0.003),
        (4.10, 6.64, 0.0008, 0.00008, 0.012, 1.72, 0.0009),
    ]
    refined_values = [
        (3.60, 4.80, 0.40, 0.17, 0.20, 22.0, 1.10),
        (3.73, 5.25, 0.18, 0.082, 0.12, 13.8, 0.70),
        (3.87, 5.75, 0.082, 0.035, 0.067, 8.2, 0.38),
        (3.98, 6.15, 0.034, 0.012, 0.033, 4.7, 0.17),
        (4.04, 6.40, 0.013, 0.004, 0.016, 2.8, 0.066),
        (4.08, 6.53, 0.005, 0.0012, 0.008, 2.0, 0.024),
        (4.10, 6.60, 0.002, 0.0004, 0.0045, 1.78, 0.008),
        (4.11, 6.64, 0.0010, 0.00015, 0.0028, 1.67, 0.002),
        (4.12, 6.66, 0.0006, 0.00006, 0.0020, 1.63, 0.0007),
    ]
    rollout_failure_values = [
        (3.60, 4.80, 0.42, 0.18, 0.24, 22.0, 1.10),
        (3.75, 5.30, 0.19, 0.08, 0.16, 13.0, 0.78),
        (3.90, 5.85, 0.08, 0.03, 0.12, 7.5, 0.55),
        (4.01, 6.25, 0.032, 0.011, 0.10, 4.2, 0.40),
        (4.07, 6.50, 0.012, 0.003, 0.11, 2.7, 0.31),
        (4.10, 6.62, 0.004, 0.0009, 0.12, 2.0, 0.26),
        (4.12, 6.69, 0.0018, 0.0003, 0.13, 1.75, 0.23),
        (4.13, 6.72, 0.0010, 0.0001, 0.14, 1.66, 0.22),
        (4.14, 6.74, 0.0007, 0.00005, 0.15, 1.62, 0.22),
    ]
    return [
        _optimal_control_trace(
            dataset_version=dataset_version,
            trace_id="pendulum-collocation-coarse",
            scenario_id="SCENARIO_PENDULUM_SWING_UP_MESH_20",
            mesh_nodes=20,
            values=coarse_values,
            terminal_summary_ja=(
                "N=20のnode／collocation条件はtolerance内ですが、区間再構成のpath違反が残るため、連続時間可行とは判定しません。"
            ),
            terminal_summary_en=(
                "The N=20 node and collocation checks meet tolerance, but reconstructed "
                "path violations remain, so continuous-time feasibility is not claimed."
            ),
        ),
        _optimal_control_trace(
            dataset_version=dataset_version,
            trace_id="pendulum-collocation-refined",
            scenario_id="SCENARIO_PENDULUM_SWING_UP_MESH_40",
            mesh_nodes=40,
            values=refined_values,
            terminal_summary_ja=(
                "N=40で再構成path違反は小さくなりましたが、有限meshのcontrastであり連続時間保証ではありません。"
            ),
            terminal_summary_en=(
                "The reconstructed path violation is smaller at N=40, but this finite-mesh "
                "contrast is not a continuous-time guarantee."
            ),
        ),
        _optimal_control_trace(
            dataset_version=dataset_version,
            trace_id="pendulum-model-rollout-failure",
            scenario_id="SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH",
            mesh_nodes=20,
            values=rollout_failure_values,
            terminal_summary_ja=(
                "NLP上のdefectは小さい一方、gravityを10%変えたvalidation rolloutでは"
                "path違反と終端誤差が残りました。"
            ),
            terminal_summary_en=(
                "The NLP defect is small, while a validation rollout with 10% gravity "
                "mismatch retains path violation and terminal error."
            ),
        ),
    ]


def _write_dummy_trace(
    output_dir: Path,
    *,
    dataset_version: str,
    additional_traces: list[AlgorithmTrace] | None = None,
) -> tuple[ManifestTraceAsset, TraceIndex, list[AlgorithmTrace]]:
    dummy_problem = get_runtime_problem("OBJECTIVE_QUADRATIC_2D")
    frames = [
        _dummy_frame(
            frame_index=0,
            iteration=0,
            evaluations=3,
            event_type="initialize",
            decision="not_applicable",
            label_ja="初期状態",
            label_en="Initialize",
            points=[
                ("vertex-a", "頂点A", "Vertex A", (-2.5, 2.0), 30.25),
                ("vertex-b", "頂点B", "Vertex B", (-1.7, 2.0), 25.29),
                ("vertex-c", "頂点C", "Vertex C", (-2.5, 2.8), 41.13),
            ],
            best_point_id="vertex-b",
            vector_origin=(-2.1, 2.0),
            movement=(0.0, 0.0),
            explanation="初期点を評価し、完全なスナップショットを記録する。",
        ),
        _dummy_frame(
            frame_index=1,
            iteration=1,
            evaluations=4,
            event_type="reflect",
            decision="accepted",
            label_ja="反射点を受理",
            label_en="Accept reflection",
            points=[
                ("vertex-a", "頂点A", "Vertex A", (-2.5, 2.0), 30.25),
                ("vertex-b", "頂点B", "Vertex B", (-1.7, 2.0), 25.29),
                ("vertex-c", "頂点C", "Vertex C", (-2.5, 2.8), 41.13),
                ("trial", "反射点", "Reflected point", (-1.7, 1.2), 16.97),
            ],
            best_point_id="trial",
            vector_origin=(-2.1, 2.0),
            movement=(0.4, -0.8),
            explanation="重心から最悪点の反対側へ反射し、改善した候補を受理する。",
        ),
        _dummy_frame(
            frame_index=2,
            iteration=1,
            evaluations=4,
            event_type="stop",
            decision="not_applicable",
            label_ja="デモを終了",
            label_en="Stop demo",
            points=[
                ("vertex-a", "頂点A", "Vertex A", (-2.5, 2.0), 30.25),
                ("vertex-b", "頂点B", "Vertex B", (-1.7, 2.0), 25.29),
                ("vertex-c", "頂点C", "Vertex C", (-1.7, 1.2), 16.97),
            ],
            best_point_id="vertex-c",
            vector_origin=(-2.1, 2.0),
            movement=(0.0, 0.0),
            explanation="契約確認用の3フレームデモを終了する。",
        ),
    ]
    trace = AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id="dummy-educational",
        method_id="M_NELDER_MEAD",
        profile_id="PROFILE_NELDER_MEAD_2D",
        objective_id="OBJECTIVE_QUADRATIC_2D",
        scenario_id="SCENARIO_NM_QUADRATIC",
        generator_id="educational.nelder_mead.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=dummy_problem.trace_objective(),
        preset={"preset_id": "VIEW_NELDER_MEAD_THEATER"},
        parameters={"initial_scale": 0.8, "adaptive": False},
        initial_state={
            "point": [-2.5, 2.0],
            "simplex": [[-2.5, 2.0], [-1.7, 2.0], [-2.5, 2.8]],
        },
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=80,
        stopping={"max_oracle_evaluations": 80, "simplex_tolerance": 0.0001},
        environment={"runtime": "educational", "version": "1.0.0"},
        fairness_statement="契約デモは単独再生であり、手法の優劣を比較しない。",
        frames=frames,
        terminal_status="completed",
        terminal_summary_ja="3フレームの契約デモを完了しました。",
        terminal_summary_en="The three-frame contract demo completed.",
        source_ids=sorted({"S002", *dummy_problem.instance.source_ids}),
    )
    index = TraceIndex(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        traces=[
            TraceIndexEntry(
                trace_id=trace.trace_id,
                path="dummy-educational.json",
                method_id=trace.method_id,
                profile_id=trace.profile_id,
                objective_id=trace.objective_id,
                scenario_id=trace.scenario_id,
                title_ja="AlgorithmTrace 契約デモ",
                title_en="AlgorithmTrace contract demo",
            )
        ],
    )
    trace_path = output_dir / "traces/dummy-educational.json"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_bytes(canonical_trace_bytes(trace))
    index_path = output_dir / "traces/index.json"
    generated_traces = [
        generate_nelder_mead_trace(
            problem_instance_id="OBJECTIVE_QUADRATIC_2D",
            trace_id="nelder-mead-quadratic",
            dataset_version=dataset_version,
        ),
        generate_nelder_mead_trace(
            problem_instance_id="OBJECTIVE_QUADRATIC_2D",
            initial_point=[2.4, -2.4],
            trace_id="nelder-mead-quadratic-shifted",
            scenario_id="SCENARIO_NM_QUADRATIC_SHIFTED",
            dataset_version=dataset_version,
        ),
        generate_nelder_mead_trace(
            problem_instance_id="OBJECTIVE_ROSENBROCK_2D",
            trace_id="nelder-mead-rosenbrock",
            dataset_version=dataset_version,
        ),
        generate_nelder_mead_trace(
            problem_instance_id="OBJECTIVE_ROSENBROCK_2D",
            initial_point=[-2.0, -1.0],
            trace_id="nelder-mead-rosenbrock-shifted",
            scenario_id="SCENARIO_NM_ROSENBROCK_SHIFTED",
            dataset_version=dataset_version,
        ),
    ]
    generated_bundles = [
        generate_gradient_bundle(dataset_version=dataset_version),
        generate_gradient_bundle(dataset_version=dataset_version, preset="divergence"),
    ]
    for generated_bundle in generated_bundles:
        generated_traces.extend(generated_bundle.member_traces)
    generated_traces.extend(generate_parameter_estimation_traces(dataset_version=dataset_version))
    generated_traces.extend(generate_so3_traces(dataset_version=dataset_version))
    generated_traces.append(
        _generate_optimal_control_history_trace(dataset_version=dataset_version)
    )
    generated_traces.extend(_generate_optimal_control_traces(dataset_version=dataset_version))
    generated_traces.extend(generate_portfolio_uncertainty_traces(dataset_version=dataset_version))
    generated_traces.extend(generate_simulation_constrained_traces(dataset_version=dataset_version))
    generated_traces.extend(generate_bilevel_regression_traces(dataset_version=dataset_version))
    generated_traces.append(generate_hybrid_chattering_trace(dataset_version=dataset_version))
    generated_traces.extend(generate_shape_optimization_traces(dataset_version=dataset_version))
    generated_traces.extend(additional_traces or [])
    generated_traces = [
        trace.model_copy(
            update={
                "scenario_id": {
                    "SCENARIO_GRADIENT_DESCENT_QUADRATIC": "SCENARIO_GD_QUADRATIC",
                }.get(trace.scenario_id, trace.scenario_id)
            }
        )
        for trace in generated_traces
    ]
    index = index.model_copy(
        update={
            "traces": [
                *index.traces,
                *[
                    TraceIndexEntry(
                        trace_id=trace.trace_id,
                        path=f"{trace.trace_id}.json",
                        method_id=trace.method_id,
                        profile_id=trace.profile_id,
                        objective_id=trace.objective_id,
                        scenario_id=trace.scenario_id,
                        title_ja=_trace_title(trace.trace_id, locale="ja"),
                        title_en=_trace_title(trace.trace_id, locale="en"),
                    )
                    for trace in generated_traces
                ],
            ]
        }
    )
    for trace in generated_traces:
        (output_dir / "traces" / f"{trace.trace_id}.json").write_bytes(canonical_trace_bytes(trace))
    _write_json(index_path, index)
    index_bytes = index_path.read_bytes()
    return (
        ManifestTraceAsset(
            contract_version="1.0.0",
            index_version="1.0.0",
            path="traces/index.json",
            bytes=len(index_bytes),
            sha256=sha256(index_bytes).hexdigest(),
        ),
        index,
        generated_traces,
    )


def _trace_title(trace_id: str, *, locale: str) -> str:
    simulation_titles = {
        "pde-state-tolerance-tight": (
            "PDE state solve · tight tolerance",
            "PDE state solve · tight tolerance",
        ),
        "pde-state-tolerance-loose": (
            "PDE state solve · loose tolerance",
            "PDE state solve · loose tolerance",
        ),
        "pde-state-solve-failure": (
            "PDE state solve · failure ledger",
            "PDE state solve · failure ledger",
        ),
    }
    if trace_id in simulation_titles:
        return simulation_titles[trace_id][0 if locale == "ja" else 1]
    parameter_titles = {
        "exponential-fit-trf": (
            "共通診断probe · TRF適用条件",
            "Shared diagnostic probe · TRF applicability",
        ),
        "exponential-fit-trf-poor-init": (
            "共通診断probe · 悪い初期値",
            "Shared diagnostic probe · poor initialization",
        ),
        "exponential-fit-lm": (
            "共通診断probe · LM適用条件",
            "Shared diagnostic probe · LM applicability",
        ),
        "exponential-fit-lbfgsb": (
            "共通診断probe · scalar fallback条件",
            "Shared diagnostic probe · scalar fallback applicability",
        ),
        NOMINAL_TRACE_ID: (
            "nominal配分 · training / held-out診断",
            "Nominal allocation · training / held-out diagnostics",
        ),
        CVAR_TRACE_ID: (
            "CVaR配分 · training / held-out診断",
            "CVaR allocation · training / held-out diagnostics",
        ),
    }
    if trace_id in parameter_titles:
        return parameter_titles[trace_id][0 if locale == "ja" else 1]
    if trace_id.startswith("nelder-mead-"):
        return "Nelder–Meadの幾何操作" if locale == "ja" else "Nelder–Mead geometric operations"
    if trace_id == "binary-knapsack-bnb-complete":
        return "0-1 knapsack: 最適性証明" if locale == "ja" else "0-1 knapsack: optimality proof"
    if trace_id == "binary-knapsack-bnb-budget":
        return "0-1 knapsack: node予算で停止" if locale == "ja" else "0-1 knapsack: node budget"
    if trace_id == "optimal-control-ec020-history":
        return (
            "Direct collocation · state/control diagnostics"
            if locale == "en"
            else "Direct collocation · state/control診断"
        )
    optimal_control_titles = {
        "pendulum-collocation-coarse": (
            "Pendulum swing-up · N=20 mesh診断",
            "Pendulum swing-up · N=20 mesh diagnostics",
        ),
        "pendulum-collocation-refined": (
            "Pendulum swing-up · N=40 mesh感度",
            "Pendulum swing-up · N=40 mesh sensitivity",
        ),
        "pendulum-model-rollout-failure": (
            "Pendulum swing-up · modelずれrollout",
            "Pendulum swing-up · model-mismatch rollout",
        ),
    }
    if trace_id in optimal_control_titles:
        return optimal_control_titles[trace_id][0 if locale == "ja" else 1]
    nested_titles = {
        BILEVEL_EXACT_TRACE_ID: (
            "Bilevel回帰 · exact inner診断",
            "Bilevel regression · exact inner diagnostics",
        ),
        BILEVEL_RELAXED_TRACE_ID: (
            "Bilevel回帰 · finite relaxationの残差",
            "Bilevel regression · finite-relaxation failure",
        ),
        HYBRID_CHATTERING_TRACE_ID: (
            "Hybrid mode discovery · chattering診断",
            "Hybrid mode discovery · chattering ledger",
        ),
    }
    if trace_id in nested_titles:
        return nested_titles[trace_id][0 if locale == "ja" else 1]
    if trace_id == "so3-projected-alignment":
        return "SO(3) · ambient step + QR projection"
    if trace_id == "so3-riemannian-alignment":
        return "SO(3) · Lie algebra update"
    method = trace_id.split("-", maxsplit=1)[0]
    labels = {
        "gradient_descent": ("勾配降下法", "Gradient descent"),
        "momentum": ("モメンタム法", "Momentum"),
        "adam": ("Adam", "Adam"),
    }
    label = labels.get(method, (trace_id, trace_id))
    return label[0 if locale == "ja" else 1]


def _build_visualization_scenario_index(
    traces: list[AlgorithmTrace],
    *,
    surrogate_scenarios: list[VisualizationScenario],
    learning_slice_scenarios: list[VisualizationScenario],
    dataset_version: str,
) -> VisualizationScenarioIndex:
    return VisualizationScenarioIndex(
        contract_version="1.2.0",
        dataset_version=dataset_version,
        scenarios=[
            *[_visualization_scenario(trace) for trace in traces],
            *surrogate_scenarios,
            *learning_slice_scenarios,
        ],
    )


def _localized(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _observable(observable_id: str, ja: str, en: str) -> VisualizationObservable:
    return VisualizationObservable(observable_id=observable_id, label_ja=ja, label_en=en)


def _signal(signal_id: str, ja: str, en: str, *observable_ids: str) -> VisualizationSignal:
    return VisualizationSignal(
        signal_id=signal_id,
        label_ja=ja,
        label_en=en,
        observable_ids=list(observable_ids),
    )


def _step(
    milestone_id: Literal["start", "first_change", "pattern_visible", "termination"],
    ja: str,
    en: str,
    *observable_ids: str,
) -> VisualizationNarrationStep:
    return VisualizationNarrationStep(
        milestone_id=milestone_id,
        title_ja=ja,
        title_en=en,
        observable_ids=list(observable_ids),
    )


def _trace_guided_story(trace: AlgorithmTrace) -> GuidedStory | None:
    if trace.scenario_id == "SCENARIO_GD_QUADRATIC":
        final_index = len(trace.frames) - 1
        return GuidedStory(
            story_version="1.0.0",
            introduction=_localized(
                "勾配、更新vector、次の点を同じframeで結び付けます。",
                "Connect the gradient, update vector, and next point in each frame.",
            ),
            steps=[
                GuidedStoryStep(
                    milestone_id="start",
                    annotation=_localized(
                        "初期点で勾配がどちらを指すかを確認します。",
                        "Inspect the gradient direction at the initial point.",
                    ),
                    frame_index=0,
                    auto_pause=True,
                    focus_target="gradient",
                    viewport_preset="overview",
                    camera_preset=None,
                    playback_speed=1.0,
                    visible_layers=["objective_value", "current_point", "gradient"],
                ),
                GuidedStoryStep(
                    milestone_id="first_change",
                    annotation=_localized(
                        "負の勾配方向のupdateが次の現在点を作ります。",
                        "The update along the negative gradient creates the next point.",
                    ),
                    frame_index=min(1, final_index),
                    auto_pause=True,
                    focus_target="update_vector",
                    viewport_preset="decision",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=[
                        "objective_value",
                        "current_point",
                        "gradient",
                        "update_vector",
                    ],
                ),
                GuidedStoryStep(
                    milestone_id="pattern_visible",
                    annotation=_localized(
                        "細長い谷を横切る振動と目的値の減少を同時に読みます。",
                        "Read cross-valley oscillation together with objective decrease.",
                    ),
                    frame_index=min(4, final_index),
                    auto_pause=True,
                    focus_target="current_point",
                    viewport_preset="trajectory",
                    camera_preset=None,
                    playback_speed=1.0,
                    visible_layers=["objective_value", "current_point", "update_vector"],
                ),
                GuidedStoryStep(
                    milestone_id="termination",
                    annotation=_localized(
                        "best-so-farと終了条件を、この固定presetの結果として確認します。",
                        "Inspect best-so-far and stopping under this fixed preset.",
                    ),
                    frame_index=final_index,
                    auto_pause=True,
                    focus_target="objective_value",
                    viewport_preset="terminal",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=["objective_value", "current_point"],
                ),
            ],
            summary=_localized(
                "勾配降下法ではgradientからupdateを作り、目的値を下げる方向へ点を移します。",
                "Gradient descent converts gradients into updates that move toward "
                "lower objective values.",
            ),
        )
    if trace.scenario_id == "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE":
        final_index = len(trace.frames) - 1
        return GuidedStory(
            story_version="1.0.0",
            introduction=_localized(
                "node、bound、incumbent、枝刈りを証明完了まで追います。",
                "Follow nodes, bounds, the incumbent, and pruning until proof completes.",
            ),
            steps=[
                GuidedStoryStep(
                    milestone_id="start",
                    annotation=_localized(
                        "root nodeの上界を確認します。", "Inspect the root bound."
                    ),
                    frame_index=0,
                    auto_pause=True,
                    focus_target="global_bound",
                    viewport_preset="overview",
                    camera_preset=None,
                    playback_speed=1.0,
                    visible_layers=["search_nodes", "global_bound"],
                ),
                GuidedStoryStep(
                    milestone_id="first_change",
                    annotation=_localized(
                        "最初のbranchで探索候補が二つに分かれます。",
                        "The first branch splits the search into two candidates.",
                    ),
                    frame_index=min(1, final_index),
                    auto_pause=True,
                    focus_target="search_nodes",
                    viewport_preset="branch",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=["search_nodes", "global_bound"],
                ),
                GuidedStoryStep(
                    milestone_id="pattern_visible",
                    annotation=_localized(
                        "incumbentより改善不能なsubtreeをboundで捨てます。",
                        "A bound removes a subtree that cannot improve the incumbent.",
                    ),
                    frame_index=max(1, round(final_index * 0.6)),
                    auto_pause=True,
                    focus_target="prune_reason",
                    viewport_preset="pruning",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=["search_nodes", "global_bound", "incumbent", "prune_reason"],
                ),
                GuidedStoryStep(
                    milestone_id="termination",
                    annotation=_localized(
                        "open nodeがなくなり、incumbentとboundの一致で最適性を証明します。",
                        "No open nodes remain; matching incumbent and bound proves optimality.",
                    ),
                    frame_index=final_index,
                    auto_pause=True,
                    focus_target="incumbent",
                    viewport_preset="terminal",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=["search_nodes", "global_bound", "incumbent"],
                ),
            ],
            summary=_localized(
                "Branch-and-Boundは全列挙せず、boundとincumbentで不要なsubtreeを除きます。",
                "Branch-and-Bound avoids full enumeration by pruning with bounds and an incumbent.",
            ),
        )
    if trace.scenario_id != "SCENARIO_NM_QUADRATIC":
        return None
    final_index = len(trace.frames) - 1
    first_change = next(
        (
            frame.frame_index
            for frame in trace.frames
            if frame.event_type not in {"initialize", "order"}
        ),
        min(1, final_index),
    )
    pattern_index = next(
        (
            frame.frame_index
            for frame in trace.frames[first_change + 1 :]
            if frame.decision == "accepted"
        ),
        max(first_change, round(final_index * 0.55)),
    )
    return GuidedStory(
        story_version="1.0.0",
        introduction=_localized(
            "4つのcueで、初期simplexから終了判断までを順に追います。",
            "Follow four cues from the initial simplex to the terminal decision.",
        ),
        steps=[
            GuidedStoryStep(
                milestone_id="start",
                annotation=_localized(
                    "3頂点の位置とbest / worstの役割を先に確認します。",
                    "First locate the three vertices and identify best and worst.",
                ),
                frame_index=0,
                auto_pause=True,
                focus_target="simplex_vertices",
                viewport_preset="overview",
                camera_preset=None,
                playback_speed=1.0,
                visible_layers=["objective_value", "simplex_vertices"],
            ),
            GuidedStoryStep(
                milestone_id="first_change",
                annotation=_localized(
                    "worstを重心の反対側へ動かし、候補を受理する根拠を見ます。",
                    "Move the worst point across the centroid and inspect the decision.",
                ),
                frame_index=first_change,
                auto_pause=True,
                focus_target="accepted_operation",
                viewport_preset="decision",
                camera_preset=None,
                playback_speed=0.5,
                visible_layers=[
                    "objective_value",
                    "simplex_vertices",
                    "accepted_operation",
                ],
            ),
            GuidedStoryStep(
                milestone_id="pattern_visible",
                annotation=_localized(
                    "受理された操作でsimplexと最良値がどう更新されるかを結び付けます。",
                    "Connect an accepted operation to the updated simplex and best value.",
                ),
                frame_index=pattern_index,
                auto_pause=True,
                focus_target="simplex_vertices",
                viewport_preset="trajectory",
                camera_preset=None,
                playback_speed=1.0,
                visible_layers=[
                    "objective_value",
                    "simplex_vertices",
                    "accepted_operation",
                ],
            ),
            GuidedStoryStep(
                milestone_id="termination",
                annotation=_localized(
                    "最終simplexの大きさと終了理由を確認し、一般的性能の証明ではないと切り分けます。",
                    "Inspect the final simplex and stop reason without generalizing performance.",
                ),
                frame_index=final_index,
                auto_pause=True,
                focus_target="objective_value",
                viewport_preset="terminal",
                camera_preset=None,
                playback_speed=0.5,
                visible_layers=["objective_value", "simplex_vertices"],
            ),
        ],
        summary=_localized(
            "Nelder–Meadは勾配ではなく、simplexの候補生成と受理判断で探索を進めます。",
            "Nelder–Mead advances through simplex proposals and decisions, not gradients.",
        ),
    )


def _trace_lesson(
    trace: AlgorithmTrace,
    *,
    is_divergence: bool,
    is_nelder_mead: bool,
    is_search_tree: bool,
    is_optimal_control: bool,
) -> VisualizationLesson:
    if trace.profile_id == SIMULATION_CONSTRAINED_PROFILE_ID:
        is_failure = trace.scenario_id == PDE_FAILURE_SCENARIO_ID
        is_loose = trace.scenario_id == PDE_LOOSE_SCENARIO_ID
        counterpart = PDE_TIGHT_SCENARIO_ID if is_loose or is_failure else PDE_LOOSE_SCENARIO_ID
        return VisualizationLesson(
            learning_objective=_localized(
                "design更新、state solve、adjoint solve、失敗statusを同じsimulator-call軸で読む",
                "Read design updates, state solves, adjoint solves, and failure status "
                "on one simulator-call axis",
            ),
            misconception=_localized(
                "state solveの失敗を大きなobjective値へ置き換えれば、"
                "失敗原因と勾配整合性を確認しなくてよい",
                "Replacing a failed state solve with a large objective removes the need "
                "to inspect failure cause and gradient consistency",
            ),
            expected_phenomenon_ja=(
                "preconditioner failureではobjectiveを作らず、state/adjoint残差と"
                "solver statusを保持する"
                if is_failure
                else "loose toleranceは線形反復を減らす一方、離散objectiveの改善と"
                "state/adjoint整合性を同時には保証しない"
                if is_loose
                else "tight toleranceはstate/adjoint残差を抑える一方、線形反復costが増える"
            ),
            expected_phenomenon_en=(
                "A preconditioner failure produces no objective and retains state/adjoint "
                "residuals and solver status"
                if is_failure
                else "A loose tolerance reduces linear iterations without guaranteeing "
                "state/adjoint consistency alongside discrete-objective progress"
                if is_loose
                else "A tight tolerance controls state/adjoint residuals at higher "
                "linear-iteration cost"
            ),
            success_signals=[
                _signal(
                    "state_and_adjoint_cost_visible",
                    "state/adjoint残差とそれぞれの線形反復数をobjectiveから分けて確認できる",
                    "State/adjoint residuals and their linear iterations remain separate "
                    "from the objective",
                    "state_residual",
                    "adjoint_residual",
                    "state_linear_iterations",
                    "adjoint_linear_iterations",
                )
            ],
            failure_signals=[
                _signal(
                    "failed_evaluation_is_explicit",
                    "state solve失敗にobjective penaltyを捏造せずfailed statusを残す",
                    "A state-solve failure remains failed instead of becoming a synthetic "
                    "objective penalty",
                    "evaluation_status",
                    "state_residual",
                )
            ],
            primary_observables=[
                _observable("objective_value", "離散objective", "discrete objective"),
                _observable("state_residual", "state残差", "state residual"),
                _observable("adjoint_residual", "adjoint残差", "adjoint residual"),
            ],
            secondary_observables=[
                _observable("state_linear_iterations", "state線形反復", "state linear iterations"),
                _observable(
                    "adjoint_linear_iterations",
                    "adjoint線形反復",
                    "adjoint linear iterations",
                ),
                _observable("evaluation_status", "evaluation status", "evaluation status"),
            ],
            narration_steps=[
                _step(
                    "start",
                    "design・state・adjointの役割を分ける",
                    "Separate design, state, and adjoint roles",
                    "objective_value",
                    "state_residual",
                    "adjoint_residual",
                ),
                _step(
                    "first_change",
                    "最初のstate/adjoint solve costを読む",
                    "Read the first state/adjoint solve cost",
                    "state_linear_iterations",
                    "adjoint_linear_iterations",
                ),
                _step(
                    "pattern_visible",
                    "toleranceとresidual/costのtrade-offを読む",
                    "Read the tolerance trade-off between residual and cost",
                    "state_residual",
                    "adjoint_residual",
                    "state_linear_iterations",
                ),
                _step(
                    "termination",
                    "終了statusとclaim scopeを確認",
                    "Inspect termination status and claim scope",
                    "evaluation_status",
                    "state_residual",
                ),
            ],
            comparison_role=(
                "failure_contrast"
                if is_failure
                else "sensitivity_variant"
                if is_loose
                else "primary_example"
            ),
            prerequisite_concept_ids=["concept.pde-constrained-optimization"],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="連続PDEの最適解は示さず、固定mesh上の残差とcostだけを比較する。",
                note_en=(
                    "No continuous-PDE optimum is shown; only fixed-mesh residuals and "
                    "costs are contrasted."
                ),
            ),
            static_summary=_localized(
                "固定meshのdesign・state・adjoint ledgerで、solver tolerance、残差、"
                "線形反復、失敗statusを並べる。",
                "Align solver tolerance, residuals, linear iterations, and failure status "
                "in a fixed-mesh design/state/adjoint ledger.",
            ),
            text_alternative=_localized(
                "各simulator callの離散objective、state/adjoint残差、線形反復数、"
                "failure statusを列挙する。",
                "List discrete objective, state/adjoint residuals, linear iterations, "
                "and failure status for every simulator call.",
            ),
            derived_media_caption=_localized(
                "PDE制約付き最適化のstate/adjoint cost ledger",
                "State/adjoint cost ledger for PDE-constrained optimization",
            ),
            limitations_ja=(
                "8×4固定meshの決定的教材であり、連続modelの精度、mesh独立性、実runtime、"
                "preconditionerの一般性能、outer optimizerの順位を保証しない。"
            ),
            limitations_en=(
                "A deterministic 8x4 fixed-mesh lesson; it does not establish "
                "continuous-model accuracy, mesh independence, real runtime, general "
                "preconditioner performance, or outer-optimizer ranking."
            ),
        )
    if is_optimal_control and trace.objective_id == "INSTANCE_PENDULUM_SWING_UP_EC020":
        is_refined_mesh = trace.scenario_id == "SCENARIO_PENDULUM_SWING_UP_MESH_40"
        is_model_mismatch = trace.scenario_id == "SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH"
        mesh_nodes = trace.parameters.get("mesh_nodes")
        if isinstance(mesh_nodes, bool) or not isinstance(mesh_nodes, int):
            raise ValueError(f"optimal-control trace {trace.trace_id} has no mesh interval count")
        comparison_role: Literal[
            "primary_example", "sensitivity_variant", "failure_contrast", "baseline"
        ]
        if is_model_mismatch:
            expected_ja = (
                "modelを変えたvalidation rolloutでは、NLPのdefectが小さくても"
                "path違反と終端誤差が残る"
            )
            expected_en = (
                "A validation rollout under model mismatch can retain path and terminal "
                "error even when the NLP defect is small"
            )
            signal_id = "model_validation_failure"
            signal_ja = "modelずれrolloutでpath違反と終端誤差が残る"
            signal_en = "Path and terminal error remain in the model-mismatch rollout"
            comparison_role = "failure_contrast"
            recommended = ["SCENARIO_PENDULUM_SWING_UP_MESH_20"]
        else:
            expected_ja = (
                "meshを細かくすると再構成path違反が変わるが、"
                "有限meshだけで連続時間可行とは判定できない"
                if is_refined_mesh
                else "objectiveとnode上のdefectが下がっても、"
                "区間再構成のpath違反が同時に消えるとは限らない"
            )
            expected_en = (
                "A finer mesh changes reconstructed path violation, but a finite mesh "
                "does not establish continuous-time feasibility"
                if is_refined_mesh
                else "Lower objective and node defects do not necessarily remove "
                "reconstructed between-point path violations"
            )
            signal_id = "mesh_feasibility_limit"
            signal_ja = "mesh上のdefectが小さくても区間内の再構成・高精度simulationが別途必要になる"
            signal_en = (
                "Small mesh defects still require interval reconstruction and "
                "high-fidelity simulation"
            )
            comparison_role = "sensitivity_variant" if is_refined_mesh else "primary_example"
            recommended = (
                ["SCENARIO_PENDULUM_SWING_UP_MESH_20"]
                if is_refined_mesh
                else [
                    "SCENARIO_PENDULUM_SWING_UP_MESH_40",
                    "SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH",
                ]
            )
        return VisualizationLesson(
            learning_objective=_localized(
                "state・control・dynamics defect・path violationを同じ評価軸で読む",
                "Read state, control, dynamics defects, and path violations on one evaluation axis",
            ),
            misconception=_localized(
                "NLPがsuccessならmeshの間でもtrajectoryが可行で、連続時間の安全性も保証される",
                "An NLP success status guarantees feasibility between mesh points and "
                "continuous-time safety",
            ),
            expected_phenomenon_ja=expected_ja,
            expected_phenomenon_en=expected_en,
            success_signals=[
                _signal(
                    "trajectory_diagnostics_visible",
                    "state・controlとdynamics defect・path violationを同じevaluationで確認できる",
                    "State/control and dynamics/path diagnostics are visible at the same "
                    "evaluation",
                    "state_norm",
                    "control_effort",
                    "dynamics_defect",
                    "path_violation",
                )
            ],
            failure_signals=[
                _signal(
                    signal_id,
                    signal_ja,
                    signal_en,
                    "dynamics_defect",
                    "path_violation",
                )
            ],
            primary_observables=[
                _observable("state_norm", "state norm", "state norm"),
                _observable("control_effort", "control effort", "control effort"),
                _observable("dynamics_defect", "dynamics defect", "dynamics defect"),
            ],
            secondary_observables=[
                _observable("path_violation", "path violation", "path violation"),
                _observable("objective_value", "目的関数値", "objective value"),
            ],
            narration_steps=[
                _step(
                    "start",
                    "初期trajectoryとcontrolを確認",
                    "Inspect the initial trajectory and control",
                    "state_norm",
                    "control_effort",
                ),
                _step(
                    "first_change",
                    "最初のdynamics defectの変化を追う",
                    "Follow the first dynamics-defect change",
                    "dynamics_defect",
                    "objective_value",
                ),
                _step(
                    "pattern_visible",
                    "path violationとobjectiveを分けて読む",
                    "Separate path violations from objective progress",
                    "path_violation",
                    "objective_value",
                ),
                _step(
                    "termination",
                    "mesh上の結果と連続時間の限界を確認",
                    "Inspect the mesh result and continuous-time limitation",
                    "dynamics_defect",
                    "path_violation",
                ),
            ],
            comparison_role=comparison_role,
            prerequisite_concept_ids=["CONCEPT_TRAJECTORY_VARIABLE", "CONCEPT_DYNAMICS_DEFECT"],
            recommended_next_scenario_ids=recommended,
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja=(
                    "連続時間の最適性・安全性は表示しない。mesh refinementと再構成で別途検証する。"
                ),
                note_en=(
                    "Continuous-time optimality and safety are not shown; validate them "
                    "with refinement and reconstruction."
                ),
            ),
            static_summary=_localized(
                "pendulum swing-upのstate、control、dynamics defect、"
                f"再構成path violationをN={mesh_nodes}の評価履歴として並べる。",
                "Align pendulum state, control, dynamics defects, and reconstructed "
                f"path violations for the N={mesh_nodes} history.",
            ),
            text_alternative=_localized(
                "各evaluationのstate norm、control effort、dynamics defect、path violation、"
                "objectiveを列挙する。",
                "List state norm, control effort, dynamics defect, path violation, and "
                "objective at each evaluation.",
            ),
            derived_media_caption=_localized(
                f"pendulum direct collocationのN={mesh_nodes}診断履歴",
                f"N={mesh_nodes} diagnostics for pendulum direct collocation",
            ),
            limitations_ja=(
                f"N={mesh_nodes}の固定meshによる教育用履歴であり、連続時間の可行性・"
                "実機安全性・動力学modelの妥当性やsolverの一般性能を保証しない"
            ),
            limitations_en=(
                f"A fixed N={mesh_nodes} educational mesh history; it does not guarantee "
                "continuous-time feasibility, hardware safety, model validity, or "
                "general solver performance"
            ),
        )
    if is_optimal_control:
        return VisualizationLesson(
            learning_objective=_localized(
                "state・control・dynamics defect・path violationを同じ評価軸で読む",
                "Read state, control, dynamics defects, and path violations on one evaluation axis",
            ),
            misconception=_localized(
                "NLPがsuccessならmeshの間でもtrajectoryが可行で、連続時間の安全性も保証される",
                "An NLP success status guarantees feasibility between mesh points and "
                "continuous-time safety",
            ),
            expected_phenomenon_ja=(
                "objectiveだけでなくdynamics defectとconstraint marginが同時に改善するとは限らない"
            ),
            expected_phenomenon_en=(
                "Objective progress does not by itself guarantee smaller dynamics defects "
                "or constraint margins"
            ),
            success_signals=[
                _signal(
                    "trajectory_diagnostics_visible",
                    "state・controlとdynamics defect・path violationを同じevaluationで確認できる",
                    "State/control and dynamics/path diagnostics are visible at the same "
                    "evaluation",
                    "state_norm",
                    "control_effort",
                    "dynamics_defect",
                    "path_violation",
                )
            ],
            failure_signals=[
                _signal(
                    "mesh_feasibility_limit",
                    "mesh上のdefectが小さくても区間内の再構成・高精度simulationが別途必要になる",
                    "Small mesh defects still require interval reconstruction and "
                    "high-fidelity simulation",
                    "dynamics_defect",
                    "path_violation",
                )
            ],
            primary_observables=[
                _observable("state_norm", "state norm", "state norm"),
                _observable("control_effort", "control effort", "control effort"),
                _observable("dynamics_defect", "dynamics defect", "dynamics defect"),
            ],
            secondary_observables=[
                _observable("path_violation", "path violation", "path violation"),
                _observable("objective_value", "目的関数値", "objective value"),
            ],
            narration_steps=[
                _step(
                    "start",
                    "初期trajectoryとcontrolを確認",
                    "Inspect the initial trajectory and control",
                    "state_norm",
                    "control_effort",
                ),
                _step(
                    "first_change",
                    "最初のdynamics defectの変化を追う",
                    "Follow the first dynamics-defect change",
                    "dynamics_defect",
                    "objective_value",
                ),
                _step(
                    "pattern_visible",
                    "path violationとobjectiveを分けて読む",
                    "Separate path violations from objective progress",
                    "path_violation",
                    "objective_value",
                ),
                _step(
                    "termination",
                    "mesh上の結果と連続時間の限界を確認",
                    "Inspect the mesh result and continuous-time limitation",
                    "dynamics_defect",
                    "path_violation",
                ),
            ],
            comparison_role="primary_example",
            prerequisite_concept_ids=["CONCEPT_TRAJECTORY_VARIABLE", "CONCEPT_DYNAMICS_DEFECT"],
            recommended_next_scenario_ids=[],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja=(
                    "連続時間の最適性・安全性は表示しない。mesh refinementと再構成で別途検証する。"
                ),
                note_en=(
                    "Continuous-time optimality and safety are not shown; validate them "
                    "with refinement and reconstruction."
                ),
            ),
            static_summary=_localized(
                "state、control、dynamics defect、path violationをmeshの評価履歴として並べる。",
                "Align state, control, dynamics defects, and path violations as a mesh "
                "evaluation history.",
            ),
            text_alternative=_localized(
                "各evaluationのstate norm、control effort、dynamics defect、path violation、"
                "objectiveを列挙する。",
                "List state norm, control effort, dynamics defect, path violation, and "
                "objective at each evaluation.",
            ),
            derived_media_caption=_localized(
                "direct collocationのstate・control・制約診断履歴",
                "State, control, and constraint diagnostics for direct collocation",
            ),
            limitations_ja="N=20の固定meshによる教育用履歴であり、連続時間の可行性・実機安全性・動力学modelの妥当性やsolverの一般性能を保証しない",
            limitations_en=(
                "A fixed N=20 educational mesh history; it does not guarantee "
                "continuous-time feasibility, hardware safety, model validity, or "
                "general solver performance"
            ),
        )
    if trace.objective_id == "INSTANCE_EXPONENTIAL_DECAY_FIT_3P":
        is_poor_initialization = trace.scenario_id == POOR_INITIALIZATION_SCENARIO_ID
        is_primary = trace.scenario_id == PRIMARY_SCENARIO_ID
        role: Literal["sensitivity_variant", "primary_example", "baseline"] = (
            "sensitivity_variant"
            if is_poor_initialization
            else "primary_example"
            if is_primary
            else "baseline"
        )
        next_id = PRIMARY_SCENARIO_ID if not is_primary else POOR_INITIALIZATION_SCENARIO_ID
        method_condition = {
            PRIMARY_SCENARIO_ID: "共通診断stateに対するTRFのbounds・残差vector適用条件",
            POOR_INITIALIZATION_SCENARIO_ID: "同じ診断probeをa=0から始める初期値感度",
            LM_SCENARIO_ID: "共通診断stateに対するLMのbounds非active適用条件",
            LBFGSB_SCENARIO_ID: "共通診断stateに対するscalar目的fallback適用条件",
        }[trace.scenario_id]
        return VisualizationLesson(
            learning_objective=_localized(
                "parameter推定値、残差norm、Jacobian rankを同じevaluation軸で読む",
                "Read parameter estimates, residual norm, and Jacobian rank on one evaluation axis",
            ),
            misconception=(
                _localized(
                    "残差二乗和が下がれば、悪い初期値やrank不足を確認しなくてよい",
                    "A decreasing residual sum of squares does not remove the need "
                    "to check initialization and rank",
                )
                if is_poor_initialization
                else None
            ),
            expected_phenomenon_ja=f"{method_condition}として、共通probeのmetric履歴を読みます。",
            expected_phenomenon_en=(
                "Read one solver-independent diagnostic-probe history through the stated "
                "applicability lens."
            ),
            success_signals=[
                _signal(
                    "residual_and_rank_visible",
                    "残差normとJacobian rankをparameter推定値と同時に確認できる",
                    "Residual norm and Jacobian rank remain visible with the parameter estimate",
                    "parameter_estimate",
                    "residual_norm",
                    "jacobian_rank",
                )
            ],
            failure_signals=(
                [
                    _signal(
                        "rank_deficient_start",
                        "初期Jacobian rankが2となり、probe終了時も残差が残る",
                        "The initial Jacobian rank is two and residual error remains "
                        "when the probe ends",
                        "jacobian_rank",
                        "residual_norm",
                        "parameter_error",
                    )
                ]
                if is_poor_initialization
                else []
            ),
            primary_observables=[
                _observable("parameter_estimate", "parameter推定値", "parameter estimate"),
                _observable("residual_norm", "残差norm", "residual norm"),
                _observable("jacobian_rank", "Jacobian rank", "Jacobian rank"),
            ],
            secondary_observables=[
                _observable("gradient_norm", "gradient norm", "gradient norm"),
                _observable("parameter_error", "既知truthからの距離", "distance from known truth"),
            ],
            narration_steps=[
                _step(
                    "start",
                    "初期parameterとrankを確認",
                    "Inspect initial parameters and rank",
                    "parameter_estimate",
                    "jacobian_rank",
                ),
                _step(
                    "first_change",
                    "最初の残差変化を追う",
                    "Follow the first residual change",
                    "parameter_estimate",
                    "residual_norm",
                ),
                _step(
                    "pattern_visible",
                    "rankと収束metricを並べる",
                    "Align rank and convergence metrics",
                    "residual_norm",
                    "gradient_norm",
                    "jacobian_rank",
                ),
                _step(
                    "termination",
                    "最終評価の誤差とstatusを確認",
                    "Inspect error and status at the final evaluation",
                    "residual_norm",
                    "parameter_error",
                ),
            ],
            comparison_role=role,
            prerequisite_concept_ids=[],
            recommended_next_scenario_ids=[next_id],
            known_reference_display=KnownReferenceDisplay(
                policy="show",
                note_ja="合成dataを生成したtruth [1.8, 0.7, 0.25] を教材診断にだけ使う",
                note_en=(
                    "Use the synthetic-data truth [1.8, 0.7, 0.25] only for teaching diagnostics"
                ),
            ),
            static_summary=_localized(
                f"{method_condition}。20観測に同じsolver非依存probeを適用し、metricを表示します。",
                "Apply one solver-independent probe to the same 20 observations and show "
                "its metrics.",
            ),
            text_alternative=_localized(
                "各evaluationの [a, k, c]、残差norm、gradient norm、Jacobian rank、"
                "truthからの距離を列挙します。",
                "List [a, k, c], residual norm, gradient norm, Jacobian rank, and "
                "distance from truth at every evaluation.",
            ),
            derived_media_caption=_localized(
                "指数減衰fitの共通診断probeによるresidual・rank metric履歴",
                "Residual and rank history from the shared exponential-fit diagnostic probe",
            ),
            limitations_ja=(
                "deterministic damped Gauss–Newton診断probeであり、member solverは実行して"
                "いません。SciPy/Ceresの内部反復、到達解、速度、一般性能、実dataの"
                "parameter識別性を表しません。"
            ),
            limitations_en=(
                "A deterministic damped Gauss-Newton diagnostic probe; no member solver was "
                "executed. It does not represent SciPy/Ceres internals, attained solutions, "
                "speed, general performance, or real-data parameter identifiability."
            ),
        )
    if is_search_tree:
        budget_stop = trace.terminal_status == "budget_exhausted"
        return VisualizationLesson(
            learning_objective=_localized(
                "上界とincumbentが探索範囲を狭める過程を読む",
                "Read how bounds and the incumbent reduce the search space",
            ),
            misconception=(
                _localized(
                    "予算で止まった探索木のincumbentは最適性が証明されている",
                    "An incumbent from a budget-stopped tree is proven optimal",
                )
                if budget_stop
                else None
            ),
            expected_phenomenon_ja="枝分かれ、上界、incumbent更新、2種類の枝刈りを追跡する",
            expected_phenomenon_en=(
                "Observe branching, bounds, incumbent updates, and two pruning reasons"
            ),
            success_signals=[
                _signal(
                    "subtree_pruned",
                    "上界または実行不可能性でsubtreeが枝刈りされる",
                    "A subtree is pruned by its bound or infeasibility",
                    "search_nodes",
                    "prune_reason",
                )
            ],
            failure_signals=(
                [
                    _signal(
                        "proof_gap_remains",
                        "node予算到達時に未探索nodeとbound gapが残る",
                        "Unexplored nodes and a bound gap remain at the node budget",
                        "search_nodes",
                        "global_bound",
                        "incumbent",
                    )
                ]
                if budget_stop
                else []
            ),
            primary_observables=[
                _observable("search_nodes", "探索node", "search nodes"),
                _observable("global_bound", "大域上界", "global bound"),
                _observable("incumbent", "暫定解", "incumbent"),
            ],
            secondary_observables=[_observable("prune_reason", "枝刈り理由", "pruning reason")],
            narration_steps=[
                _step("start", "root nodeから開始", "Start from the root node", "search_nodes"),
                _step(
                    "first_change",
                    "最初のbranchとbound更新",
                    "First branch and bound update",
                    "search_nodes",
                    "global_bound",
                ),
                _step(
                    "pattern_visible",
                    "incumbent更新と枝刈りを比較",
                    "Compare incumbent updates and pruning",
                    "incumbent",
                    "prune_reason",
                ),
                _step(
                    "termination",
                    "証明完了か予算停止かを確認",
                    "Check whether proof completed or the budget stopped the run",
                    "global_bound",
                    "incumbent",
                ),
            ],
            comparison_role="failure_contrast" if budget_stop else "primary_example",
            prerequisite_concept_ids=["CONCEPT_BRANCH_AND_BOUND", "CONCEPT_INCUMBENT"],
            recommended_next_scenario_ids=[
                "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE"
                if budget_stop
                else "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET"
            ],
            known_reference_display=KnownReferenceDisplay(
                policy="show",
                note_ja="既知の最適値とbound gapを表示する",
                note_en="Show the known optimum and bound gap",
            ),
            static_summary=_localized(
                "探索木でnode、bound、incumbent、枝刈り理由を同時に追う。",
                "Follow nodes, bounds, the incumbent, and pruning reasons together.",
            ),
            text_alternative=_localized(
                "各milestoneで展開済みnode、global bound、incumbent、停止理由を読み上げる。",
                "At each milestone, report explored nodes, global bound, incumbent, "
                "and stop reason.",
            ),
            derived_media_caption=_localized(
                "Branch-and-Boundの探索木: boundとincumbentによる枝刈り",
                "Branch-and-Bound tree: pruning by bounds and the incumbent",
            ),
            limitations_ja=(
                "4変数の教育用Branch-and-Boundであり、実solverのcut生成やpresolve性能は再現しない"
            ),
            limitations_en=(
                "A four-variable educational Branch-and-Bound; solver cuts and presolve are omitted"
            ),
        )

    if is_nelder_mead:
        shifted = trace.scenario_id.endswith("_SHIFTED")
        base_id = trace.scenario_id.removesuffix("_SHIFTED")
        next_id = base_id if shifted else f"{trace.scenario_id}_SHIFTED"
        return VisualizationLesson(
            learning_objective=_localized(
                "単体の幾何操作と候補の受理判断を結び付けて読む",
                "Connect simplex geometry with candidate acceptance decisions",
            ),
            misconception=None,
            expected_phenomenon_ja="反射・拡大・収縮・縮小で単体が移動する",
            expected_phenomenon_en=(
                "The simplex moves by reflection, expansion, contraction, and shrinkage"
            ),
            success_signals=[
                _signal(
                    "accepted_simplex_move",
                    "受理された操作で単体と最良値が更新される",
                    "An accepted operation updates the simplex and best value",
                    "simplex_vertices",
                    "accepted_operation",
                    "objective_value",
                )
            ],
            failure_signals=[],
            primary_observables=[
                _observable("simplex_vertices", "単体の頂点", "simplex vertices"),
                _observable("accepted_operation", "受理操作", "accepted operation"),
            ],
            secondary_observables=[_observable("objective_value", "目的関数値", "objective value")],
            narration_steps=[
                _step(
                    "start", "初期simplexを確認", "Inspect the initial simplex", "simplex_vertices"
                ),
                _step(
                    "first_change",
                    "最初の候補と受理判断",
                    "First candidate and acceptance decision",
                    "simplex_vertices",
                    "accepted_operation",
                ),
                _step(
                    "pattern_visible",
                    "単体の移動と縮小を追跡",
                    "Follow simplex motion and contraction",
                    "simplex_vertices",
                    "objective_value",
                ),
                _step(
                    "termination",
                    "最終simplexと終了理由",
                    "Final simplex and termination reason",
                    "simplex_vertices",
                    "objective_value",
                ),
            ],
            comparison_role="sensitivity_variant" if shifted else "primary_example",
            prerequisite_concept_ids=["CONCEPT_DERIVATIVE_FREE", "CONCEPT_SIMPLEX"],
            recommended_next_scenario_ids=[next_id],
            known_reference_display=KnownReferenceDisplay(
                policy="show",
                note_ja="問題instanceの既知最適点をgoal cueとして表示する",
                note_en="Show the problem instance optimum as a goal cue",
            ),
            static_summary=_localized(
                "等高線上でsimplex頂点、候補点、受理操作、最良値の変化を示す。",
                "Show simplex vertices, candidate, accepted operation, and best-value "
                "changes on contours.",
            ),
            text_alternative=_localized(
                "各frameの頂点順位、候補点、操作、受理結果、最良値を順に読む。",
                "Report vertex ranks, candidate, operation, decision, and best value "
                "for each frame.",
            ),
            derived_media_caption=_localized(
                "Nelder–Mead: simplexの幾何操作と受理判断",
                "Nelder–Mead: simplex geometry and acceptance decisions",
            ),
            limitations_ja="2次元の教育用決定論的実行であり、一般的な性能優劣を示さない",
            limitations_en="A deterministic 2D educational run, not a general performance ranking",
        )

    method_label = trace.method_id.removeprefix("M_").replace("_", " ").title()
    standard_and_failure_ids = {
        "M_GRADIENT_DESCENT": (
            "SCENARIO_GD_QUADRATIC",
            "SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE",
        ),
        "M_MOMENTUM_SGD": (
            "SCENARIO_MOMENTUM_QUADRATIC",
            "SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE",
        ),
        "M_ADAM": ("SCENARIO_ADAM_QUADRATIC", "SCENARIO_ADAM_QUADRATIC_DIVERGENCE"),
    }
    standard_id, failure_id = standard_and_failure_ids[trace.method_id]
    counterpart = standard_id if is_divergence else failure_id
    return VisualizationLesson(
        learning_objective=_localized(
            "勾配、更新vector、軌跡、目的値を同じevaluationで読む",
            "Read gradient, update vector, trajectory, and objective at the same evaluation",
        ),
        misconception=(
            _localized(
                "勾配の反対へ進めば学習率に関係なく目的値は下がり続ける",
                "Moving against the gradient always decreases the objective regardless "
                "of step size",
            )
            if is_divergence
            else None
        ),
        expected_phenomenon_ja="学習率と更新則により谷での振動・発散の仕方が変わる",
        expected_phenomenon_en=(
            "Learning rate and update rules change oscillation and divergence in the valley"
        ),
        success_signals=[
            _signal(
                "trajectory_response_visible",
                "gradientとupdateの向きが次の現在点へ反映される",
                "Gradient and update directions are reflected in the next current point",
                "current_point",
                "gradient",
                "update_vector",
            )
        ],
        failure_signals=(
            [
                _signal(
                    "objective_growth",
                    "更新後に目的値と振幅が増大する",
                    "Objective value and oscillation amplitude grow after updates",
                    "objective_value",
                    "current_point",
                    "update_vector",
                )
            ]
            if is_divergence
            else []
        ),
        primary_observables=[
            _observable("current_point", "現在点", "current point"),
            _observable("gradient", "勾配", "gradient"),
            _observable("update_vector", "更新vector", "update vector"),
        ],
        secondary_observables=[_observable("objective_value", "目的関数値", "objective value")],
        narration_steps=[
            _step(
                "start",
                "初期点と勾配を確認",
                "Inspect initial point and gradient",
                "current_point",
                "gradient",
            ),
            _step(
                "first_change",
                "最初のupdateを追う",
                "Follow the first update",
                "gradient",
                "update_vector",
                "current_point",
            ),
            _step(
                "pattern_visible",
                "谷を横切る振動または発散を読む",
                "Read cross-valley oscillation or divergence",
                "current_point",
                "objective_value",
            ),
            _step(
                "termination",
                "best-so-farと終了理由を確認",
                "Check best-so-far and termination reason",
                "current_point",
                "objective_value",
            ),
        ],
        comparison_role="failure_contrast" if is_divergence else "primary_example",
        prerequisite_concept_ids=["CONCEPT_GRADIENT", "CONCEPT_LEARNING_RATE"],
        recommended_next_scenario_ids=[counterpart],
        known_reference_display=KnownReferenceDisplay(
            policy="show",
            note_ja="既知最適点を軌跡と同じ座標系に表示する",
            note_en="Show the known optimum in the trajectory coordinate system",
        ),
        static_summary=_localized(
            f"{method_label}の現在点、gradient、update、目的値をevaluation軸で同期する。",
            f"Synchronize {method_label} current point, gradient, update, and objective "
            "by evaluation.",
        ),
        text_alternative=_localized(
            "各evaluationの現在点、目的値、gradient、update vector、終了状態を読む。",
            "Report current point, objective, gradient, update vector, and status at "
            "each evaluation.",
        ),
        derived_media_caption=_localized(
            f"{method_label}: 細長い谷での更新軌跡",
            f"{method_label}: update trajectory in an elongated valley",
        ),
        limitations_ja="同一presetの教育用比較であり、一般的な手法の優劣を示さない",
        limitations_en="An educational fixed-preset comparison, not a general method ranking",
    )


def _visualization_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    if trace.profile_id in {SHAPE_OPTIMIZATION_PROFILE_ID, SHAPE_TOPOLOGY_PROFILE_ID}:
        return build_shape_optimization_scenario(trace)
    if trace.profile_id == PORTFOLIO_UNCERTAINTY_PROFILE_ID:
        return build_portfolio_uncertainty_scenario(trace)
    if trace.profile_id in {BILEVEL_PROFILE_ID, HYBRID_PROFILE_ID}:
        return build_nested_solve_scenario(trace)
    if trace.profile_id == SO3_PROFILE_ID:
        return build_so3_scenario(trace)
    is_nelder_mead = trace.profile_id == "PROFILE_NELDER_MEAD_2D"
    is_search_tree = trace.profile_id == "PROFILE_SEARCH_TREE_01"
    is_parameter_estimation = trace.objective_id == "INSTANCE_EXPONENTIAL_DECAY_FIT_3P"
    is_optimal_control = trace.profile_id == "PROFILE_OPTIMAL_CONTROL_GENERIC"
    is_simulation_constrained = trace.profile_id == SIMULATION_CONSTRAINED_PROFILE_ID
    is_divergence = trace.trace_id.endswith("-divergence")
    point = [0.0, 0.0, 0.0, 0.0] if is_search_tree else trace.initial_state.get("point")
    if not isinstance(point, list) or not all(isinstance(value, (int, float)) for value in point):
        raise ValueError(f"trace {trace.trace_id} has no numeric initial condition")
    preset_id = trace.preset.get("preset_id")
    if not isinstance(preset_id, str) or not preset_id.strip():
        raise ValueError(f"trace {trace.trace_id} has no parameter preset ID")
    seed_status = trace.seed.get("status")
    seed_value = trace.seed.get("value")
    if seed_status not in {"fixed", "not_applicable"}:
        raise ValueError(f"trace {trace.trace_id} has unsupported seed status")
    if seed_value is not None and (isinstance(seed_value, bool) or not isinstance(seed_value, int)):
        raise ValueError(f"trace {trace.trace_id} has an invalid seed value")
    renderer_family: RendererFamily = (
        "search_tree"
        if is_search_tree
        else "generic_metric_history"
        if is_parameter_estimation or is_optimal_control or is_simulation_constrained
        else "simplex_geometry"
        if is_nelder_mead
        else "continuous_trajectory"
    )
    observable_ids = (
        ["search_nodes", "global_bound", "incumbent", "prune_reason"]
        if is_search_tree
        else [
            "objective_value",
            "state_residual",
            "adjoint_residual",
            "state_linear_iterations",
            "adjoint_linear_iterations",
            "evaluation_status",
        ]
        if is_simulation_constrained
        else [
            "state_norm",
            "control_effort",
            "dynamics_defect",
            "path_violation",
            "objective_value",
        ]
        if is_optimal_control
        else [
            "parameter_estimate",
            "residual_norm",
            "gradient_norm",
            "jacobian_rank",
            "parameter_error",
        ]
        if is_parameter_estimation
        else ["objective_value", "simplex_vertices", "accepted_operation"]
        if is_nelder_mead
        else ["objective_value", "current_point", "gradient", "update_vector"]
    )
    purpose: Literal["mechanism", "comparison", "failure_contrast", "sensitivity"] = (
        "failure_contrast"
        if trace.scenario_id
        in {PDE_FAILURE_SCENARIO_ID, "SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH"}
        else "sensitivity"
        if trace.scenario_id
        in {
            PDE_LOOSE_SCENARIO_ID,
            POOR_INITIALIZATION_SCENARIO_ID,
            "SCENARIO_PENDULUM_SWING_UP_MESH_40",
        }
        else "mechanism"
        if trace.scenario_id == PDE_TIGHT_SCENARIO_ID
        else "mechanism"
        if trace.scenario_id == PRIMARY_SCENARIO_ID
        else "comparison"
        if is_parameter_estimation
        else "mechanism"
        if is_optimal_control
        else "failure_contrast"
        if is_divergence or (is_search_tree and trace.terminal_status == "budget_exhausted")
        else "mechanism"
        if is_nelder_mead or is_search_tree
        else "comparison"
    )
    payload = canonical_trace_bytes(trace)
    identity_status, canonical_scenario_id = scenario_identity(trace.scenario_id)
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status=identity_status,
        canonical_scenario_id=canonical_scenario_id,
        title_ja=_trace_title(trace.trace_id, locale="ja"),
        title_en=_trace_title(trace.trace_id, locale="en"),
        purpose=purpose,
        problem_definition_id=(
            "PROBLEM_BINARY_KNAPSACK"
            if is_search_tree
            else "PROBLEM_TOPOLOGY_OPTIMIZATION"
            if is_simulation_constrained
            else "PROBLEM_NONLINEAR_LEAST_SQUARES"
            if is_parameter_estimation
            else "PROBLEM_OPTIMAL_CONTROL"
            if is_optimal_control
            else "PROBLEM_CONTINUOUS_UNCONSTRAINED"
        ),
        problem_instance_id=trace.objective_id,
        lesson=_trace_lesson(
            trace,
            is_divergence=is_divergence,
            is_nelder_mead=is_nelder_mead,
            is_search_tree=is_search_tree,
            is_optimal_control=is_optimal_control,
        ),
        guided_story=_trace_guided_story(trace),
        experiment=VisualizationExperiment(
            oracle_policy=(
                ["residual_vector", "jacobian"]
                if is_parameter_estimation
                else ["state_solve", "adjoint_solve"]
                if is_simulation_constrained
                else ["objective_value", "constraint_value", "constraint_jacobian"]
                if is_optimal_control and trace.objective_id == "INSTANCE_PENDULUM_SWING_UP_EC020"
                else ["objective_value"]
                if is_nelder_mead or is_search_tree
                else ["objective_value", "gradient"]
            ),
            initial_condition=VisualizationInitialCondition(
                point=[float(value) for value in point]
            ),
            parameter_preset_id=preset_id,
            seed=VisualizationSeed(status=seed_status, value=seed_value),
            budget=VisualizationBudget(
                metric="oracle_evaluations",
                value=trace.evaluation_budget,
            ),
            stopping=_numeric_record(trace.stopping, owner=f"trace {trace.trace_id} stopping"),
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id=f"RUN_{trace.trace_id.upper().replace('-', '_')}",
                method_id=trace.method_id,
                profile_id=trace.profile_id,
                implementation_mapping_status=trace.implementation_mapping_status,
                implementation_id=trace.implementation_id,
                artifact_id=trace.trace_id,
            )
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="AlgorithmTrace",
            artifact_contract_version=trace.contract_version,
            renderer_family=renderer_family,
            renderer_contract_version="1.0.0",
            observable_ids=observable_ids,
            payload_path=f"traces/{trace.trace_id}.json",
            payload_bytes=len(payload),
            payload_sha256=sha256(payload).hexdigest(),
        ),
        source_ids=trace.source_ids,
        last_verified=(
            "2026-07-19"
            if is_simulation_constrained
            else "2026-07-17"
            if is_parameter_estimation or is_search_tree
            else "2026-07-15"
        ),
    )


def _write_search_tree_artifacts(
    output_dir: Path, *, dataset_version: str
) -> tuple[SearchTreeIndex, list[SearchTreeArtifact]]:
    artifacts = [
        generate_search_tree_artifact(dataset_version=dataset_version, node_stop_limit=9),
        generate_search_tree_artifact(dataset_version=dataset_version, node_stop_limit=4),
    ]
    entries: list[SearchTreeIndexEntry] = []
    for artifact in artifacts:
        artifact_path = f"search-trees/{artifact.artifact_id}.json"
        _write_json(output_dir / artifact_path, artifact)
        fallback_path = output_dir / artifact.static_fallback.path
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        fallback_path.write_text(render_search_tree_svg(artifact), encoding="utf-8", newline="\n")
        entries.append(
            SearchTreeIndexEntry(
                artifact_id=artifact.artifact_id,
                path=artifact_path,
                trace_id=artifact.trace.trace_id,
                scenario_id=artifact.scenario_id,
                artifact_kind=artifact.artifact_kind,
                renderer_family=artifact.renderer_family,
                renderer_contract_version=artifact.renderer_contract_version,
                static_fallback_path=artifact.static_fallback.path,
            )
        )
    index = SearchTreeIndex(dataset_version=dataset_version, artifacts=entries)
    index_path = output_dir / "search-trees/index.json"
    _write_json(index_path, index)
    return index, artifacts


def _numeric_record(value: dict[str, Any], *, owner: str) -> dict[str, bool | int | float]:
    result: dict[str, bool | int | float] = {}
    for key, item in value.items():
        if not isinstance(item, (bool, int, float)):
            raise ValueError(f"{owner}.{key} must be numeric or boolean")
        result[key] = item
    return result


def _dummy_frame(
    *,
    frame_index: int,
    iteration: int,
    evaluations: int,
    event_type: str,
    decision: Literal["accepted", "rejected", "not_applicable"],
    label_ja: str,
    label_en: str,
    points: list[tuple[str, str, str, tuple[float, float], float]],
    best_point_id: str,
    vector_origin: tuple[float, float],
    movement: tuple[float, float],
    explanation: str,
) -> TraceFrame:
    return TraceFrame(
        frame_index=frame_index,
        iteration=iteration,
        oracle_evaluations=evaluations,
        elapsed_steps=frame_index,
        elapsed_time_ms=float(frame_index * 100),
        event_type=event_type,
        decision=decision,
        explanation_key=f"trace.dummy.{event_type}",
        event_label_ja=label_ja,
        event_label_en=label_en,
        keyframe=True,
        points=[
            TracePoint(
                point_id=point_id,
                role="simplex-vertex" if point_id != "trial" else "trial-point",
                coordinates=list(coordinates),
                value=value,
                label_ja=point_label_ja,
                label_en=point_label_en,
            )
            for point_id, point_label_ja, point_label_en, coordinates, value in points
        ],
        vectors=[
            TraceVector(
                vector_id="movement",
                role="movement",
                origin=list(vector_origin),
                components=list(movement),
                label_ja="移動量",
                label_en="Movement",
            )
        ],
        metrics=[
            TraceMetric(
                metric_id="objective",
                label_ja="目的関数値",
                label_en="Objective value",
                value=min(point[4] for point in points),
                unit=None,
            )
        ],
        payload={
            "explanation": explanation,
            "vertices": [point[0] for point in points if point[0] != "trial"],
            "values": {point[0]: point[4] for point in points},
            "best_vertex": best_point_id,
        },
    )


def _build_problem_structure(
    *,
    preset: ViewPresetSeed,
    dataset_version: str,
    generated_at: datetime,
    questions: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    feature_values: list[dict[str, Any]],
    features: list[dict[str, Any]],
    methods: list[dict[str, Any]],
    problems: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> ViewSpec:
    question_by_id = {str(question["question_id"]): question for question in questions}
    expected_question_ids = {
        question_id for group in preset.filter_policy.groups for question_id in group.question_ids
    }
    if set(question_by_id) != expected_question_ids:
        missing = sorted(expected_question_ids - set(question_by_id))
        unexpected = sorted(set(question_by_id) - expected_question_ids)
        raise ValueError(
            "problem-structure question mapping is incomplete; "
            f"missing={missing}, unexpected={unexpected}"
        )

    rules_by_answer: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for rule in rules:
        key = (str(rule["question_id"]), str(rule["answer_condition"]))
        rules_by_answer[key].append(rule)

    feature_value_by_key = {
        (str(value["feature_id"]), str(value["value_code"])): value for value in feature_values
    }

    nodes: list[ViewNode] = [
        ViewNode(
            node_id=f"branch:{group.group_id}",
            node_type="branch",
            label=group.label_ja,
            label_en=group.label_en,
            summary=preset.description_ja,
            display_order=display_order,
            default_collapsed=True,
            emphasis="primary",
            related_entities=[],
        )
        for display_order, group in enumerate(preset.filter_policy.groups)
    ]

    alternative_ids = {
        alternative_id
        for group in preset.filter_policy.groups
        for alternative_id in group.alternative_ids
    }
    alternative_by_id = {
        str(alternative["alternative_id"]): alternative for alternative in alternatives
    }
    for display_order, alternative_id in enumerate(sorted(alternative_ids)):
        alternative = alternative_by_id[alternative_id]
        alternative_id = str(alternative["alternative_id"])
        nodes.append(
            ViewNode(
                node_id=f"entity:alternative:{alternative_id}",
                node_type="entity_reference",
                label=_required_display_text(
                    alternative.get("name_ja"), f"alternative {alternative_id} name_ja"
                ),
                label_en=_required_display_text(
                    alternative.get("name_en"), f"alternative {alternative_id} name_en"
                ),
                summary=str(alternative.get("why_before_generic_optimization") or ""),
                display_order=display_order,
                default_collapsed=False,
                emphasis="muted",
                parent_node_id="branch:alternative-first",
                related_entities=[
                    EntityReference(entity_type="alternative", entity_id=alternative_id)
                ],
                source_ids=_string_list(alternative["source_ids"]),
            )
        )

    for group in preset.filter_policy.groups:
        for question_order, question_id in enumerate(group.question_ids):
            question = question_by_id[question_id]
            question_node_id = f"question:{question_id}"
            allowed_answers = _string_list(question["allowed_answers"])
            feature_id = str(question["mapped_feature_id"])
            nodes.append(
                ViewNode(
                    node_id=question_node_id,
                    node_type="question",
                    label=_required_display_text(
                        question.get("question_ja"), f"question {question_id} question_ja"
                    ),
                    label_en=_required_display_text(
                        question.get("question_en"), f"question {question_id} question_en"
                    ),
                    summary=str(question.get("why_asked") or ""),
                    display_order=question_order,
                    default_collapsed=True,
                    emphasis="normal",
                    parent_node_id=f"branch:{group.group_id}",
                    question_id=question_id,
                    answer_type=_answer_type(question["answer_type"]),
                    allowed_answers=allowed_answers,
                    related_entities=[EntityReference(entity_type="feature", entity_id=feature_id)],
                    source_ids=_string_list(question["source_ids"]),
                )
            )
            for answer_order, answer_value in enumerate(allowed_answers):
                matching_rules = rules_by_answer.get((question_id, answer_value), [])
                answer_label, answer_label_en = _answer_labels(
                    feature_id, answer_value, feature_value_by_key
                )
                nodes.append(
                    ViewNode(
                        node_id=f"answer:{question_id}:{answer_value}",
                        node_type="answer",
                        label=answer_label,
                        label_en=answer_label_en,
                        summary=(
                            str(matching_rules[0].get("explanation") or "")
                            if matching_rules
                            else ""
                        ),
                        display_order=answer_order,
                        default_collapsed=False,
                        emphasis="normal",
                        parent_node_id=question_node_id,
                        answer_bindings=[
                            AnswerBinding(question_id=question_id, answer_value=answer_value)
                        ],
                        related_entities=_rule_references(matching_rules),
                        source_ids=_stable_union(
                            _string_list(question["source_ids"]),
                            *(_string_list(rule["source_ids"]) for rule in matching_rules),
                        ),
                    )
                )

    edges = [
        ViewEdge(
            edge_id=f"hierarchy:{node.parent_node_id}:{node.node_id}",
            source_node_id=node.parent_node_id,
            target_node_id=node.node_id,
            edge_type="hierarchy",
            explanation=_hierarchy_explanation(node),
        )
        for node in nodes
        if node.parent_node_id is not None
    ]

    entities = _build_entities(
        features=features,
        methods=methods,
        problems=problems,
        alternatives=alternatives,
        sources=sources,
    )

    return ViewSpec(
        version=VIEW_VERSION,
        view_id=preset.view_id,
        preset_id=preset.preset_id,
        title=preset.name_ja,
        description=preset.description_ja,
        limitations=preset.limitations_ja,
        axis=preset.axis,
        relation_types=preset.relation_types,
        max_depth=preset.max_depth,
        filter_policy=_view_filter_policy(preset),
        focus_fallback_entity_types=preset.focus_fallback_entity_types,
        dataset_version=dataset_version,
        generated_at=generated_at,
        root_node_ids=[f"branch:{group.group_id}" for group in preset.filter_policy.groups],
        nodes=nodes,
        edges=edges,
        entities=entities,
    )


def _build_entities(
    *,
    features: list[dict[str, Any]],
    methods: list[dict[str, Any]],
    problems: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> list[ViewEntity]:
    entities = [
        ViewEntity(
            entity_type="feature",
            entity_id=str(feature["feature_id"]),
            label=_required_display_text(
                feature.get("name_ja"), f"feature {feature['feature_id']} name_ja"
            ),
            label_en=_required_display_text(
                feature.get("name_en"), f"feature {feature['feature_id']} name_en"
            ),
            summary=str(feature.get("definition") or ""),
            url="",
            source_ids=_string_list(feature["source_ids"]),
        )
        for feature in features
    ]
    entities.extend(
        ViewEntity(
            entity_type="method",
            entity_id=str(method["method_id"]),
            label=_required_display_text(
                method.get("name_ja"), f"method {method['method_id']} name_ja"
            ),
            label_en=_required_display_text(
                method.get("name_en"), f"method {method['method_id']} name_en"
            ),
            summary=str(method.get("summary") or ""),
            url="",
            source_ids=_string_list(method["source_ids"]),
        )
        for method in methods
    )
    entities.extend(
        ViewEntity(
            entity_type="problem",
            entity_id=str(problem["problem_id"]),
            label=_required_display_text(
                problem.get("name_ja"), f"problem {problem['problem_id']} name_ja"
            ),
            label_en=_required_display_text(
                problem.get("name_en"), f"problem {problem['problem_id']} name_en"
            ),
            summary=str(problem.get("summary") or ""),
            url="",
            source_ids=_string_list(problem["source_ids"]),
        )
        for problem in problems
    )
    entities.extend(
        ViewEntity(
            entity_type="alternative",
            entity_id=str(alternative["alternative_id"]),
            label=_required_display_text(
                alternative.get("name_ja"),
                f"alternative {alternative['alternative_id']} name_ja",
            ),
            label_en=_required_display_text(
                alternative.get("name_en"),
                f"alternative {alternative['alternative_id']} name_en",
            ),
            summary=str(alternative.get("why_before_generic_optimization") or ""),
            url="",
            source_ids=_string_list(alternative["source_ids"]),
        )
        for alternative in alternatives
    )
    entities.extend(
        ViewEntity(
            entity_type="source",
            entity_id=str(source["source_id"]),
            label=_required_display_text(
                source.get("title"), f"source {source['source_id']} title"
            ),
            label_en=_required_display_text(
                source.get("title"), f"source {source['source_id']} title"
            ),
            summary=str(source.get("supported_claim") or ""),
            url=str(source.get("url") or ""),
            source_ids=[],
        )
        for source in sources
    )
    return entities


def _build_grouped_semantic_view(
    *,
    preset: ViewPresetSeed,
    dataset_version: str,
    generated_at: datetime,
    features: list[dict[str, Any]],
    methods: list[dict[str, Any]],
    problems: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> ViewSpec:
    records = {
        "feature": {str(row["feature_id"]): row for row in features},
        "method": {str(row["method_id"]): row for row in methods},
        "alternative": {str(row["alternative_id"]): row for row in alternatives},
    }
    presentation = {
        "feature": ("feature_id", "name_ja", "name_en", "definition"),
        "method": ("method_id", "name_ja", "name_en", "summary"),
        "alternative": (
            "alternative_id",
            "name_ja",
            "name_en",
            "why_before_generic_optimization",
        ),
    }
    nodes: list[ViewNode] = []
    for group_order, group in enumerate(preset.filter_policy.groups):
        branch_id = f"branch:{group.group_id}"
        nodes.append(
            ViewNode(
                node_id=branch_id,
                node_type="branch",
                label=group.label_ja,
                label_en=group.label_en,
                summary=preset.description_ja,
                display_order=group_order,
                default_collapsed=False,
                emphasis="primary",
                related_entities=[],
                source_ids=preset.source_ids,
            )
        )
        selectors = (
            ("feature", group.feature_ids),
            ("method", group.method_ids),
            ("alternative", group.alternative_ids),
        )
        child_order = 0
        for entity_type, entity_ids in selectors:
            id_key, label_key, label_en_key, summary_key = presentation[entity_type]
            for entity_id in entity_ids:
                try:
                    record = records[entity_type][entity_id]
                except KeyError as error:
                    raise ValueError(
                        f"view {preset.view_id} references missing {entity_type}: {entity_id}"
                    ) from error
                nodes.append(
                    ViewNode(
                        node_id=f"entity:{entity_type}:{entity_id}",
                        node_type="entity_reference",
                        label=_required_display_text(
                            record.get(label_key), f"{entity_type} {record[id_key]} {label_key}"
                        ),
                        label_en=_required_display_text(
                            record.get(label_en_key),
                            f"{entity_type} {record[id_key]} {label_en_key}",
                        ),
                        summary=str(record.get(summary_key) or ""),
                        display_order=child_order,
                        default_collapsed=False,
                        emphasis="normal",
                        parent_node_id=branch_id,
                        related_entities=[
                            EntityReference(entity_type=entity_type, entity_id=entity_id)
                        ],
                        source_ids=_string_list(record["source_ids"]),
                    )
                )
                child_order += 1

    edges = [
        ViewEdge(
            edge_id=f"hierarchy:{node.parent_node_id}:{node.node_id}",
            source_node_id=node.parent_node_id,
            target_node_id=node.node_id,
            edge_type="hierarchy",
            explanation=_hierarchy_explanation(node),
        )
        for node in nodes
        if node.parent_node_id is not None
    ]
    return ViewSpec(
        version=VIEW_VERSION,
        view_id=preset.view_id,
        preset_id=preset.preset_id,
        title=preset.name_ja,
        description=preset.description_ja,
        limitations=preset.limitations_ja,
        axis=preset.axis,
        relation_types=preset.relation_types,
        max_depth=preset.max_depth,
        filter_policy=_view_filter_policy(preset),
        focus_fallback_entity_types=preset.focus_fallback_entity_types,
        dataset_version=dataset_version,
        generated_at=generated_at,
        root_node_ids=[f"branch:{group.group_id}" for group in preset.filter_policy.groups],
        nodes=nodes,
        edges=edges,
        entities=_build_entities(
            features=features,
            methods=methods,
            problems=problems,
            alternatives=alternatives,
            sources=sources,
        ),
    )


def _view_filter_policy(preset: ViewPresetSeed) -> ViewFilterPolicy:
    return ViewFilterPolicy(
        mode=preset.filter_policy.mode,
        groups=[
            ViewFilterGroup(
                group_id=group.group_id,
                label=group.label_ja,
                label_en=group.label_en,
                question_ids=group.question_ids,
                feature_ids=group.feature_ids,
                method_ids=group.method_ids,
                alternative_ids=group.alternative_ids,
            )
            for group in preset.filter_policy.groups
        ],
    )


def _target_ids_by_type(
    rules: list[dict[str, Any]],
) -> dict[str, set[str]]:
    target_ids: dict[str, set[str]] = {entity_type: set() for entity_type in RELATED_ENTITY_TYPES}
    for rule in rules:
        entity_type = str(rule["action_target_type"])
        if entity_type not in RELATED_ENTITY_TYPES:
            if entity_type == "none":
                continue
            raise ValueError(f"unsupported atlas rule target type: {entity_type}")
        target_ids[entity_type].update(_string_list(rule["action_target_ids"]))
    return target_ids


def _rule_references(rules: list[dict[str, Any]]) -> list[EntityReference]:
    references: list[EntityReference] = []
    seen: set[tuple[str, str]] = set()
    for rule in rules:
        entity_type = str(rule["action_target_type"])
        if entity_type not in RELATED_ENTITY_TYPES:
            continue
        for entity_id in _string_list(rule["action_target_ids"]):
            key = (entity_type, entity_id)
            if key in seen:
                continue
            seen.add(key)
            references.append(EntityReference(entity_type=entity_type, entity_id=entity_id))
    return references


def _answer_labels(
    feature_id: str,
    answer_value: str,
    feature_value_by_key: dict[tuple[str, str], dict[str, Any]],
) -> tuple[str, str]:
    feature_value = feature_value_by_key.get((feature_id, answer_value))
    if feature_value is not None:
        return (
            _required_display_text(
                feature_value.get("label_ja"),
                f"feature value {feature_id}/{answer_value} label_ja",
            ),
            _required_display_text(
                feature_value.get("label_en"),
                f"feature value {feature_id}/{answer_value} label_en",
            ),
        )
    try:
        label_ja = ANSWER_LABELS_JA[answer_value]
    except KeyError as error:
        raise ValueError(f"missing explicit answer label: {answer_value}") from error
    if "（" in label_ja and label_ja.endswith("）"):
        return label_ja, label_ja.rsplit("（", maxsplit=1)[1][:-1]
    return label_ja, ANSWER_LABELS_EN_WITHOUT_PARENTHETICAL[answer_value]


def _hierarchy_explanation(node: ViewNode) -> str:
    if node.node_type == "question":
        return "この分岐で確認する診断質問。"
    if node.node_type == "answer":
        return "診断質問に対する選択肢。"
    if node.node_type == "entity_reference":
        return "汎用最適化の前に確認する代替解法。"
    return "親分岐から展開する項目。"


def _require_all_ids(
    rows: list[dict[str, Any]],
    id_column: str,
    expected_ids: list[str],
    entity_type: str,
) -> None:
    actual_ids = {str(row[id_column]) for row in rows}
    missing = sorted(set(expected_ids) - actual_ids)
    if missing:
        raise ValueError(f"atlas export references missing {entity_type} IDs: {', '.join(missing)}")


def _stable_union(*values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for value in values for item in value))


def _write_json(path: Path, model: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = model if isinstance(model, dict) else model.model_dump(mode="json")
    if compact:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    else:
        payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8", newline="\n")


def _write_content_index(path: Path, dataset_version: str) -> None:
    pages = [page for page in load_content(CONTENT_DIRECTORY) if page.status == "published"]
    _write_json(
        path,
        {
            "contract_version": "2.0.0",
            "dataset_version": dataset_version,
            "pages": [_content_payload(page) for page in pages],
        },
    )


def _content_payload(page: ContentPage) -> dict[str, Any]:
    return {
        "content_id": page.content_id,
        "kind": page.kind,
        "canonical_entity_type": page.canonical_entity_type,
        "canonical_entity_id": page.canonical_entity_id,
        "title_ja": page.title_ja,
        "title_en": page.title_en,
        "summary": page.summary,
        "html": page.html,
        "toc": [
            {"heading_id": heading.heading_id, "label": heading.label, "level": heading.level}
            for heading in page.toc
        ],
        "prerequisites": list(page.prerequisites),
        "related_ids": list(page.related_ids),
        "visualization_ids": list(page.visualization_ids),
        "comparison_ids": list(page.comparison_ids),
        "source_ids": list(page.source_ids),
        "status": page.status,
        "last_reviewed": page.last_reviewed,
        "seo_title": page.title_ja,
        "seo_description": page.summary,
    }


def _write_seeded_index(
    path: Path,
    source: Path,
    *,
    collection_field: str,
    contract_version: str,
    dataset_version: str,
) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if set(payload) != {collection_field} or not isinstance(payload[collection_field], list):
        raise ValueError(f"invalid seeded site index: {source}")
    _write_json(
        path,
        {
            "contract_version": contract_version,
            "dataset_version": dataset_version,
            collection_field: payload[collection_field],
        },
    )


def _required_display_text(value: object, context: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"atlas export requires non-empty display metadata: {context}")
    return str(value)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise TypeError("repository export lists must be normalized before serialization")
    return [str(item) for item in value]


def _answer_type(value: object) -> Literal["single_choice", "multi_choice"]:
    if value == "single_choice" or value == "multi_choice":
        return value
    raise ValueError(f"unsupported question answer_type: {value}")
