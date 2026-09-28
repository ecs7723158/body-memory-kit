from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import BodyLog, RED_FLAGS, SOURCES, SESSION_TAGS
from .store import BodyMemoryStore


def _bool_arg(value: str) -> bool:
    text = value.lower()
    if text in {"true", "yes", "1", "y"}:
        return True
    if text in {"false", "no", "0", "n"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="body-memory", description="Offline FIT v0.1 BodyLog memory")
    parser.add_argument("--root", default=str(Path.cwd() / "body-memory"), help="JSONL store directory")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="import Markdown/YAML-frontmatter logs")
    p_import.add_argument("path")

    p_add = sub.add_parser("add", help="add one BodyLog; omitted fields remain null")
    p_add.add_argument("--date")
    p_add.add_argument("--weight-kg", type=float)
    p_add.add_argument("--waist-cm", type=float)
    p_add.add_argument("--sleep-h", type=float)
    p_add.add_argument("--stress-1to5", type=float)
    p_add.add_argument("--train-done", type=_bool_arg)
    p_add.add_argument("--session-tag", choices=SESSION_TAGS)
    p_add.add_argument("--rpe-avg-1to10", type=float)
    p_add.add_argument("--pain-flag", type=_bool_arg)
    p_add.add_argument("--notes", default=None)
    for name in ("chest_cm", "arm_cm", "hip_cm", "thigh_cm", "bodyfat_est_pct", "protein_g_est", "calories_est", "mood_1to5"):
        p_add.add_argument("--" + name.replace("_", "-"), dest=name, type=float)
    p_add.add_argument("--steps", type=int)
    p_add.add_argument("--source", choices=SOURCES, default="manual")
    p_add.add_argument("--photo-id", action="append", dest="photo_ids", default=[])
    p_add.add_argument("--injury-note")
    for flag in RED_FLAGS:
        p_add.add_argument("--" + flag.replace("_", "-"), action="store_true")

    p_search = sub.add_parser("search", help="search BodyLog JSON fields")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=20)

    p_week = sub.add_parser("weekly-summary", help="descriptive 7- or 14-day summary")
    p_week.add_argument("--days", type=int, choices=(7, 14), default=7)

    args = parser.parse_args(argv)
    store = BodyMemoryStore(args.root)
    if args.command == "import":
        logs = store.import_markdown(args.path)
        print(json.dumps({"imported": len(logs), "logs": [log.to_dict() for log in logs]}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "add":
        data = vars(args).copy()
        data.pop("command", None)
        data.pop("root", None)
        data.pop("path", None)
        data.pop("query", None)
        data.pop("limit", None)
        data.pop("days", None)
        log = store.add(BodyLog.from_mapping(data))
        print(json.dumps({"ok": True, "log": log.to_dict()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "search":
        print(json.dumps([log.to_dict() for log in store.search(args.query, args.limit)], ensure_ascii=False, indent=2))
        return 0
    if args.command == "weekly-summary":
        print(json.dumps(store.weekly_summary(args.days), ensure_ascii=False, indent=2))
        return 0
    print("unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
