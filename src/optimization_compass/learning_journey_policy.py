from __future__ import annotations

from collections.abc import Mapping, Set
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonBlank = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
JourneyAssetType = Literal[
    "scenario",
    "comparison",
    "visualization_artifact",
    "content",
]
JourneyAssetPolicy = Literal["standalone", "warning", "error"]

JOURNEY_ASSET_TYPES = frozenset({"scenario", "comparison", "visualization_artifact", "content"})


class JourneyPolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LearningJourneyAssetPolicy(JourneyPolicyModel):
    asset_type: JourneyAssetType
    asset_id: NonBlank
    policy: JourneyAssetPolicy
    reason: NonBlank


class LearningJourneyAssetPolicyIndex(JourneyPolicyModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    assets: list[LearningJourneyAssetPolicy]

    @model_validator(mode="after")
    def validate_unique_assets(self) -> Self:
        keys = [(asset.asset_type, asset.asset_id) for asset in self.assets]
        if len(keys) != len(set(keys)):
            raise ValueError("learning journey asset policy keys must be unique")
        return self


def load_learning_journey_asset_policy(
    path: Path,
    *,
    inventories: Mapping[str, Set[str]] | None = None,
) -> LearningJourneyAssetPolicyIndex:
    index = LearningJourneyAssetPolicyIndex.model_validate_json(path.read_text(encoding="utf-8"))
    if inventories is not None:
        validate_learning_journey_asset_policy_references(index, inventories=inventories)
    return index


def validate_learning_journey_asset_policy_references(
    index: LearningJourneyAssetPolicyIndex,
    *,
    inventories: Mapping[str, Set[str]],
) -> None:
    inventory_types = set(inventories)
    if inventory_types != JOURNEY_ASSET_TYPES:
        missing = sorted(JOURNEY_ASSET_TYPES - inventory_types)
        unexpected = sorted(inventory_types - JOURNEY_ASSET_TYPES)
        details = [
            *(f"missing={','.join(missing)}" for _ in [None] if missing),
            *(f"unexpected={','.join(unexpected)}" for _ in [None] if unexpected),
        ]
        raise ValueError(
            "asset policy inventories must cover the exact contract: " + "; ".join(details)
        )

    missing_references = [
        f"{asset.asset_type}:{asset.asset_id}"
        for asset in index.assets
        if asset.asset_id not in inventories[asset.asset_type]
    ]
    if missing_references:
        raise ValueError(
            "learning journey asset policy references missing assets: "
            + ", ".join(sorted(missing_references))
        )
