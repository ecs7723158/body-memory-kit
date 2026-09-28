import json
from pathlib import Path

from body_memory import BodyLog, BodyMemoryStore, import_markdown


FIXTURE = Path(__file__).parent / "fixtures" / "demo_body_log.md"


def test_schema_fields_and_demo_import(tmp_path: Path):
    logs = import_markdown(FIXTURE)
    assert len(logs) == 1
    log = logs[0]
    assert log.date == "2099-01-01"
    assert log.train_done is True
    assert log.session_tag == "A"
    assert set(log.red_flags) == {"sharp_pain", "radiating_pain", "dizziness", "chest_pain"}
    assert "bodybuilding" in (log.notes or "")
    assert BodyLog.from_mapping({}).weight_kg is None


def test_store_search_and_null_safe_summary(tmp_path: Path):
    store = BodyMemoryStore(tmp_path)
    store.add(BodyLog.from_mapping({"date": "2099-01-01", "notes": "fictional bodybuilding goal", "train_done": True}))
    assert len(store.search("bodybuilding")) == 1
    assert json.loads((tmp_path / "bodylogs.jsonl").read_text())["date"] == "2099-01-01"
    summary = store.weekly_summary(7)
    assert summary["entries"] == 0  # future fixture is outside today's window
    assert "trends" in summary


def test_bullet_import(tmp_path: Path):
    source = tmp_path / "export.md"
    source.write_text("- 2099-02-02\n- weight: 81 kg\n- sleep: 7.5 h\n- training: yes\n- notes: fictional test\n", encoding="utf-8")
    log = import_markdown(source)[0]
    assert log.weight_kg == 81
    assert log.sleep_h == 7.5
    assert log.train_done is True
