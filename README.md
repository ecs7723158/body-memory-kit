# body-memory-kit

Offline Python package and CLI for long-term bodybuilding memory using the FIT v0.1 `BodyLog` shape. It stores metric observations locally as JSONL and performs only descriptive 7/14-day summaries. It does not diagnose, prescribe, or replace a clinician.

## Non-medical disclaimer
This is a personal organization tool, not medical advice or a health-monitoring device. Do not use it to make urgent health decisions. Stop training and seek qualified medical help for concerning symptoms; in particular, treat sharp pain, radiating pain, dizziness, or chest pain as red flags.

## Gemini NotebookLM / GPT export flow

1. Create an inbox: `mkdir -p ~/Projects/body-memory-kit/inbox`.
2. In Gemini NotebookLM, export the relevant note/conversation as `.md` or `.txt` (or copy the Markdown text) into that `inbox/`. This is a manual sync **from** Gemini; no API access or background sync is used.
3. GPT/Codex notes follow the same path: save/export `.md` or `.txt` into `inbox/`.
4. Import locally: `body-memory --root ./body-memory import inbox/my-export.md`.

Only put data you intend to keep locally in the inbox. Review imported fields before relying on them. The demo fixture is fictional and contains no personal medical data.

## Install and CLI

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
body-memory --root ./body-memory add --date 2026-09-28 --notes 'manual check-in' --source manual
body-memory --root ./body-memory search bodybuilding
body-memory --root ./body-memory weekly-summary --days 7
```

`add` accepts FIT v0.1 fields such as `--weight-kg`, `--sleep-h`, `--train-done true`, `--session-tag A`, and red flags such as `--sharp-pain`. Missing required values are stored as `null`. See `schema/bodylog.schema.json` for the exact contract.

## FIT v0.1 fields

Required: `date`, `weight_kg`, `waist_cm`, `sleep_h`, `stress_1to5`, `train_done`, `session_tag`, `rpe_avg_1to10`, `pain_flag`, `notes` (missing values may be `null`). Optional: `chest_cm`, `arm_cm`, `hip_cm`, `thigh_cm`, `bodyfat_est_pct`, `steps`, `protein_g_est`, `calories_est`, `mood_1to5`, `source` (`gemini_notebook|gpt_export|manual`), `photo_ids`, `injury_note`. Red flags are `sharp_pain`, `radiating_pain`, `dizziness`, and `chest_pain` under `red_flags`.
