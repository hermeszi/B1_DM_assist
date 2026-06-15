# dnd_gm_assist (Individual use)

## Overview

### Problem
- **Who is affected?** A tabletop RPG Dungeon Master — specifically the "forever DM" who always runs the game and rarely gets to be surprised by it.

- **What is the issue?** A DM improvises constantly: encounters, loot, NPC reactions, descriptions. The usual aid is random tables, but they are **context-blind** — they will offer a desert ambush in a frozen cavern, or generic loot that ignores the story so far. Keeping improvised content consistent with the campaign's location, tone, party level, and recent events is manual work, and it is hard to be both consistent *and* surprised.

### Outcome
- A single-user web app that holds a campaign's live **state** and generates **context-aware** content — an encounter, a piece of loot, an NPC (or their spoken response), or read-aloud description — that stays consistent with the established world. The current state plus a rolling session log are injected into every prompt, so generated loot can reference recent events and NPCs remember the story. Generations and the DM's own journal notes are saved to a shared session log, and that log feeds back into future generation. Multiple campaigns can be stored and loaded.

- This is the **individual-use** companion to a team/organisational project (`class_assist`). Both run the same engine — generate → validate → persist → history — repointed to a different domain.

---

## Demo
[Youtube demo](https://youtu.be/hdoOrQmwY74)
1. Load a campaign, or create a new one, from the campaign selector.
2. Review/edit the campaign state — party level, location, tone, recent events, known NPCs.
3. Pick a kind (encounter / loot / npc / description) and optionally describe the moment.
4. **Generate** → a titled result: content to read aloud, any mechanics, a DM-only secret, and a tie-in to existing lore.
5. Edit if needed, **Save** → it appears in the session log.
6. Write a **journal note** of what actually happened → also saved to the log, and fed into the context of future generations.

<img width="2026" height="1190" alt="B1_DM_assist" src="https://github.com/user-attachments/assets/961eedf2-f7da-4e6d-9915-c2e97483b475" />


---

## Technology Stack
### Frontend
- HTML + vanilla JavaScript (no build step), Tailwind via CDN.

### Backend
- Python, FastAPI, uvicorn.
- SQLite (stdlib `sqlite3`).
- OpenRouter (OpenAI-compatible Chat Completions), model `openai/gpt-4o-mini`, called via `httpx`.

---

## Installation
1. `cp .env.example .env` and set `OPENROUTER_API_KEY` (and `MODEL`, default `openai/gpt-4o-mini`).
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. `uvicorn src.main:app --reload --port 8002`  (or `docker compose up --build`)
4. Open `http://localhost:8002`.

## Usage
Load or create a campaign → edit its state → pick a kind, optionally describe the moment → Generate → review/edit → Save. Write journal notes as the session unfolds; both saved generations and notes appear in the session log (newest first) and feed the context of later generations. Switch campaigns from the selector — each keeps its own state and log.

## Project Structure
- `src/` — `main.py` (routes), `database.py` (SQLite), `ai_service.py` (OpenRouter call, validation, context assembly), `prompts.py` (system prompt + output contract), `static/` (DM console).
- `data/schema.sql` — schema + a fictional seed campaign. The live `.db` is gitignored.
- `tests/` — contract tests (`pytest`).
- `docs/ai-dev/` — AI usage log.
- `Extra/` — full AI chat-session logs.

## Data & Safety
All campaign data is fictional, so there is no personal-data risk. If you later ground the AI in your own source material (a planned feature), do not commit copyrighted sourcebooks or their extracted text — use your own homebrew or the openly-licensed D&D SRD. The live database is gitignored.
