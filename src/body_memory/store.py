from __future__ import annotations

import json
import re
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from .models import BodyLog
from .parser import import_markdown


class BodyMemoryStore:
    """Small JSONL store; no network, database, or medical inference."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "bodylogs.jsonl"

    def add(self, log: BodyLog) -> BodyLog:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log.to_dict(), ensure_ascii=False) + "\n")
        return log

    def import_markdown(self, path: str | Path) -> list[BodyLog]:
        logs = import_markdown(path)
        for log in logs:
            self.add(log)
        return logs

    def list(self) -> list[BodyLog]:
        if not self.path.exists():
            return []
        logs: list[BodyLog] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                logs.append(BodyLog.from_mapping(json.loads(line)))
        return logs

    def search(self, query: str, limit: int = 20) -> list[BodyLog]:
        tokens = [token for token in re.split(r"\s+", query.lower().strip()) if token]
        if not tokens:
            return []
        scored: list[tuple[int, str, BodyLog]] = []
        for log in self.list():
            blob = json.dumps(log.to_dict(), ensure_ascii=False).lower()
            score = sum(token in blob for token in tokens)
            if score:
                scored.append((score, log.date or "", log))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored[:limit]]

    def weekly_summary(self, days: int = 7) -> dict:
        if days not in (7, 14):
            raise ValueError("days must be 7 or 14")
        today = date.today()
        start = today - timedelta(days=days - 1)
        logs = [log for log in self.list() if log.is_valid_date() and start <= date.fromisoformat(log.date) <= today]
        logs.sort(key=lambda log: log.date or "")

        def nums(name: str) -> list[float]:
            return [float(getattr(log, name)) for log in logs if getattr(log, name) is not None]

        def avg(name: str) -> float | None:
            values = nums(name)
            return round(sum(values) / len(values), 2) if values else None

        def trend(name: str) -> dict[str, float | None]:
            values = nums(name)
            return {"first": values[0] if values else None, "last": values[-1] if values else None,
                    "change": round(values[-1] - values[0], 2) if len(values) > 1 else None}

        return {
            "window_days": days,
            "start": start.isoformat(),
            "end": today.isoformat(),
            "entries": len(logs),
            "training_sessions": sum(1 for log in logs if log.train_done is True),
            "pain_flags": sum(1 for log in logs if log.pain_flag is True),
            "red_flag_entries": sum(1 for log in logs if any(log.red_flags.values())),
            "averages": {"weight_kg": avg("weight_kg"), "sleep_h": avg("sleep_h"), "stress_1to5": avg("stress_1to5"), "rpe_avg_1to10": avg("rpe_avg_1to10")},
            "trends": {"weight_kg": trend("weight_kg"), "sleep_h": trend("sleep_h"), "stress_1to5": trend("stress_1to5")},
            "disclaimer": "Non-medical descriptive summary; red flags should be handled by a qualified professional.",
        }
