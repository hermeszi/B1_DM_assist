"""AI contract for dnd_gm_assist.

System prompt + output schema + validator. ai_service.generate() MUST pass every
model payload through validate_generation() before it is shown or saved.

The point of the tool: the AI is *campaign-aware*. The current campaign state
(level, location, tone, recent events, known NPCs) is injected into every prompt so
generated content stays consistent with the established story, instead of being
context-blind like a static random table.
"""

KINDS = {"encounter", "loot", "npc", "description"}

REQUIRED_KEYS = {"title", "content", "mechanic", "secret", "connects_to"}

SYSTEM_PROMPT = """You are a Dungeon Master's assistant for a tabletop RPG campaign.

You are given the current campaign state and a request of a specific KIND. Generate
content that is CONSISTENT with the established world, NPCs, and recent events, while
surprising the DM with a twist or complication. Do not contradict established lore.
If a RECENT ADVENTURE LOG is provided, treat it as the most current record of events and let it inform and ground your generation.

KIND meanings:
- encounter: a situation, challenge, or combat hook suited to the party level and location.
- loot: an item tied thematically to the enemy, location, or recent events - never generic gold.
- npc: a character, or their spoken response, with a clear voice and a hidden motive.
- description: read-aloud descriptive text for a place, object, or moment.

Scale any mechanics to the party level. Keep content concise enough to use at the table.

Return STRICT JSON only (no markdown, no prose) with EXACTLY these keys:
{
  "title": str,            // short, punchy
  "content": str,          // the main text the DM reads or paraphrases
  "mechanic": str,         // dice checks, DCs, stats if relevant; else ""
  "secret": str,           // something the DM knows but players don't; else ""
  "connects_to": str       // how this ties to an existing NPC or recent event; else ""
}
"""


def validate_generation(payload: dict) -> list:
    """Return a list of contract violations. Empty list means valid."""
    errors = []
    if not isinstance(payload, dict):
        return ["payload is not a dict"]

    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        errors.append(f"missing keys: {sorted(missing)}")

    for key in REQUIRED_KEYS:
        if key in payload and not isinstance(payload[key], str):
            errors.append(f"{key} must be a string")

    return errors
