from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import EntityRecommendation, RecommendationRequest


def ids(items: list[EntityRecommendation]) -> set[str]:
    return {item.entity_id for item in items}


def test_binary_problem_promotes_native_discrete_methods(engine: RecommendationEngine) -> None:
    result = engine.recommend(
        RecommendationRequest(
            answers={
                "Q01": ["binary"],
                "Q03": ["linear"],
                "Q04": ["logical_or_combinatorial"],
                "Q10": ["gap_desired"],
            }
        )
    )
    recommended = ids(result.first_choices + result.conditional_choices)
    assert "M_BRANCH_CUT" in recommended
    assert "M_CP_SAT" in recommended


def test_non_differentiable_exclusion_wins(engine: RecommendationEngine) -> None:
    result = engine.recommend(
        RecommendationRequest(
            answers={
                "Q04": ["none"],
                "Q05": ["autodiff", "not_differentiable"],
                "Q09": ["local_is_fine"],
            }
        )
    )
    assert "M_BFGS" in ids(result.excluded_methods)
    assert "M_BFGS" not in ids(result.first_choices + result.conditional_choices)
    assert any("除外を優先" in warning for warning in result.warnings)


def test_expensive_experiment_promotes_bayesian_optimization(
    engine: RecommendationEngine,
) -> None:
    result = engine.recommend(
        RecommendationRequest(
            answers={
                "Q02": ["experiment_only"],
                "Q05": ["unreliable_or_none"],
                "Q06": ["hours_or_more"],
                "Q09": ["global_candidate_desired"],
            }
        )
    )
    assert "M_BAYESIAN_OPT_GP" in ids(result.first_choices)


def test_binary_gap_request_demotes_non_certifying_local_search(
    engine: RecommendationEngine,
) -> None:
    result = engine.recommend(
        RecommendationRequest(
            answers={
                "Q01": ["binary"],
                "Q10": ["gap_desired"],
                "Q11": ["scheduling_routing"],
            }
        )
    )
    assert "M_LOCAL_SEARCH_COMBINATORIAL" not in ids(result.first_choices)
    assert "M_LOCAL_SEARCH_COMBINATORIAL" in ids(result.conditional_choices)


def test_binary_domain_excludes_continuous_cma_es(engine: RecommendationEngine) -> None:
    result = engine.recommend(
        RecommendationRequest(
            answers={
                "Q01": ["binary"],
                "Q05": ["unreliable_or_none"],
                "Q09": ["global_candidate_desired"],
            }
        )
    )
    assert "M_CMA_ES" in ids(result.excluded_methods)
    assert "M_CMA_ES" not in ids(result.first_choices + result.conditional_choices)


def test_invalid_answer_is_rejected(engine: RecommendationEngine) -> None:
    try:
        engine.recommend(RecommendationRequest(answers={"Q01": ["banana"]}))
    except ValueError as exc:
        assert "invalid answers" in str(exc)
    else:
        raise AssertionError("invalid answer should fail")
