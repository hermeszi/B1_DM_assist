# AI Usage Overview

## AI Tools
- **OpenRouter - openai/gpt-4o-mini** (in-app): generates campaign-aware content
  (encounter / loot / npc / description) from the injected campaign state. Reliable JSON
  via the OpenAI-compatible API.
- **Claude Code** (development agent): implemented each module against hand-written contracts.
- [Declare any others used.]

## Development Approach with AI
**Method: contract-first** (reused from the companion project). I authored the DB schema,
the AI output schema + validator (`src/prompts.py`), and the tests by hand, then had Claude
Code implement against them one file per task, reviewing each diff.

### Key prompts
- [Paste your actual Claude Code task prompts.]

### Key review points and decisions
| Decision | Choice | Why |
|---|---|---|
| Make generation context-aware | Inject campaign state into every prompt | The core differentiator vs a static random table |
| Reuse class_assist architecture | Same generate->validate->persist->history spine | Proven, fast, and shows one pattern across two domains |
| Output contract | One fixed JSON schema across all kinds | Keeps parsing/validation uniform; kind only steers content |

## Reflection
- What worked:
- What failed / changed:
- What I'd improve:

## Extra
- Full AI chat-session logs are in the /Extra folder. [Scrub any API keys first.]
