from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.trace_models import AlgorithmTrace, TraceFrame, TraceMetric

SEARCH_TREE_CONTRACT_VERSION: Literal["1.0.0"] = "1.0.0"
SEARCH_TREE_GENERATOR_ID = "educational.branch_bound.knapsack.v1"
SEARCH_TREE_GENERATOR_VERSION = "1.1.0"
SEARCH_TREE_EVALUATION_BUDGET = 9

NonBlank = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
NodeState = Literal[
    "open",
    "active",
    "branched",
    "feasible",
    "infeasible_pruned",
    "bound_pruned",
    "optimal",
]
Feasibility = Literal["undetermined", "feasible", "infeasible"]
PruneReason = Literal["capacity_exceeded", "bound_not_better"]
TerminalState = Literal["ongoing", "optimality_proven", "budget_exhausted"]


class SearchTreeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class SearchTreeNode(SearchTreeModel):
    node_id: NonBlank
    parent_id: NonBlank | None
    depth: int = Field(ge=0)
    branch_label_ja: NonBlank
    branch_label_en: NonBlank
    partial_assignment: dict[str, Literal[0, 1]]
    weight: int = Field(ge=0)
    objective_value: int = Field(ge=0)
    bound: float | None
    feasibility: Feasibility
    state: NodeState
    prune_reason: PruneReason | None
    prune_explanation_ja: str | None
    prune_explanation_en: str | None

    @model_validator(mode="after")
    def validate_prune_explanation(self) -> Self:
        pruned = self.state in {"infeasible_pruned", "bound_pruned"}
        fields_present = (
            self.prune_reason is not None
            and bool(self.prune_explanation_ja and self.prune_explanation_ja.strip())
            and bool(self.prune_explanation_en and self.prune_explanation_en.strip())
        )
        if pruned != fields_present:
            raise ValueError("pruned nodes require a reason and bilingual explanation")
        return self


class SearchTreeIncumbent(SearchTreeModel):
    node_id: str | None
    source: Literal["heuristic", "tree"]
    assignment: dict[str, Literal[0, 1]]
    value: int = Field(ge=0)
    weight: int = Field(ge=0)


class SearchTreeProgress(SearchTreeModel):
    explored_nodes: int = Field(ge=0)
    open_nodes: int = Field(ge=0)
    node_budget: int = Field(gt=0)


class SearchTreeFramePayload(SearchTreeModel):
    contract_version: Literal["1.0.0"] = SEARCH_TREE_CONTRACT_VERSION
    renderer_family: Literal["search_tree"] = "search_tree"
    renderer_contract_version: Literal["1.0.0"] = SEARCH_TREE_CONTRACT_VERSION
    nodes: list[SearchTreeNode] = Field(min_length=1)
    active_node_id: str | None
    incumbent: SearchTreeIncumbent | None
    best_feasible_value: int | None
    global_bound: float
    absolute_gap: float | None
    relative_gap: float | None
    progress: SearchTreeProgress
    decision_explanation_ja: NonBlank
    decision_explanation_en: NonBlank
    terminal_state: TerminalState

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("search-tree node IDs must be unique")
        node_id_set = set(node_ids)
        for node in self.nodes:
            if node.parent_id is not None and node.parent_id not in node_id_set:
                raise ValueError(f"search-tree node parent is missing: {node.node_id}")
        if self.active_node_id is not None and self.active_node_id not in node_id_set:
            raise ValueError("active search-tree node is missing")
        if (self.incumbent is None) != (self.best_feasible_value is None):
            raise ValueError("incumbent and best_feasible_value must appear together")
        if self.incumbent is not None and self.best_feasible_value != self.incumbent.value:
            raise ValueError("best_feasible_value must equal the incumbent value")
        if self.incumbent is None:
            if self.absolute_gap is not None or self.relative_gap is not None:
                raise ValueError("gap is unavailable before a feasible solution exists")
        else:
            expected_gap = max(0.0, self.global_bound - self.incumbent.value)
            if self.absolute_gap != expected_gap:
                raise ValueError("absolute_gap is inconsistent with bound and incumbent")
            expected_relative = expected_gap / max(1.0, abs(float(self.incumbent.value)))
            if self.relative_gap != expected_relative:
                raise ValueError("relative_gap is inconsistent with absolute_gap")
        if self.terminal_state == "optimality_proven" and self.absolute_gap != 0.0:
            raise ValueError("optimality_proven requires a zero gap")
        return self


class StaticFallback(SearchTreeModel):
    path: NonBlank
    media_type: Literal["image/svg+xml"]
    alt_ja: NonBlank
    alt_en: NonBlank


class SearchTreeArtifact(SearchTreeModel):
    contract_version: Literal["1.0.0"] = SEARCH_TREE_CONTRACT_VERSION
    dataset_version: NonBlank
    artifact_id: NonBlank
    artifact_kind: Literal["executable_trace"] = "executable_trace"
    renderer_family: Literal["search_tree"] = "search_tree"
    renderer_contract_version: Literal["1.0.0"] = SEARCH_TREE_CONTRACT_VERSION
    scenario_id: NonBlank
    trace: AlgorithmTrace
    static_fallback: StaticFallback

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.trace.dataset_version != self.dataset_version:
            raise ValueError("search-tree artifact and trace dataset versions differ")
        if self.trace.scenario_id != self.scenario_id:
            raise ValueError("search-tree artifact and trace scenario IDs differ")
        for frame in self.trace.frames:
            SearchTreeFramePayload.model_validate(frame.payload)
        expected_terminal = {
            "completed": "optimality_proven",
            "budget_exhausted": "budget_exhausted",
        }.get(self.trace.terminal_status)
        final_payload = SearchTreeFramePayload.model_validate(self.trace.frames[-1].payload)
        if expected_terminal is None or final_payload.terminal_state != expected_terminal:
            raise ValueError("trace and search-tree terminal states differ")
        return self


class SearchTreeIndexEntry(SearchTreeModel):
    artifact_id: NonBlank
    path: NonBlank
    trace_id: NonBlank
    scenario_id: NonBlank
    artifact_kind: Literal["executable_trace"]
    renderer_family: Literal["search_tree"]
    renderer_contract_version: Literal["1.0.0"]
    static_fallback_path: NonBlank


class SearchTreeIndex(SearchTreeModel):
    contract_version: Literal["1.0.0"] = SEARCH_TREE_CONTRACT_VERSION
    dataset_version: NonBlank
    artifacts: list[SearchTreeIndexEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ids(self) -> Self:
        ids = [entry.artifact_id for entry in self.artifacts]
        if len(ids) != len(set(ids)):
            raise ValueError("search-tree artifact IDs must be unique")
        return self


@dataclass(frozen=True)
class _Item:
    item_id: str
    weight: int
    value: int


@dataclass
class _Node:
    node_id: str
    parent_id: str | None
    depth: int
    branch_label_ja: str
    branch_label_en: str
    assignment: dict[str, Literal[0, 1]]
    weight: int
    value: int
    bound: float | None = None
    feasibility: Feasibility = "undetermined"
    state: NodeState = "open"
    prune_reason: PruneReason | None = None
    prune_explanation_ja: str | None = None
    prune_explanation_en: str | None = None


_PROBLEM = get_runtime_problem("INSTANCE_BINARY_KNAPSACK_4")
_RAW_ITEMS = _PROBLEM.instance.parameters["items"]
if not isinstance(_RAW_ITEMS, list):
    raise ValueError("knapsack registry items must be a list")


def _metadata_int(value: object) -> int:
    if not isinstance(value, int):
        raise ValueError("knapsack registry integer metadata is invalid")
    return value


_ITEMS = tuple(
    _Item(str(item["item_id"]), _metadata_int(item["weight"]), _metadata_int(item["value"]))
    for item in _RAW_ITEMS
    if isinstance(item, dict)
)
_CAPACITY = _metadata_int(_PROBLEM.instance.parameters["capacity"])
_SOURCE_IDS = list(_PROBLEM.instance.source_ids)


def generate_search_tree_artifact(
    *,
    dataset_version: str,
    evaluation_budget: int = SEARCH_TREE_EVALUATION_BUDGET,
    node_stop_limit: int = SEARCH_TREE_EVALUATION_BUDGET,
) -> SearchTreeArtifact:
    if evaluation_budget < 1:
        raise ValueError("search-tree evaluation budget must be positive")
    if node_stop_limit < 1 or node_stop_limit > evaluation_budget:
        raise ValueError("search-tree node stop limit must be within the evaluation budget")
    nodes: dict[str, _Node] = {"root": _Node("root", None, 0, "根", "Root", {}, 0, 0)}
    nodes["root"].bound = _fractional_bound(nodes["root"])
    stack = ["root"]
    frames: list[TraceFrame] = []
    incumbent: SearchTreeIncumbent | None = None
    explored = 0

    def append(
        event_type: str,
        label_ja: str,
        label_en: str,
        explanation_ja: str,
        explanation_en: str,
        *,
        active_node_id: str | None,
        terminal_state: TerminalState = "ongoing",
        decision: Literal["accepted", "rejected", "not_applicable"] = "not_applicable",
    ) -> None:
        open_bounds = [
            node.bound
            for node in nodes.values()
            if node.state in {"open", "active"} and node.bound is not None
        ]
        incumbent_value = incumbent.value if incumbent else None
        global_bound = max(
            [float(value) for value in open_bounds]
            + ([float(incumbent_value)] if incumbent_value is not None else [0.0])
        )
        absolute_gap = None if incumbent_value is None else max(0.0, global_bound - incumbent_value)
        relative_gap = (
            None
            if incumbent_value is None or absolute_gap is None
            else absolute_gap / max(1.0, abs(float(incumbent_value)))
        )
        payload = SearchTreeFramePayload(
            nodes=[_public_node(node) for node in nodes.values()],
            active_node_id=active_node_id,
            incumbent=incumbent,
            best_feasible_value=incumbent_value,
            global_bound=global_bound,
            absolute_gap=absolute_gap,
            relative_gap=relative_gap,
            progress=SearchTreeProgress(
                explored_nodes=explored,
                open_nodes=sum(node.state == "open" for node in nodes.values()),
                node_budget=node_stop_limit,
            ),
            decision_explanation_ja=explanation_ja,
            decision_explanation_en=explanation_en,
            terminal_state=terminal_state,
        )
        metrics = [
            TraceMetric(
                metric_id="global-bound",
                label_ja="大域上界",
                label_en="Global upper bound",
                value=global_bound,
                unit=None,
            )
        ]
        if incumbent_value is not None:
            metrics.extend(
                [
                    TraceMetric(
                        metric_id="best-feasible",
                        label_ja="best feasible value",
                        label_en="Best feasible value",
                        value=float(incumbent_value),
                        unit=None,
                    ),
                    TraceMetric(
                        metric_id="absolute-gap",
                        label_ja="最適性gap",
                        label_en="Optimality gap",
                        value=float(absolute_gap or 0.0),
                        unit=None,
                    ),
                ]
            )
        frame_index = len(frames)
        frames.append(
            TraceFrame(
                frame_index=frame_index,
                iteration=explored,
                oracle_evaluations=explored,
                elapsed_steps=frame_index,
                elapsed_time_ms=float(frame_index * 25),
                event_type=event_type,
                decision=decision,
                explanation_key=f"search-tree.{event_type}",
                event_label_ja=label_ja,
                event_label_en=label_en,
                keyframe=True,
                points=[],
                vectors=[],
                metrics=metrics,
                payload=payload.model_dump(mode="json"),
            )
        )

    append(
        "initialize",
        "探索木を初期化",
        "Initialize search tree",
        "根nodeを作り、0-1 knapsackの緩和上界を準備します。",
        "Create the root node and prepare the relaxed upper bound.",
        active_node_id="root",
    )
    incumbent = SearchTreeIncumbent(
        node_id=None,
        source="heuristic",
        assignment={"A": 1, "B": 0, "D": 1, "C": 0},
        value=13,
        weight=6,
    )
    append(
        "incumbent_update",
        "初期の実行可能解を登録",
        "Register initial feasible solution",
        "簡単なheuristicで得た値13をincumbentとして登録します。これは最適性の証明ではありません。",
        "Register value 13 from a simple heuristic as the incumbent; this is not a proof.",
        active_node_id="root",
        decision="accepted",
    )

    while stack and explored < node_stop_limit:
        node_id = stack.pop()
        node = nodes[node_id]
        node.state = "active"
        explored += 1
        append(
            "propagate",
            "部分割当を反映",
            "Propagate partial assignment",
            f"{node.branch_label_ja}の部分割当から使用重量と残り容量を確定します。",
            "Propagate the partial assignment to determine used and remaining capacity.",
            active_node_id=node_id,
        )
        if node.weight > _CAPACITY:
            node.feasibility = "infeasible"
            node.state = "infeasible_pruned"
            node.prune_reason = "capacity_exceeded"
            node.prune_explanation_ja = (
                f"重量{node.weight}が容量{_CAPACITY}を超えるため、このnode以下は探索しません。"
            )
            node.prune_explanation_en = (
                f"Weight {node.weight} exceeds capacity {_CAPACITY}, so this subtree is skipped."
            )
            append(
                "infeasible_prune",
                "実行不可能で枝刈り",
                "Prune infeasible node",
                node.prune_explanation_ja,
                node.prune_explanation_en,
                active_node_id=node_id,
                decision="rejected",
            )
            continue

        node.feasibility = "feasible"
        node.bound = _fractional_bound(node)
        append(
            "relax",
            "緩和上界を計算",
            "Compute relaxation bound",
            f"未割当を分数選択できる緩和で、このnodeの上界を{node.bound:.2f}と見積もります。",
            f"Use a fractional relaxation to estimate this node's upper bound as {node.bound:.2f}.",
            active_node_id=node_id,
        )
        if node_id == "root":
            append(
                "bound_update",
                "大域上界を更新",
                "Update global bound",
                "open nodeの上界の最大値を、未探索部分が到達しうる大域上界として更新します。",
                "Update the global upper bound from the best bound among open nodes.",
                active_node_id=node_id,
            )
        if incumbent is not None and node.bound <= incumbent.value:
            node.state = "bound_pruned"
            node.prune_reason = "bound_not_better"
            node.prune_explanation_ja = (
                f"上界{node.bound:.2f}がincumbent {incumbent.value}を超えないため、"
                "改善できず探索しません。"
            )
            node.prune_explanation_en = (
                f"The bound {node.bound:.2f} cannot beat incumbent {incumbent.value}, "
                "so the subtree is skipped."
            )
            append(
                "bound_prune",
                "boundで枝刈り",
                "Prune by bound",
                node.prune_explanation_ja,
                node.prune_explanation_en,
                active_node_id=node_id,
                decision="rejected",
            )
            continue
        if node.depth == len(_ITEMS):
            node.state = "feasible"
            if incumbent is None or node.value > incumbent.value:
                incumbent = SearchTreeIncumbent(
                    node_id=node.node_id,
                    source="tree",
                    assignment=node.assignment,
                    value=node.value,
                    weight=node.weight,
                )
                append(
                    "incumbent_update",
                    "incumbentを更新",
                    "Update incumbent",
                    f"実行可能な完全割当で値{node.value}を得たため、best feasibleを更新します。",
                    f"A complete feasible assignment reaches {node.value}, updating best feasible.",
                    active_node_id=node_id,
                    decision="accepted",
                )
            continue

        item = _ITEMS[node.depth]
        node.state = "branched"
        exclude_id = f"{node.node_id}-0"
        include_id = f"{node.node_id}-1"
        exclude_assignment = {**node.assignment, item.item_id: 0}
        include_assignment = {**node.assignment, item.item_id: 1}
        exclude = _Node(
            exclude_id,
            node.node_id,
            node.depth + 1,
            f"{item.item_id}=0",
            f"{item.item_id}=0",
            exclude_assignment,
            node.weight,
            node.value,
        )
        include = _Node(
            include_id,
            node.node_id,
            node.depth + 1,
            f"{item.item_id}=1",
            f"{item.item_id}=1",
            include_assignment,
            node.weight + item.weight,
            node.value + item.value,
        )
        exclude.bound = _fractional_bound(exclude)
        include.bound = _fractional_bound(include) if include.weight <= _CAPACITY else None
        nodes[exclude_id] = exclude
        nodes[include_id] = include
        stack.extend([exclude_id, include_id])
        append(
            "branch",
            f"{item.item_id}で枝分かれ",
            f"Branch on {item.item_id}",
            f"未決定の{item.item_id}を0と1に固定した2つの子nodeを作ります。",
            f"Create two child nodes by fixing undecided item {item.item_id} to 0 and 1.",
            active_node_id=node_id,
        )

    if stack:
        append(
            "budget_exhausted",
            "node予算に到達",
            "Node budget exhausted",
            "node予算に達したため停止します。incumbentは候補解ですが、残るgapのため最適性は未証明です。",
            "Stop at the node budget. The incumbent is a candidate, but the remaining "
            "gap means optimality is unproven.",
            active_node_id=None,
            terminal_state="budget_exhausted",
        )
        terminal_status: Literal["completed", "budget_exhausted"] = "budget_exhausted"
        terminal_ja = "実行可能な候補解を保持したままnode予算で停止し、最適性は未証明です。"
        terminal_en = (
            "Stopped at the node budget with a feasible candidate and no optimality proof."
        )
    else:
        if incumbent is None:
            raise RuntimeError("deterministic search completed without a feasible solution")
        if incumbent.node_id and incumbent.node_id in nodes:
            nodes[incumbent.node_id].state = "optimal"
        append(
            "optimality_proven",
            "最適性を証明",
            "Optimality proven",
            "open nodeがなくなり大域上界とbest feasibleが一致したため、"
            "値15の最適性が証明されました。",
            "No open nodes remain and the global bound equals best feasible, "
            "proving value 15 optimal.",
            active_node_id=incumbent.node_id,
            terminal_state="optimality_proven",
            decision="accepted",
        )
        terminal_status = "completed"
        terminal_ja = "best feasible value 15と大域上界15が一致し、最適性を証明しました。"
        terminal_en = "Best feasible value 15 matches the global bound 15, proving optimality."

    suffix = "complete" if terminal_status == "completed" else "budget"
    scenario_id = f"SCENARIO_BINARY_KNAPSACK_BNB_{suffix.upper()}"
    trace = AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=f"binary-knapsack-bnb-{suffix}",
        method_id="M_BRANCH_BOUND",
        profile_id="PROFILE_SEARCH_TREE_01",
        objective_id="INSTANCE_BINARY_KNAPSACK_4",
        scenario_id=scenario_id,
        generator_id=SEARCH_TREE_GENERATOR_ID,
        generator_version=SEARCH_TREE_GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=_PROBLEM.trace_objective(),
        preset={
            "preset_id": "BNB_DEPTH_FIRST_INCLUDE_FIRST",
            "strategy": "depth_first_include_first",
            "renderer_family": "search_tree",
            "renderer_contract_version": "1.0.0",
        },
        parameters={
            "capacity": _CAPACITY,
            "items": [
                {"item_id": item.item_id, "weight": item.weight, "value": item.value}
                for item in _ITEMS
            ],
        },
        initial_state={"assignment": {}, "heuristic_incumbent": 13},
        seed={"status": "fixed", "value": 0},
        evaluation_budget=evaluation_budget,
        stopping={"max_nodes": node_stop_limit},
        environment={
            "runtime": "deterministic_educational_generator",
            "version": SEARCH_TREE_GENERATOR_VERSION,
        },
        fairness_statement=(
            "同じproblem instance・seed・depth-first include-first strategyで再生成する。"
            "naive enumerationやsolver間の速度比較には用いない。"
        ),
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja=terminal_ja,
        terminal_summary_en=terminal_en,
        source_ids=_SOURCE_IDS,
    )
    artifact_id = trace.trace_id
    return SearchTreeArtifact(
        dataset_version=dataset_version,
        artifact_id=artifact_id,
        scenario_id=scenario_id,
        trace=trace,
        static_fallback=StaticFallback(
            path=f"search-trees/{artifact_id}.svg",
            media_type="image/svg+xml",
            alt_ja="0-1 knapsackの探索木、incumbent、上界、枝刈り状態の静止画",
            alt_en="Static search tree with incumbent, bound, and pruning states",
        ),
    )


def render_search_tree_svg(artifact: SearchTreeArtifact) -> str:
    payload = SearchTreeFramePayload.model_validate(artifact.trace.frames[-1].payload)
    width = 960
    height = 120 + max(node.depth for node in payload.nodes) * 120
    positions: dict[str, tuple[float, float]] = {}
    by_depth: dict[int, list[SearchTreeNode]] = {}
    for node in payload.nodes:
        by_depth.setdefault(node.depth, []).append(node)
    for depth, level in by_depth.items():
        ordered = sorted(level, key=lambda node: node.node_id)
        for index, node in enumerate(ordered):
            positions[node.node_id] = (
                width * (index + 1) / (len(ordered) + 1),
                70.0 + depth * 115.0,
            )
    lines = []
    for node in payload.nodes:
        if node.parent_id is None:
            continue
        x1, y1 = positions[node.parent_id]
        x2, y2 = positions[node.node_id]
        lines.append(f'<line x1="{x1:.1f}" y1="{y1 + 24:.1f}" x2="{x2:.1f}" y2="{y2 - 24:.1f}" />')
    cards = []
    for node in payload.nodes:
        x, y = positions[node.node_id]
        state_class = escape(node.state)
        bound = "—" if node.bound is None else f"{node.bound:.2f}"
        cards.append(
            f'<g class="node {state_class}" transform="translate({x - 62:.1f} {y - 25:.1f})">'
            '<rect width="124" height="50" rx="8" />'
            f'<text x="62" y="19">{escape(node.branch_label_ja)}</text>'
            f'<text x="62" y="38">value {node.objective_value} · bound {bound}</text>'
            "</g>"
        )
    status = "最適性証明" if payload.terminal_state == "optimality_proven" else "node予算で停止"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        f'<title id="title">0-1 knapsack探索木: {escape(status)}</title>'
        '<desc id="desc">探索木の静止画fallback。緑は実行可能、赤は実行不可能、'
        "灰色はbound枝刈り。</desc>"
        "<style>svg{background:#f7f5ef;font-family:system-ui,sans-serif}"
        "line{stroke:#8b877d;stroke-width:2}"
        ".node rect{fill:#fff;stroke:#49463f;stroke-width:2}"
        ".node text{text-anchor:middle;font-size:11px;fill:#25231f}"
        ".infeasible_pruned rect{fill:#f9dddd;stroke:#a53d3d}"
        ".bound_pruned rect{fill:#e6e3dc;stroke:#746f65}"
        ".optimal rect{fill:#d9f2df;stroke:#2d7a46}"
        "text.heading{font-size:15px;font-weight:700;text-anchor:start}</style>"
        f'<text class="heading" x="20" y="24">{escape(status)} · '
        f"best {payload.best_feasible_value} · "
        f"bound {payload.global_bound:.2f} · gap {payload.absolute_gap}</text>"
        + "".join(lines)
        + "".join(cards)
        + "</svg>\n"
    )


def _fractional_bound(node: _Node) -> float:
    if node.weight > _CAPACITY:
        return float(node.value)
    capacity_left = _CAPACITY - node.weight
    bound = float(node.value)
    for item in _ITEMS[node.depth :]:
        if item.weight <= capacity_left:
            capacity_left -= item.weight
            bound += item.value
        else:
            bound += item.value * capacity_left / item.weight
            break
    return bound


def _public_node(node: _Node) -> SearchTreeNode:
    return SearchTreeNode(
        node_id=node.node_id,
        parent_id=node.parent_id,
        depth=node.depth,
        branch_label_ja=node.branch_label_ja,
        branch_label_en=node.branch_label_en,
        partial_assignment=node.assignment,
        weight=node.weight,
        objective_value=node.value,
        bound=node.bound,
        feasibility=node.feasibility,
        state=node.state,
        prune_reason=node.prune_reason,
        prune_explanation_ja=node.prune_explanation_ja,
        prune_explanation_en=node.prune_explanation_en,
    )
