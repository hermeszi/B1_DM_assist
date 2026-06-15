# AI Development Log

## AI Usage Overview

This project was developed as a 2-hour prototype for the B1 Builders Programme. It is the **individual-use** companion to `class_assist` (the team/organisational project).

The goal was a single-user web app that helps a tabletop Dungeon Master generate **context-aware** content during play. Static random tables are context-blind; this app injects the live campaign state into every prompt so the output stays consistent with the story.

The main user flow is:

```text
Load campaign → adjust state → pick a kind + describe the moment → generate → review/edit → save to log
```

The AI generates one of four kinds — encounter, loot, npc, description — each as a structured record:

- title
- content (read-aloud / main text)
- mechanic (dice, DCs, stats, if any)
- secret (a DM-only twist)
- connects_to (a tie-in to an existing NPC or recent event)

The aim is not to replace the DM. The DM reviews and edits every result, decides what to save, and decides what to promote into the campaign's canon.

---

## AI Tools Used

### OpenRouter — `openai/gpt-4o-mini`

Used inside the app to turn the campaign state plus a kind request into a structured generation.

I chose OpenRouter because it provides an OpenAI-compatible API and let me test quickly with a low-cost model. The call was first tested separately with `curl` to confirm the API key and model ID worked before wiring it into the app.

### OpenRouter for pre-build planning

Before building, I used OpenRouter to compare second-project ideas and plans across several models (Claude, GPT, DeepSeek, Gemini). I asked them to validate the D&D helper as an individual-use B1 project, suggest a structure, and flag risks, then compared the responses rather than following one.

The comparison helped me make these choices:

- Reuse the `class_assist` architecture instead of designing a new one, because the same generate → validate → persist → history pattern fits a completely different domain.
- Use SQLite, since a single `campaigns` table already supports multiple stored games with no extra setup.
- Keep one fixed output contract for all kinds, instead of a different shape per kind.
- Defer PDF/source-material grounding to a later version, to protect the 2-hour scope.
- Use fictional campaign data only.

The models disagreed most on scope — some proposed elaborate tiered systems, sound effects, and separate NPC/location tables. I used that disagreement to scope *down* to the core differentiator (context-aware generation) and avoid scope creep.

### Claude Code

Used as the main coding assistant. I did not allow it to build large parts freely. I used a controlled, pseudocode-first workflow and reviewed every diff. It implemented:

- SQLite database helper functions
- the OpenRouter API service and context assembly
- FastAPI routes
- the DM console frontend
- the journal-notes feature and multi-campaign support
- tests and bug fixes

---

## Development Method

### Pseudocode-first workflow

Before letting Claude Code edit files, I asked it to explain the intended logic first.

```text
1. I describe the task.
2. Claude Code gives pseudocode or a short implementation plan.
3. I review the plan.
4. If acceptable, I allow Claude Code to edit the file.
5. I review the diff before accepting.
6. I run tests or manual checks.
7. I commit only after checking the output.
```

This let me catch misunderstandings about the data flow before any source file was touched.

### Contract-first approach

Instead of asking the AI to build freely, I defined the important structure first:

- Database shape
- AI output fields and validation rules
- Expected routes
- Test cases

The key contract files were:

```text
data/schema.sql
src/prompts.py
tests/test_ai_contract.py
CLAUDE.md
```

Claude Code then implemented one module at a time against these contracts, which made each change easy to review and stopped unrelated files from being changed.

### Reuse over rebuild

The single biggest decision was to **reuse the `class_assist` engine** rather than start fresh. The two apps share the same spine — generate → validate → persist → history — and differ only in the schema and the prompt. `students` became `campaigns`; `lesson_entries` became `generations` plus journal notes. This saved build time and, for the interview, demonstrates that the pattern transfers across domains rather than being copied once.

---

## The Core Idea: Context-Aware Generation

This is what makes the app different from a random table.

The campaign state (party level, location, tone, recent events, known NPCs) is injected into **every** prompt. On top of that, the most recent session-log entries — both AI generations the DM kept and the DM's own journal notes — are injected as recent context, capped to a fixed budget. So:

- Generated loot ties to recent events instead of being generic.
- NPCs stay consistent with what has already happened.
- A journal note ("the party betrayed Captain Hollow") feeds straight into the next generation.

The log becomes the rolling memory; `recent_events` stays as an optional curated summary. This closes a loop: play → note → richer context → better generation.

---

## Key Prompts Used

### Database module

```text
Implement src/database.py based on data/schema.sql.
Before writing code, give me pseudocode for the functions first.
Functions: init_db(), get_campaign(id), update_campaign(id, fields),
save_generation(gen), get_log(campaign_id).
Use stdlib sqlite3 only. Do not touch other files. Show the diff.
```

### AI service module

```text
Implement src/ai_service.py. Pseudocode first, then code after I approve.
- _call_model(system, user): POST to OpenRouter chat completions, OpenAI format,
  response_format json_object, key + model from env, load_dotenv() at import.
- generate(campaign, kind, dm_input, recent_log=None): reject kinds not in KINDS,
  build the user message from campaign state + recent log + dm_input, parse JSON,
  run validate_generation(), retry once on failure.
Do not hardcode keys. Do not touch other files.
```

(The `load_dotenv()`-at-import instruction was added deliberately: in the companion project, the first live call returned 401 because the environment was never loaded.)

### Backend routes

```text
Implement src/main.py with the routes in CLAUDE.md. Route-level pseudocode first.
GET /api/campaigns, POST /api/campaigns, GET /api/campaign/{id}, PUT /api/campaign/{id},
POST /api/generate, POST /api/save, POST /api/note, GET /api/campaign/{id}/log.
In /api/generate, fetch the recent log and pass it to generate(). Mount the static
frontend. Show the diff.
```

### Frontend

```text
Build the DM console in vanilla HTML + JS. UI-flow pseudocode first.
Three columns: editable campaign state; kind picker + describe-the-moment + Generate
with editable result + Save; session log (newest first, live-refresh on save).
Add a campaign selector + New Campaign form, and a Journal note box.
Use the selected campaign id in EVERY request. Keep it simple for a 2-hour prototype.
```

---

## Important Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| App type | Web app | B1 requires frontend and backend components. |
| Architecture | Reuse the `class_assist` spine | Same generate→validate→persist→history pattern; shows transfer across domains, and is far faster than rebuilding. |
| Core feature | Inject campaign state + recent log into every prompt | The differentiator vs a context-blind random table. |
| Output contract | One fixed JSON schema for all kinds | Uniform parsing/validation; `kind` only steers the content. |
| Database | SQLite | The `campaigns` table already supports multiple stored games with no schema change. |
| Session log | One unified journal (AI generations + manual notes via a `source` flag) | A single adventure record that also feeds future context. |
| AI provider | OpenRouter with `openai/gpt-4o-mini` | Low cost, fast, OpenAI-compatible. |
| Source-material grounding (PDF) | Deferred to a later version | Context-stuffing is feasible; retrieval/embeddings for large sourcebooks is out of 2-hour scope. |
| Campaign data | Fictional only | No personal-data risk; respect copyright of any real source material. |
| AI review | DM reviews before saving; DM decides canon | AI proposes, the human runs the table. |

---

## A Note on Guardrails (and how they differ from the companion project)

In `class_assist`, the guardrail is **factual integrity** — the AI must not invent a child's achievements or leak personal data. Here, the content is deliberately invented (that is the point), so the guardrail is **narrative integrity** — the AI must stay consistent with established lore and not contradict the campaign. Same engineering technique (a constrained system prompt + validated output), different failure mode to guard against. Recognising that contrast was a useful design insight.

---

## Testing Approach

### Automated tests

A contract test suite checks the structure of every AI generation:

- all required fields present: `title`, `content`, `mechanic`, `secret`, `connects_to`
- field types correct; optional fields may be empty
- invalid or incomplete output is rejected

The model call is mocked so tests run without real API requests.

### Manual AI testing

- **Context payoff:** generate loot after a recent event is logged → the item references that event, not a generic table result.
- **NPC motive:** an NPC generation includes a hidden motive in the `secret` field.
- **Scaling:** an encounter's mechanics scale to the party level.
- **Invalid kind:** a kind outside the allowed set is rejected (HTTP 400).
- **Log feedback:** add a journal note, then generate → the new content reflects the note.

### User testing

The main test was the DM loop:

```text
1. Load a campaign
2. Adjust state
3. Pick a kind + describe the moment
4. Generate
5. Review/edit
6. Save (appears in the log)
7. Write a journal note (also in the log; feeds future context)
```

Success criteria: generation is fast and stays on-theme; the log shows generations and notes together; a journal note visibly influences the next generation; switching campaigns keeps each game's state and log isolated.

---

## What Worked

Reusing the proven `class_assist` engine was the strongest decision — most of the architecture was already validated, so the work was mostly schema and prompt design. The contract-first plus pseudocode-first workflow kept Claude Code's changes small and reviewable. And the context-injection idea paid off visibly: generations referenced recent events instead of reading like a generic table.

## What Changed During Development

- Started with a single hardcoded campaign (`id=1`) and generalised to multiple stored campaigns once the core flow worked — no schema change was needed.
- Added manual journal notes after realising the single `recent_events` field was too thin to carry the story; the unified log feeding context replaced hand-maintaining that field.
- Deferred PDF source-material grounding to keep the prototype scope honest.

## What I Would Improve Next

- Ground generation in uploaded source material via retrieval/embeddings (for large sourcebooks, not just context-stuffing).
- AI-summarise the running log back into `recent_events`.
- NPC portrait / image generation.
- Favourites and search across the log; structured NPC and location tables.
- Export a session recap.

---

## Notes on AI Responsibility

The AI proposes; the DM disposes. Generated content is a suggestion the DM can accept, edit, or discard, and canon is only what the DM chooses to keep. The content is fiction, so personal-data risk is low — but any real source material used to ground the AI must respect copyright and stay out of the public repo.

## Extra

Full AI chat logs and planning notes are stored in:

```text
Extra/chat_logs/
```

Before committing or submitting, all logs should be checked for API keys and any other sensitive information, which should be removed.
