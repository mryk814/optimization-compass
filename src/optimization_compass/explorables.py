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
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_PARAM_NAME_PATTERN = re.compile(r"^[a-z][A-Za-z0-9_]*$")
# Keys a lesson step uses for itself (``::: step seconds=6 predict answer=2``).
RESERVED_PARAM_NAMES = frozenset({"seconds", "predict", "answer"})


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


class Param(BaseModel):
    """One setting a guided beat or a lesson step may set on the figure.

    ``number`` and ``integer`` carry a closed range; ``choice`` carries its allowed words. The
    declaration is what lets an article's lesson be checked without running the figure.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["number", "integer", "choice"]
    min: float | None = None
    max: float | None = None
    choices: tuple[str, ...] | None = None
    # What a lesson's first step shows when it does not set this param.
    default: float | str | None = None

    @model_validator(mode="after")
    def _shape(self) -> Param:
        self._check_shape()
        if self.default is not None and (problem := self.problem_with(self.default)):
            raise ValueError(f"default {self.default!r} {problem}")
        return self

    def _check_shape(self) -> None:
        if self.type == "choice":
            if self.min is not None or self.max is not None:
                raise ValueError("a choice param takes choices, not min / max")
            choices = self.choices or ()
            if len(choices) < 2 or len(set(choices)) != len(choices):
                raise ValueError("a choice param needs at least two distinct choices")
            if any(not re.fullmatch(r"[A-Za-z0-9_-]+", choice) for choice in choices):
                raise ValueError("choices must be words of letters, digits, - and _")
            return
        if self.choices is not None:
            raise ValueError(f"a {self.type} param takes min / max, not choices")
        if self.min is None or self.max is None or not self.min < self.max:
            raise ValueError(f"a {self.type} param needs min < max")
        if self.type == "integer" and not (self.min.is_integer() and self.max.is_integer()):
            raise ValueError("an integer param needs whole-number min and max")

    def problem_with(self, value: float | str) -> str | None:
        """Why ``value`` is not a value of this param, or None when it is."""
        if self.type == "choice":
            if value not in (self.choices or ()):
                return f"must be one of {', '.join(self.choices or ())}"
            return None
        if isinstance(value, str):
            return "must be a number"
        assert self.min is not None and self.max is not None
        if not self.min <= value <= self.max:
            return f"must be within {self.min:g}..{self.max:g}"
        if self.type == "integer" and not float(value).is_integer():
            return "must be a whole number"
        return None


class Explorable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title_ja: str
    question: str
    fixed_conditions: str
    not_implied: str
    # None: the figure predates params; its beats are unchecked and it cannot be used in a lesson.
    params: dict[str, Param] | None = None
    beats: tuple[Beat, ...] = ()

    @field_validator("params")
    @classmethod
    def _param_names(cls, value: dict[str, Param] | None) -> dict[str, Param] | None:
        for name in value or {}:
            if not _PARAM_NAME_PATTERN.match(name):
                raise ValueError(f"param name must start with a lowercase letter: {name!r}")
            if name in RESERVED_PARAM_NAMES:
                raise ValueError(f"param name is reserved for lesson steps: {name!r}")
        return value

    @model_validator(mode="after")
    def _beats_use_declared_params(self) -> Explorable:
        if self.params is None:
            return self
        for number, beat in enumerate(self.beats, start=1):
            for key, value in beat.settings.items():
                if key not in self.params:
                    raise ValueError(f"beat {number} sets {key!r}, which params does not declare")
                problem = self.params[key].problem_with(value)
                if problem:
                    raise ValueError(f"beat {number} setting {key}={value!r} {problem}")
        return self

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


_EMBED = re.compile(r"^:{3,} (?:explorable|lesson) (\S+)", re.MULTILINE)


def embedded_figure_ids(body: str) -> tuple[str, ...]:
    """Figure ids an article body embeds, as ``::: explorable <id>`` or ``:::: lesson <id>``."""
    return tuple(_EMBED.findall(body))
