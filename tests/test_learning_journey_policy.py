from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.learning_journey_policy import (
    JOURNEY_ASSET_TYPES,
    LearningJourneyAssetPolicyIndex,
    load_learning_journey_asset_policy,
    validate_learning_journey_asset_policy_references,
)

ROOT = Path(__file__).parents[1]
POLICY_SEED = ROOT / "data/seeds/learning_journey_asset_policy.json"


def test_canonical_asset_policy_seed_is_strict_and_explicit() -> None:
    index = load_learning_journey_asset_policy(
        POLICY_SEED,
        inventories={asset_type: set() for asset_type in JOURNEY_ASSET_TYPES},
    )

    assert index.contract_version == "1.0.0"
    assert index.assets == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("asset_type", "trace"),
        ("policy", "implicit_standalone"),
        ("reason", "   "),
    ],
)
def test_asset_policy_rejects_unknown_vocabulary_and_blank_reasons(field: str, value: str) -> None:
    asset = {
        "asset_type": "scenario",
        "asset_id": "SCENARIO_EXAMPLE",
        "policy": "warning",
        "reason": "Not yet connected to a learning journey.",
    }
    asset[field] = value

    with pytest.raises(ValidationError):
        LearningJourneyAssetPolicyIndex.model_validate(
            {"contract_version": "1.0.0", "assets": [asset]}
        )


def test_asset_policy_rejects_duplicate_asset_keys() -> None:
    asset = {
        "asset_type": "visualization_artifact",
        "asset_id": "ARTIFACT_EXAMPLE",
        "policy": "standalone",
        "reason": "Published as an intentionally standalone teaching artifact.",
    }

    with pytest.raises(ValidationError, match="asset policy keys must be unique"):
        LearningJourneyAssetPolicyIndex.model_validate(
            {"contract_version": "1.0.0", "assets": [asset, asset]}
        )


def test_reference_validation_rejects_missing_policy_assets() -> None:
    payload = {
        "contract_version": "1.0.0",
        "assets": [
            {
                "asset_type": "content",
                "asset_id": "missing-page",
                "policy": "warning",
                "reason": "The page is not connected to a journey.",
            }
        ],
    }
    index = LearningJourneyAssetPolicyIndex.model_validate(payload)
    with pytest.raises(ValueError, match="content:missing-page"):
        validate_learning_journey_asset_policy_references(
            index,
            inventories={asset_type: set() for asset_type in JOURNEY_ASSET_TYPES},
        )


def test_reference_validation_requires_all_asset_inventories() -> None:
    with pytest.raises(ValueError, match="exact contract"):
        load_learning_journey_asset_policy(POLICY_SEED, inventories={"scenario": set()})
