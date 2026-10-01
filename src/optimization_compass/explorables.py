"""Registry of interactive teaching figures ("explorables") that articles may embed.

An article opts in with ``::: explorable <id>``. The registry is the authority for which ids
exist, what question each answers, and what it must not be read as implying. The React
component for each id lives in ``site/src/features/explorable/registry.tsx``; a site test keeps
both sides in step.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources

from pydantic import BaseModel, ConfigDict, field_validator

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


_MAX_SCENE_SECONDS = 60.0


class Beat(BaseModel):
    """One step of a guided scene: the figure's settings, how long to show them, and what to say.

    The same beats drive the in-page guided playback, the recorded video, its captions and,
    later, the synthesized narration (ADR 0018).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    settings: dict[str, float | str]
    duration_s: float
    caption_ja: str
    narration_ja: str

    @field_validator("duration_s")
    @classmethod
    def _duration(cls, value: float) -> float:
        if not 2.0 <= value <= 15.0:
            raise ValueError("beat duration_s must be between 2 and 15 seconds")
        return value

    @field_validator("caption_ja", "narration_ja")
    @classmethod
    def _sentence(cls, value: str) -> str:
        if not value.strip() or not value.endswith("。"):
            raise ValueError("beat text must be a non-blank sentence ending with 。")
        return value


class Explorable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title_ja: str
    question: str
    fixed_conditions: str
    not_implied: str
    beats: tuple[Beat, ...] = ()

    @field_validator("id")
    @classmethod
    def _valid_id(cls, value: str) -> str:
        if not _ID_PATTERN.match(value):
            raise ValueError(f"explorable id must be kebab-case: {value!r}")
        return value

    @field_validator("title_ja", "question", "fixed_conditions", "not_implied")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("explorable text fields must not be blank")
        return value

    @field_validator("beats")
    @classmethod
    def _scene_length(cls, value: tuple[Beat, ...]) -> tuple[Beat, ...]:
        if sum(beat.duration_s for beat in value) > _MAX_SCENE_SECONDS:
            raise ValueError(f"a guided scene must not exceed {_MAX_SCENE_SECONDS:.0f} seconds")
        return value


class _Registry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int
    explorables: tuple[Explorable, ...]


@lru_cache(maxsize=1)
def load_explorables() -> dict[str, Explorable]:
    raw = resources.files("optimization_compass").joinpath("resources/explorables.json")
    registry = _Registry.model_validate(json.loads(raw.read_text(encoding="utf-8")))
    if registry.schema_version != 1:
        raise ValueError(f"unsupported explorable registry version: {registry.schema_version}")
    entries = {item.id: item for item in registry.explorables}
    if len(entries) != len(registry.explorables):
        raise ValueError("explorable ids must be unique")
    return entries


def is_valid_explorable_id(value: str) -> bool:
    return bool(_ID_PATTERN.match(value))
