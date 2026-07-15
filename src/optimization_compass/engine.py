from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from optimization_compass.db import KnowledgeRepository, split_ids
from optimization_compass.models import (
    EntityRecommendation,
    Followup,
    ImplementationSummary,
    RecommendationRequest,
    RecommendationResponse,
    RuleTrace,
)


@dataclass
class Candidate:
    entity_id: str
    high: int = 0
    medium: int = 0
    candidate: int = 0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)

    @property
    def support_count(self) -> int:
        return self.high + self.medium + self.candidate

    @property
    def ordering_key(self) -> tuple[int, int, int, str]:
        return (-self.high, -self.medium, -self.support_count, self.entity_id)

    def add_rule(
        self, priority: str, explanation: str, warnings: str, source_ids: list[str]
    ) -> None:
        if priority == "high":
            self.high += 1
        elif priority == "medium":
            self.medium += 1
        elif priority == "candidate":
            self.candidate += 1
        if explanation and explanation not in self.reasons:
            self.reasons.append(explanation)
        if warnings and warnings not in self.warnings:
            self.warnings.append(warnings)
        for source_id in source_ids:
            if source_id not in self.source_ids:
                self.source_ids.append(source_id)

    def absorb(self, other: Candidate) -> None:
        self.high += other.high
        self.medium += other.medium
        self.candidate += other.candidate
        for reason in other.reasons:
            if reason not in self.reasons:
                self.reasons.append(reason)
        for warning in other.warnings:
            if warning not in self.warnings:
                self.warnings.append(warning)
        for source_id in other.source_ids:
            if source_id not in self.source_ids:
                self.source_ids.append(source_id)

    def demote_to_conditional(self, warning: str) -> None:
        self.medium += self.high
        self.high = 0
        if warning not in self.warnings:
            self.warnings.append(warning)


class RecommendationEngine:
    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self.repository = repository or KnowledgeRepository()

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        valid_answers = self._validate_answers(request.answers, request.language)
        method_candidates: dict[str, Candidate] = {}
        excluded_methods: dict[str, Candidate] = {}
        alternative_candidates: dict[str, Candidate] = {}
        problem_candidates: dict[str, Candidate] = {}
        followups: list[Followup] = []
        global_warnings: list[str] = []
        trace: list[RuleTrace] = []

        for rule in self.repository.rules():
            question_id = str(rule["question_id"])
            matched_answer = str(rule["answer_condition"])
            if matched_answer not in valid_answers.get(question_id, set()):
                continue

            target_ids = split_ids(rule.get("action_target_ids"))
            source_ids = split_ids(rule.get("source_ids"))
            action_type = str(rule["action_type"])
            priority = str(rule["priority_effect"])
            explanation = str(rule.get("explanation") or "")
            warnings = str(rule.get("warnings") or "")

            trace.append(
                RuleTrace(
                    rule_id=str(rule["rule_id"]),
                    question_id=question_id,
                    matched_answer=matched_answer,
                    action_type=action_type,
                    action_target_type=str(rule["action_target_type"]),
                    action_target_ids=target_ids,
                    priority_effect=priority,
                    explanation=explanation,
                    warnings=warnings,
                    source_ids=source_ids,
                )
            )

            if action_type == "promote_method":
                self._add_candidates(
                    method_candidates, target_ids, priority, explanation, warnings, source_ids
                )
            elif action_type == "exclude_method":
                self._add_candidates(
                    excluded_methods, target_ids, priority, explanation, warnings, source_ids
                )
            elif action_type == "recommend_alternative":
                self._add_candidates(
                    alternative_candidates, target_ids, priority, explanation, warnings, source_ids
                )
            elif action_type == "include_problem":
                self._add_candidates(
                    problem_candidates, target_ids, priority, explanation, warnings, source_ids
                )
            elif action_type == "ask_followup":
                followups.append(
                    Followup(
                        question_id=question_id,
                        explanation=explanation,
                        target_type=str(rule["action_target_type"]),
                        target_ids=target_ids,
                    )
                )
            elif action_type == "warn":
                message = warnings or explanation
                if message and message not in global_warnings:
                    global_warnings.append(message)

        all_method_ids = list(dict.fromkeys([*method_candidates, *excluded_methods]))
        method_rows = self.repository.methods(all_method_ids)
        self._apply_variable_domain_compatibility(
            self._single_answer(valid_answers, "Q01"),
            method_candidates,
            excluded_methods,
            method_rows,
            global_warnings,
            request.language,
        )
        self._apply_guarantee_compatibility(
            self._single_answer(valid_answers, "Q10"),
            method_candidates,
            excluded_methods,
            method_rows,
            global_warnings,
            request.language,
        )
        self._apply_failure_guidance(
            valid_answers,
            method_candidates,
            excluded_methods,
            global_warnings,
            request.language,
        )

        conflicting = set(method_candidates) & set(excluded_methods)
        if conflicting:
            global_warnings.append(
                "一部の手法に支持規則と除外規則が同時に一致しました。除外を優先しています。"
            )
        for method_id in excluded_methods:
            method_candidates.pop(method_id, None)

        method_ids = list(method_candidates)
        excluded_ids = list(excluded_methods)
        missing_rows = [method_id for method_id in excluded_ids if method_id not in method_rows]
        if missing_rows:
            method_rows.update(self.repository.methods(missing_rows))
        implementations = self.repository.method_implementations(
            method_ids, request.max_implementations_per_method
        )

        sorted_methods = sorted(method_candidates.values(), key=lambda item: item.ordering_key)
        first = [item for item in sorted_methods if item.high >= 2]
        conditional = [item for item in sorted_methods if item.high < 2]

        # Avoid an empty first-choice section when the user only answered a few questions.
        if not first and conditional:
            first = conditional[: min(3, request.max_methods)]
            conditional = conditional[len(first) :]

        first_entities = self._method_entities(
            first[: request.max_methods],
            method_rows,
            implementations,
            "first_choice",
            request.language,
        )
        conditional_entities = self._method_entities(
            conditional[: request.max_methods],
            method_rows,
            implementations,
            "conditional",
            request.language,
        )
        excluded_entities = self._method_entities(
            sorted(excluded_methods.values(), key=lambda item: item.ordering_key),
            method_rows,
            {},
            "excluded",
            request.language,
        )

        alternative_rows = self.repository.alternatives(list(alternative_candidates))
        alternatives = self._alternative_entities(
            sorted(alternative_candidates.values(), key=lambda item: item.ordering_key),
            alternative_rows,
            request.language,
        )

        problem_rows = self.repository.problems(list(problem_candidates))
        problems = self._problem_entities(
            sorted(problem_candidates.values(), key=lambda item: item.ordering_key),
            problem_rows,
            request.language,
        )

        return RecommendationResponse(
            alternatives_first=alternatives,
            first_choices=first_entities,
            conditional_choices=conditional_entities,
            excluded_methods=excluded_entities,
            candidate_problem_archetypes=problems,
            followups=self._dedupe_followups(followups),
            warnings=global_warnings,
            trace=trace,
            answered_question_count=len(valid_answers),
            dataset_version=self.repository.dataset_version(),
            disclaimer=(
                "候補選定支援であり、実問題での数値検証・安全性・最適性・商用条件を保証しません。"
                if request.language == "ja"
                else "This is decision support, not a guarantee of numerical performance, safety, "
                "optimality, or commercial terms."
            ),
        )

    def _apply_failure_guidance(
        self,
        answers: dict[str, tuple[str, ...]],
        method_candidates: dict[str, Candidate],
        excluded_methods: dict[str, Candidate],
        global_warnings: list[str],
        language: str,
    ) -> None:
        question_features = {
            str(row["question_id"]): str(row["mapped_feature_id"])
            for row in self.repository.recommendation_questions()
        }
        feature_answers = {
            question_features[question_id]: set(values)
            for question_id, values in answers.items()
            if question_id in question_features
        }
        guidance = self.repository.failure_guidance(
            list(dict.fromkeys([*method_candidates, *excluded_methods])), feature_answers
        )
        for item in guidance:
            candidate = method_candidates.get(item.method_id)
            if candidate is None:
                continue
            warning = item.warning if language == "ja" else f"{item.failure_mode_id}: {item.name}"
            if item.disposition == "exclude":
                method_candidates.pop(item.method_id)
                excluded = excluded_methods.setdefault(item.method_id, Candidate(item.method_id))
                excluded.absorb(candidate)
                excluded.add_rule("high", item.name, warning, list(item.source_ids))
            else:
                if warning not in candidate.warnings:
                    candidate.warnings.append(warning)
                for source_id in item.source_ids:
                    if source_id not in candidate.source_ids:
                        candidate.source_ids.append(source_id)
        if guidance:
            message = (
                f"{len(guidance)}件のfailure modeを回答条件と照合しました。"
                if language == "ja"
                else f"Matched {len(guidance)} failure modes against the supplied context."
            )
            if message not in global_warnings:
                global_warnings.append(message)

    def _apply_variable_domain_compatibility(
        self,
        domain: str | None,
        method_candidates: dict[str, Candidate],
        excluded_methods: dict[str, Candidate],
        method_rows: dict[str, dict[str, Any]],
        global_warnings: list[str],
        language: str,
    ) -> None:
        if domain is None or domain == "structured_or_unknown":
            return
        encoded_count = 0
        excluded_count = 0
        for method_id, candidate in list(method_candidates.items()):
            row = method_rows.get(method_id)
            if row is None:
                continue
            compatibility = self._variable_compatibility(
                domain, str(row.get("variable_types") or "")
            )
            if compatibility == "encoded":
                candidate.demote_to_conditional(
                    "変数domainを直接扱わず、encoding・relaxation・wrapperが必要です。"
                    if language == "ja"
                    else "This variable domain requires encoding, relaxation, or a wrapper."
                )
                encoded_count += 1
            elif compatibility == "incompatible":
                method_candidates.pop(method_id)
                excluded = excluded_methods.setdefault(method_id, Candidate(method_id))
                excluded.absorb(candidate)
                excluded.add_rule(
                    "high",
                    (
                        f"回答された変数domain ({domain}) と手法の対応 "
                        f"({row.get('variable_types')}) が一致しません。"
                        if language == "ja"
                        else f"The selected variable domain ({domain}) is incompatible with "
                        f"the method support ({row.get('variable_types')})."
                    ),
                    "変数変換を行う場合は、可行性・距離・保証が変わらないか確認してください。"
                    if language == "ja"
                    else (
                        "If variables are transformed, re-check feasibility, geometry, "
                        "and guarantees."
                    ),
                    split_ids(row.get("reference_source_ids")),
                )
                excluded_count += 1
        if encoded_count:
            global_warnings.append(
                f"{encoded_count}件の候補は変数encoding等が必要なため、条件付き候補へ下げました。"
                if language == "ja"
                else (
                    f"{encoded_count} candidates were demoted because variable encoding "
                    "is required."
                )
            )
        if excluded_count:
            global_warnings.append(
                f"{excluded_count}件の候補を変数domain不一致として除外しました。"
                if language == "ja"
                else f"{excluded_count} candidates were excluded for variable-domain mismatch."
            )

    def _apply_guarantee_compatibility(
        self,
        goal: str | None,
        method_candidates: dict[str, Candidate],
        excluded_methods: dict[str, Candidate],
        method_rows: dict[str, dict[str, Any]],
        global_warnings: list[str],
        language: str,
    ) -> None:
        if goal is None:
            return
        if goal not in {"gap_desired", "global_proof_required"}:
            return

        demoted_count = 0
        excluded_count = 0
        for method_id, candidate in list(method_candidates.items()):
            row = method_rows.get(method_id)
            if row is None or self._supports_certificate(row):
                continue
            if goal == "gap_desired":
                candidate.demote_to_conditional(
                    "この手法単独では一般に最適性gapや上下界を返しません。"
                    if language == "ja"
                    else "This method generally does not provide an optimality gap or bounds."
                )
                demoted_count += 1
            else:
                method_candidates.pop(method_id)
                excluded = excluded_methods.setdefault(method_id, Candidate(method_id))
                excluded.absorb(candidate)
                excluded.add_rule(
                    "high",
                    "大域最適性の証明要件を満たす一般的なcertificateがありません。"
                    if language == "ja"
                    else "The method lacks a general certificate for global optimality.",
                    "heuristicをincumbent生成に使う場合も、証明可能なsolverを別に必要とします。"
                    if language == "ja"
                    else (
                        "A heuristic may generate incumbents, but a certifying solver is still "
                        "required."
                    ),
                    split_ids(row.get("reference_source_ids")),
                )
                excluded_count += 1

        if demoted_count:
            global_warnings.append(
                f"{demoted_count}件の候補はgap・上下界を一般に返さないため、条件付きへ下げました。"
                if language == "ja"
                else (
                    f"{demoted_count} candidates were demoted because they generally do not "
                    "provide gaps or bounds."
                )
            )
        if excluded_count:
            global_warnings.append(
                f"{excluded_count}件の候補を大域証明要件との不一致で除外しました。"
                if language == "ja"
                else (
                    f"{excluded_count} candidates were excluded because they do not satisfy "
                    "the global-proof requirement."
                )
            )

    @staticmethod
    def _supports_certificate(row: dict[str, Any]) -> bool:
        scope = str(row.get("solution_scope") or "").lower()
        certificate = str(row.get("optimality_certificate") or "").lower()
        exactness = str(row.get("exactness") or "").lower()
        if "global_certificate" in scope:
            return True
        certificate_terms = (
            "gap",
            "bound",
            "dual",
            "primal",
            "unsat",
            "certificate",
            "proof",
        )
        if any(term in certificate for term in certificate_terms):
            return True
        return "exact" in exactness and "global" in scope

    @staticmethod
    def _variable_compatibility(domain: str, variable_types: str) -> str:
        tokens = [token.strip().lower() for token in variable_types.split(";") if token.strip()]
        if not tokens:
            return "unknown"
        native_terms = {
            "continuous": {"continuous", "real"},
            "integer": {"integer", "finite_domain", "discrete"},
            "binary": {"binary", "boolean", "finite_domain", "discrete"},
            "categorical": {"categorical", "discrete"},
            "mixed": {"mixed"},
        }.get(domain, {domain})
        encoded_markers = ("by_encoding", "by_model", "by_wrapper", "by_relaxation")

        for token in tokens:
            if token == "mixed" and domain != "mixed":
                return "native"
            if any(term == token for term in native_terms):
                return "native"
            if any(term in token for term in native_terms) and not any(
                marker in token for marker in encoded_markers
            ):
                return "native"

        if any(any(marker in token for marker in encoded_markers) for token in tokens):
            return "encoded"
        return "incompatible"

    def _validate_answers(
        self, answers: dict[str, list[str]], language: str
    ) -> dict[str, tuple[str, ...]]:
        questions = self.repository.questions(language)
        allowed = {row["question_id"]: set(row["allowed_answers"]) for row in questions}
        unknown_question_ids = set(answers) - set(allowed)
        if unknown_question_ids:
            raise ValueError(f"unknown question IDs: {sorted(unknown_question_ids)}")

        question_by_id = {str(row["question_id"]): row for row in questions}
        normalized: dict[str, tuple[str, ...]] = {}
        for question_id, values in answers.items():
            if not values:
                raise ValueError(f"answers for {question_id} must be non-empty")
            if len(values) != len(set(values)):
                raise ValueError(f"answers for {question_id} contain duplicate values")
            invalid = set(values) - allowed[question_id]
            if invalid:
                raise ValueError(
                    f"invalid answers for {question_id}: {sorted(invalid)}; "
                    f"allowed={sorted(allowed[question_id])}"
                )
            question = question_by_id[question_id]
            if question["answer_type"] == "single_choice" and len(values) != 1:
                raise ValueError(
                    f"single_choice answer for {question_id} must contain exactly one value"
                )
            if "unknown" in values and len(values) != 1:
                raise ValueError(f"unknown must be the sole value for {question_id}")
            normalized[question_id] = tuple(values)
        return normalized

    @staticmethod
    def _single_answer(answers: dict[str, tuple[str, ...]], question_id: str) -> str | None:
        values = answers.get(question_id)
        if values is None:
            return None
        return values[0]

    @staticmethod
    def _add_candidates(
        collection: dict[str, Candidate],
        target_ids: list[str],
        priority: str,
        explanation: str,
        warnings: str,
        source_ids: list[str],
    ) -> None:
        for target_id in target_ids:
            candidate = collection.setdefault(target_id, Candidate(target_id))
            candidate.add_rule(priority, explanation, warnings, source_ids)

    @staticmethod
    def _dedupe_followups(items: list[Followup]) -> list[Followup]:
        seen: set[tuple[str, str, tuple[str, ...]]] = set()
        result: list[Followup] = []
        for item in items:
            key = (item.question_id, item.target_type, tuple(item.target_ids))
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def _method_entities(
        self,
        candidates: list[Candidate],
        rows: dict[str, dict[str, Any]],
        implementations: dict[str, list[dict[str, Any]]],
        band: str,
        language: str,
    ) -> list[EntityRecommendation]:
        result: list[EntityRecommendation] = []
        for candidate in candidates:
            row = rows.get(candidate.entity_id)
            if row is None:
                continue
            name = str(row["name_ja"] if language == "ja" else row["name_en"])
            impls = [
                ImplementationSummary(
                    implementation_id=str(item["implementation_id"]),
                    library_name=str(item.get("library_name") or ""),
                    solver_name=str(item.get("solver_name") or ""),
                    language=str(item.get("language") or ""),
                    license=str(item.get("license") or "unknown"),
                    maintenance_status=str(item.get("maintenance_status") or "unknown"),
                    last_release=str(item.get("last_release") or "unknown"),
                    official_docs_url=str(item.get("official_docs_url") or ""),
                    official_repo_url=str(item.get("official_repo_url") or ""),
                    support_level=str(item.get("support_level") or ""),
                    notes=str(item.get("implementation_notes") or item.get("notes") or ""),
                )
                for item in implementations.get(candidate.entity_id, [])
            ]
            result.append(
                EntityRecommendation(
                    entity_id=candidate.entity_id,
                    name=name,
                    name_en=str(row.get("name_en") or ""),
                    summary=str(row.get("summary") or ""),
                    priority_band=band,  # type: ignore[arg-type]
                    supporting_rule_count=candidate.support_count,
                    high_priority_rule_count=candidate.high,
                    medium_priority_rule_count=candidate.medium,
                    reasons=candidate.reasons,
                    warnings=candidate.warnings,
                    source_ids=candidate.source_ids,
                    implementations=impls,
                )
            )
        return result

    @staticmethod
    def _alternative_entities(
        candidates: list[Candidate], rows: dict[str, dict[str, Any]], language: str
    ) -> list[EntityRecommendation]:
        result: list[EntityRecommendation] = []
        for candidate in candidates:
            row = rows.get(candidate.entity_id)
            if row is None:
                continue
            result.append(
                EntityRecommendation(
                    entity_id=candidate.entity_id,
                    name=str(row["name_ja"] if language == "ja" else row["name_en"]),
                    name_en=str(row.get("name_en") or ""),
                    summary=str(row.get("why_before_generic_optimization") or ""),
                    priority_band="alternative",
                    supporting_rule_count=candidate.support_count,
                    high_priority_rule_count=candidate.high,
                    medium_priority_rule_count=candidate.medium,
                    reasons=candidate.reasons + [str(row.get("preferred_approach") or "")],
                    warnings=candidate.warnings
                    + (
                        [str(row.get("false_positive_warning"))]
                        if row.get("false_positive_warning")
                        else []
                    ),
                    source_ids=list(
                        dict.fromkeys(candidate.source_ids + split_ids(row.get("source_ids")))
                    ),
                )
            )
        return result

    @staticmethod
    def _problem_entities(
        candidates: list[Candidate], rows: dict[str, dict[str, Any]], language: str
    ) -> list[EntityRecommendation]:
        result: list[EntityRecommendation] = []
        for candidate in candidates:
            row = rows.get(candidate.entity_id)
            if row is None:
                continue
            result.append(
                EntityRecommendation(
                    entity_id=candidate.entity_id,
                    name=str(row["name_ja"] if language == "ja" else row["name_en"]),
                    name_en=str(row.get("name_en") or ""),
                    summary=str(row.get("summary") or ""),
                    priority_band="conditional",
                    supporting_rule_count=candidate.support_count,
                    high_priority_rule_count=candidate.high,
                    medium_priority_rule_count=candidate.medium,
                    reasons=candidate.reasons,
                    warnings=candidate.warnings,
                    source_ids=list(
                        dict.fromkeys(candidate.source_ids + split_ids(row.get("source_ids")))
                    ),
                )
            )
        return result
