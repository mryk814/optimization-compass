from __future__ import annotations

from pathlib import Path

from optimization_compass.content_models import load_content


def test_optimal_control_content_forms_a_robotics_reading_path() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = {page.content_id: page for page in load_content(root / "content")}

    family = pages["family.optimal-control"]
    assert list(family.prerequisites) == [
        "concept.trajectory-variable",
        "concept.dynamics-defect",
        "concept.path-terminal-constraints",
        "concept.time-discretization",
    ]
    assert "## Roboticsでの読み替え" in family.body
    assert "#/learn/concept.receding-horizon" in family.body

    expected = {
        "direct-shooting": ["concept.trajectory-variable", "concept.time-discretization"],
        "multiple-shooting": [
            "concept.trajectory-variable",
            "concept.dynamics-defect",
            "concept.time-discretization",
        ],
        "direct-collocation": [
            "concept.trajectory-variable",
            "concept.dynamics-defect",
            "concept.path-terminal-constraints",
            "concept.time-discretization",
        ],
        "ilqr-ddp": [
            "concept.trajectory-variable",
            "concept.time-discretization",
            "concept.receding-horizon",
        ],
    }
    for content_id, prerequisites in expected.items():
        page = pages[content_id]
        assert list(page.prerequisites) == prerequisites
        assert "## 次に読む" in page.body
        assert "#/learn/concept.trajectory-variable" in page.body
