# dnd_gm_assist — project context for Claude Code

## What this is
A ~2-hour prototype for the 42 SG B1 Builders submission (individual-use project).
A Dungeon Master's assistant. The DM keeps a campaign's **state** (party level,
location, tone, recent events, known NPCs) and asks the app to generate context-aware
content: an encounter, a piece of loot, an NPC (or their response), or read-aloud
description. The current campaign state is injected into every prompt, so output stays
consistent with the established story instead of being context-blind like a static
random table. Generations are saved to a session log.

Same architecture as the companion project class_assist: **generate -> validate ->
persist -> history**. Different domain.

## Stack (do not change without asking)
- Backend: FastAPI + uvicorn (Python 3.12)
- DB: SQLite (stdlib sqlite3), file at data/gm_assist.db, schema in data/schema.sql
- Frontend: single src/static/index.html + app.js, vanilla JS, NO build step. Tailwind via CDN allowed.
- LLM: OpenRouter (OpenAI-compatible Chat Completions),
  https://openrouter.ai/api/v1/chat/completions. Key in env OPENROUTER_API_KEY,
  model in env MODEL (default openai/gpt-4o-mini).

## Contracts (source of truth — implement AGAINST these, do not redefine)
- DB shape: data/schema.sql
- AI output shape + validator: src/prompts.py (SYSTEM_PROMPT, KINDS, REQUIRED_KEYS, validate_generation)
- Tests that must pass: tests/test_ai_contract.py  ->  pytest -q

## Conventions
- ai_service MUST expose `_call_model(system, user) -> str` returning raw model text, so
  tests can monkeypatch it. It POSTs to OpenRouter with Authorization: Bearer
  <OPENROUTER_API_KEY>, OpenAI chat format, response_format={"type":"json_object"}.
- `generate(campaign, kind, dm_input) -> dict` builds the user message from the campaign
  state + kind + dm_input, calls _call_model with SYSTEM_PROMPT, parses JSON, runs
  validate_generation(), retries the model ONCE on an invalid payload. Reject any kind
  not in KINDS.
- Read the key from env, never hardcode. No hidden network calls in tests.

## Tasks (build in this order, one diff at a time)
1. src/database.py  : init_db(), get_campaign(campaign_id), update_campaign(campaign_id, fields),
                      save_generation(gen), get_log(campaign_id)
2. src/ai_service.py: _call_model(system, user), generate(campaign, kind, dm_input)
3. src/main.py      : GET /api/campaign, PUT /api/campaign, POST /api/generate (no save),
                      POST /api/save, GET /api/campaign/{id}/log; mount src/static at "/"
4. src/static/      : DM console — left: editable campaign state; centre: kind picker +
                      dm_input box + Generate + editable result (title/content/mechanic/
                      secret/connects_to) + Save; right: session log newest-first,
                      live-refresh on Save
5. make tests pass  : pytest -q
6. stretch          : "promote to lore" button appending a generation's gist to the
                      campaign's recent_events; mark favourites

## Run
- Dev:       uvicorn src.main:app --reload --port 8002
- Container: docker compose up --build   ->  http://localhost:8002
