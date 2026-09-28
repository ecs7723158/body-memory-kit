from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

SOURCES = ("gemini_notebook", "gpt_export", "manual")
SESSION_TAGS = ("A", "B", "C", "other")
REQUIRED_FIELDS = (
    "date", "weight_kg", "waist_cm", "sleep_h", "stress_1to5", "train_done",
    "session_tag", "rpe_avg_1to10", "pain_flag", "notes",
)
OPTIONAL_FIELDS = (
    "chest_cm", "arm_cm", "hip_cm", "thigh_cm", "bodyfat_est_pct", "steps",
    "protein_g_est", "calories_est", "mood_1to5", "source", "photo_ids", "injury_note",
)
RED_FLAGS = ("sharp_pain", "radiating_pain", "dizziness", "chest_pain")


def _number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    text = str(value).strip().lower().replace("kg", "").replace("cm", "").replace("h", "")
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def _boolean(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "y", "1", "done", "completed"}:
        return True
    if text in {"false", "no", "n", "0", "not done", "none"}:
        return False
    return None


@dataclass
class BodyLog:
    """FIT v0.1 BodyLog. Missing required values are represented as None."""

    date: str | None = None
    weight_kg: float | int | None = None
    waist_cm: float | int | None = None
    sleep_h: float | int | None = None
    stress_1to5: float | int | None = None
    train_done: bool | None = None
    session_tag: str | None = None
    rpe_avg_1to10: float | int | None = None
    pain_flag: bool | None = None
    notes: str | None = None
    chest_cm: float | int | None = None
    arm_cm: float | int | None = None
    hip_cm: float | int | None = None
    thigh_cm: float | int | None = None
    bodyfat_est_pct: float | int | None = None
    steps: int | None = None
    protein_g_est: float | int | None = None
    calories_est: float | int | None = None
    mood_1to5: float | int | None = None
    source: str | None = "manual"
    photo_ids: list[str] = field(default_factory=list)
    injury_note: str | None = None
    red_flags: dict[str, bool] = field(default_factory=lambda: {name: False for name in RED_FLAGS})

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "BodyLog":
        values = dict(data)
        red = values.pop("red_flags", {}) or {}
        if not isinstance(red, dict):
            red = {}
        flags = {name: bool(_boolean(red.get(name))) if _boolean(red.get(name)) is not None else False for name in RED_FLAGS}
        for name in RED_FLAGS:
            if name in values:
                parsed = _boolean(values.pop(name))
                flags[name] = parsed if parsed is not None else False
        kwargs: dict[str, Any] = {name: None for name in REQUIRED_FIELDS}
        kwargs.update({name: None for name in OPTIONAL_FIELDS})
        kwargs["source"] = "manual"
        kwargs["photo_ids"] = []
        kwargs["red_flags"] = flags
        for key, value in values.items():
            if key in kwargs:
                kwargs[key] = value
        for key in ("weight_kg", "waist_cm", "sleep_h", "stress_1to5", "rpe_avg_1to10", "chest_cm", "arm_cm", "hip_cm", "thigh_cm", "bodyfat_est_pct", "protein_g_est", "calories_est", "mood_1to5"):
            kwargs[key] = _number(kwargs[key])
        if kwargs["steps"] is not None:
            parsed_steps = _number(kwargs["steps"])
            kwargs["steps"] = int(parsed_steps) if parsed_steps is not None else None
        for key in ("train_done", "pain_flag"):
            kwargs[key] = _boolean(kwargs[key])
        if kwargs["date"] is not None:
            kwargs["date"] = str(kwargs["date"]).strip()
        if kwargs["session_tag"] is not None:
            session = str(kwargs["session_tag"]).strip()
            kwargs["session_tag"] = session if session in SESSION_TAGS else "other"
        if kwargs["source"] not in SOURCES and kwargs["source"] is not None:
            kwargs["source"] = "manual"
        if kwargs["notes"] is not None:
            kwargs["notes"] = str(kwargs["notes"]).strip()
        if kwargs["photo_ids"] is None:
            kwargs["photo_ids"] = []
        elif isinstance(kwargs["photo_ids"], str):
            kwargs["photo_ids"] = [part.strip() for part in kwargs["photo_ids"].split(",") if part.strip()]
        else:
            kwargs["photo_ids"] = [str(item) for item in kwargs["photo_ids"]]
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_valid_date(self) -> bool:
        if not self.date:
            return False
        try:
            date.fromisoformat(self.date)
        except ValueError:
            return False
        return True
