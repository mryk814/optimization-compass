from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, date, datetime, time
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from optimization_compass.db import KnowledgeRepository
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
from optimization_compass.view_spec import (
    AnswerBinding,
    EntityReference,
    ManifestAsset,
    ManifestTraceAsset,
    ManifestView,
    SiteManifest,
    ViewEdge,
    ViewEntity,
    ViewNode,
    ViewSpec,
)

VIEW_VERSION: Literal["1.0.0"] = "1.0.0"
VIEW_ID = "problem-structure"
VIEW_PATH = "views/problem-structure.json"
VIEW_TITLE = "最適化問題の構造マップ"
VIEW_DESCRIPTION = "問題の特徴から、関連する問題型・手法・代替解法・根拠をたどるためのビュー。"

BRANCHES: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "alternative-first",
        "代替解法を先に確認",
        "Check alternatives first",
        "汎用最適化を選ぶ前に、専用解法や問題の置き換えを確認する。",
        (),
    ),
    (
        "variable-domain",
        "変数と計算資源",
        "Variables and compute",
        "変数型・規模・反復実行条件から、実行可能な手法の範囲を整理する。",
        ("Q01", "Q08", "Q12"),
    ),
    (
        "objective-information",
        "目的関数と評価情報",
        "Objective and evaluation information",
        "目的の表現・微分・評価費・信頼性から、使える情報と探索方法を整理する。",
        ("Q02", "Q03", "Q05", "Q06", "Q07"),
    ),
    (
        "constraint-structure",
        "制約と特殊構造",
        "Constraints and special structure",
        "制約の種類と利用できる特殊構造から、専用手法の候補を整理する。",
        ("Q04", "Q11"),
    ),
    (
        "required-outcome-guarantee",
        "求める解と保証",
        "Required outcome and guarantee",
        "局所解・大域探索・証明の必要性から、求める結果の水準を整理する。",
        ("Q09", "Q10"),
    ),
)

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


def export_site_data(output_dir: Path, repository: KnowledgeRepository) -> SiteManifest:
    release = repository.latest_release()
    generated_at = datetime.combine(
        date.fromisoformat(release["release_date"]), time.min, tzinfo=UTC
    )
    questions = repository.atlas_questions()
    rules = repository.atlas_rules()
    alternatives = repository.atlas_alternatives()

    question_feature_ids = {str(question["mapped_feature_id"]) for question in questions}
    target_ids = _target_ids_by_type(rules)
    feature_ids = sorted(question_feature_ids | target_ids["feature"])
    features = repository.atlas_features(feature_ids)
    feature_values = repository.atlas_feature_values(feature_ids)
    methods = repository.atlas_methods(sorted(target_ids["method"]))
    problems = repository.atlas_problems(sorted(target_ids["problem"]))

    _require_all_ids(features, "feature_id", feature_ids, "feature")
    _require_all_ids(methods, "method_id", sorted(target_ids["method"]), "method")
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
    )
    sources = repository.atlas_sources(source_ids)
    _require_all_ids(sources, "source_id", source_ids, "source")

    view = _build_problem_structure(
        dataset_version=release["version"],
        generated_at=generated_at,
        questions=questions,
        rules=rules,
        feature_values=feature_values,
        features=features,
        methods=methods,
        problems=problems,
        alternatives=alternatives,
        sources=sources,
    )
    from optimization_compass.site_recommendation import build_site_data

    recommendation_data = build_site_data(repository)
    _write_json(output_dir / VIEW_PATH, view)
    _write_json(output_dir / "recommendation/site-data.json", recommendation_data)
    trace_asset = _write_dummy_trace(output_dir, dataset_version=release["version"])
    manifest = SiteManifest(
        version=VIEW_VERSION,
        dataset_version=release["version"],
        generated_at=generated_at,
        views=[ManifestView(view_id=VIEW_ID, version=VIEW_VERSION, path=VIEW_PATH)],
        recommendation=ManifestAsset(version="1.0.0", path="recommendation/site-data.json"),
        traces=trace_asset,
    )

    _write_json(output_dir / "manifest.json", manifest)
    return manifest


def _write_dummy_trace(output_dir: Path, *, dataset_version: str) -> ManifestTraceAsset:
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
        objective={
            "family": "quadratic",
            "dimensions": 2,
            "generator_id": "objective.quadratic.v1",
            "domain": {"x": [-4.0, 4.0], "y": [-4.0, 4.0]},
            "display_range": {"x": [-4.0, 4.0], "y": [-4.0, 4.0], "z": [0.0, 40.0]},
            "display_expression": "f(x, y) = (x - 1)^2 + 2(y + 1)^2",
            "optimum": {"point": [1.0, -1.0], "value": 0.0},
        },
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
        source_ids=["S001", "S002"],
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
    _write_json(index_path, index)
    index_bytes = index_path.read_bytes()
    return ManifestTraceAsset(
        contract_version="1.0.0",
        index_version="1.0.0",
        path="traces/index.json",
        bytes=len(index_bytes),
        sha256=sha256(index_bytes).hexdigest(),
    )


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
    expected_question_ids = {question_id for _, _, _, _, ids in BRANCHES for question_id in ids}
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

    nodes = [
        ViewNode(
            node_id=f"branch:{branch_id}",
            node_type="branch",
            label=label,
            label_en=label_en,
            summary=summary,
            display_order=display_order,
            default_collapsed=True,
            emphasis="primary",
            related_entities=[],
        )
        for display_order, (branch_id, label, label_en, summary, _) in enumerate(BRANCHES)
    ]

    alternative_group_id = "feature:alternative-first"
    nodes.append(
        ViewNode(
            node_id=alternative_group_id,
            node_type="feature",
            label="汎用最適化の前に確認する選択肢",
            label_en="Alternatives to generic optimization",
            summary="問題構造を活かす専用解法や別の定式化を先に確認する。",
            display_order=0,
            default_collapsed=True,
            emphasis="normal",
            parent_node_id="branch:alternative-first",
            related_entities=[],
        )
    )
    for display_order, alternative in enumerate(alternatives):
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
                parent_node_id=alternative_group_id,
                related_entities=[
                    EntityReference(entity_type="alternative", entity_id=alternative_id)
                ],
                source_ids=_string_list(alternative["source_ids"]),
            )
        )

    for branch_id, _, _, _, question_ids in BRANCHES:
        for question_order, question_id in enumerate(question_ids):
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
                    parent_node_id=f"branch:{branch_id}",
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
        view_id=VIEW_ID,
        title=VIEW_TITLE,
        description=VIEW_DESCRIPTION,
        dataset_version=dataset_version,
        generated_at=generated_at,
        root_node_ids=[f"branch:{branch_id}" for branch_id, _, _, _, _ in BRANCHES],
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


def _write_json(path: Path, model: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        model.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True
    )
    path.write_text(payload + "\n", encoding="utf-8", newline="\n")


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
