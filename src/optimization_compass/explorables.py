"""Registry of interactive teaching figures ("explorables") that articles may embed.

An article opts in with ``::: explorable <id>``. Each figure is one folder,
``site/src/features/explorable/figures/<id>/``: its ``meta.json`` is the authority for the id,
the question the figure answers, and what it must not be read as implying, and its
``Figure.tsx`` is the React component the site discovers by the same folder name. Keeping
everything about a figure in its folder lets figures be added in parallel without touching a
shared list.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

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


# The figures live in the site source, so content is compiled from a repository checkout
# (as it already is for content/); an installed wheel does not carry them.
FIGURES_DIR = Path(__file__).resolve().parents[2] / "site/src/features/explorable/figures"


def read_explorables(figures_dir: Path) -> dict[str, Explorable]:
    """Validate every ``<figures_dir>/<id>/meta.json``; the folder name must be the id."""
    if not figures_dir.is_dir():
        raise ValueError(f"explorable figures not found: {figures_dir}")
    entries: dict[str, Explorable] = {}
    for folder in sorted(path for path in figures_dir.iterdir() if path.is_dir()):
        meta = folder / "meta.json"
        if not meta.is_file():
            raise ValueError(f"{meta}: every figure folder needs a meta.json")
        try:
            entry = Explorable.model_validate(json.loads(meta.read_text(encoding="utf-8")))
        except ValueError as error:
            raise ValueError(f"{meta}: {error}") from error
        if entry.id != folder.name:
            raise ValueError(f"{meta}: id {entry.id!r} must match its folder name {folder.name!r}")
        entries[entry.id] = entry
    return entries


@lru_cache(maxsize=1)
def load_explorables() -> dict[str, Explorable]:
    return read_explorables(FIGURES_DIR)


def is_valid_explorable_id(value: str) -> bool:
    return bool(_ID_PATTERN.match(value))
