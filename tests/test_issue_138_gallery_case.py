from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
GALLERY_SEED = ROOT / "data/seeds/site_gallery.json"


def test_multi_fidelity_simulator_case_declares_cost_and_failure_policy() -> None:
    payload = json.loads(GALLERY_SEED.read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == "multi-fidelity-simulator")

    assert case["problem_archetype_id"] == "PA014"
    assert case["candidate_methods"] == [
        {
            "method_id": "M_BAYESIAN_OPT_GP",
            "reason": (
                "高 fidelity の評価を節約しながら、低 fidelity の観測も含めた surrogate と"
                "不確実性から次の simulator call を選ぶため"
            ),
        }
    ]
    assert [item["method_id"] for item in case["conditional_methods"]] == ["M_HYPERBAND_ASHA"]
    assert {item["method_id"] for item in case["excluded_methods"]} == {"M_NELDER_MEAD"}
    assert set(case["implementation_ids"]) == {"I_BOTORCH", "I_OPTUNA", "I_RAY_TUNE"}
    assert {"S035", "S038", "S059", "S069", "S075"} <= set(case["source_ids"])
    assert case["map_node_id"] in {
        f"answer:{question}:{answer}" for question, answer in case["question_answers"].items()
    }
    assert "c_L=1" in case["decision_variables"]
    assert "c_H=12" in case["decision_variables"]
    assert "high-fidelity-equivalent" in case["constraints"]
    assert "status" in case["constraints"]
    assert "目的値の大きな値へ置換しない" in case["constraints"]
    assert case["comparison_ids"] == ["COMPARE_BO_MULTIFIDELITY_COST"]
    assert case["visualization_ids"] == [
        "SCENARIO_BO_1D_EXPLORE_NOISELESS",
        "SCENARIO_BO_1D_EXPLOIT_NOISELESS",
        "SCENARIO_BO_1D_EXPLORE_SMALL_NOISE",
        "SCENARIO_BO_1D_EXPLOIT_SMALL_NOISE",
        "SCENARIO_BO_1D_MULTIFIDELITY_LEDGER",
        "SCENARIO_BO_1D_HIGH_FIDELITY_BASELINE",
        "SCENARIO_BO_1D_LOW_FIDELITY_BIAS",
    ]
    assert "high-fidelity-equivalent costで同期" in case["practical_notes"]
    assert "順位反転" in case["practical_notes"]
    compile(case["python_example"], "multi-fidelity-simulator", "exec")


def test_bo_guidance_separates_method_defaults_evaluation_policy_and_recommendation() -> None:
    method = (ROOT / "content/methods/bayesian-optimization.md").read_text(encoding="utf-8")
    family = (ROOT / "content/methods/family-expensive-black-box.md").read_text(encoding="utf-8")

    for term in ("method", "implementation", "evaluation policy", "recommendation"):
        assert term in method
    assert "library versionとdefault値" in method
    for term in ("cost model", "target fidelity", "補正model"):
        assert term in method
    assert "low/highで反転" in method
    assert "failed領域の近傍を繰り返し提案" in method
    assert "high-fidelity-equivalent cost" in family
    assert "一般的なpolicy順位は決めません" in family
