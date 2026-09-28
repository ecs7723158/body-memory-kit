from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .models import BodyLog

ALIASES = {
    "weight": "weight_kg", "weightkg": "weight_kg", "waist": "waist_cm", "waistcm": "waist_cm",
    "sleep": "sleep_h", "sleep_hours": "sleep_h", "stress": "stress_1to5", "stress1to5": "stress_1to5",
    "training": "train_done", "training_session": "train_done", "train": "train_done",
    "session": "session_tag", "rpe": "rpe_avg_1to10", "pain": "pain_flag", "bodyfat": "bodyfat_est_pct",
    "bodyfatpct": "bodyfat_est_pct", "protein": "protein_g_est", "calories": "calories_est", "mood": "mood_1to5",
    "photos": "photo_ids", "injury": "injury_note", "source_type": "source",
}


def _key(raw: str) -> str:
    key = re.sub(r"[^a-z0-9]", "", raw.lower())
    return ALIASES.get(key, raw.strip().lower().replace("-", "_").replace(" ", "_"))


def _value(raw: str) -> Any:
    value = raw.strip().strip('"\'')
    if value.startswith("[") and value.endswith("]"):
        return [item.strip().strip('"\'') for item in value[1:-1].split(",") if item.strip()]
    return value


def _parse_pairs(lines: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in lines:
        line = line.strip()
        if line.startswith("-"):
            line = line[1:].strip()
        match = re.match(r"^([^:#]+):\s*(.*)$", line)
        if match:
            result[_key(match.group(1))] = _value(match.group(2))
    return result


def import_markdown(path: str | Path) -> list[BodyLog]:
    """Parse simple YAML frontmatter or bullet-style exported logs offline."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    frontmatter: dict[str, Any] = {}
    body_start = 0
    stripped = text.lstrip()
    if stripped.startswith("---"):
        start = next((i for i, line in enumerate(lines) if line.strip() == "---"), None)
        if start is not None:
            end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "---"), None)
            if end is not None:
                frontmatter = _parse_pairs(lines[start + 1:end])
                body_start = end + 1

    if frontmatter:
        if not frontmatter.get("notes"):
            body = "\n".join(line.strip() for line in lines[body_start:] if line.strip() and not line.lstrip().startswith("#"))
            if body:
                frontmatter["notes"] = body
        return [BodyLog.from_mapping(frontmatter)]

    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    notes: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        heading_date = re.match(r"^#{1,6}\s*(\d{4}-\d{2}-\d{2})\b", line)
        if heading_date:
            if current:
                if notes:
                    current["notes"] = " ".join(notes)
                records.append(current)
            current, notes = {"date": heading_date.group(1)}, []
            continue
        date_line = re.match(r"^-?\s*(\d{4}-\d{2}-\d{2})\s*:\s*(.*)$", line)
        if date_line:
            if current:
                if notes:
                    current["notes"] = " ".join(notes)
                records.append(current)
            current, notes = {"date": date_line.group(1), "notes": date_line.group(2).strip()}, []
            continue
        bullet_date = re.match(r"^-?\s*(\d{4}-\d{2}-\d{2})\s*$", line)
        if bullet_date:
            if current:
                if notes:
                    current["notes"] = " ".join(notes)
                records.append(current)
            current, notes = {"date": bullet_date.group(1)}, []
            continue
        pair = _parse_pairs([line])
        if pair:
            # A second date starts a new bullet-log record.
            if "date" in pair and current.get("date"):
                if notes:
                    current["notes"] = " ".join(notes)
                records.append(current)
                current, notes = {}, []
            current.update(pair)
        elif line.startswith("-"):
            notes.append(line[1:].strip())
        elif current:
            notes.append(line)
        else:
            notes.append(line)
    if current or notes:
        if notes:
            current["notes"] = " ".join(notes)
        records.append(current)
    return [BodyLog.from_mapping(record) for record in records if record]
