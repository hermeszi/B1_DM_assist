import json
import os
import re

import httpx
from dotenv import load_dotenv

from src.prompts import KINDS, REQUIRED_KEYS, SYSTEM_PROMPT, validate_generation

load_dotenv()

_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _call_model(system: str, user: str) -> str:
    api_key = os.environ["OPENROUTER_API_KEY"]
    model = os.environ.get("MODEL", "openai/gpt-4o-mini")
    response = httpx.post(
        _API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)


def _build_user_message(campaign: dict, kind: str, dm_input: str) -> str:
    lines = [
        f"CAMPAIGN: {campaign.get('name', '')}",
        f"System: {campaign.get('system', '')}",
        f"Setting: {campaign.get('setting', '')}",
        f"Tone: {campaign.get('tone', '')}",
        f"Party level: {campaign.get('party_level', '')}",
        f"Current location: {campaign.get('current_location', '')}",
        f"Recent events: {campaign.get('recent_events', '')}",
        f"Known NPCs: {campaign.get('known_npcs', '')}",
        "",
        f"KIND: {kind}",
        f"DM input: {dm_input}",
    ]
    return "\n".join(lines)


def _build_log_block(recent_log: list[dict]) -> str:
    lines = ["", "RECENT ADVENTURE LOG (newest first):"]
    total = 0
    for entry in recent_log[:8]:
        if entry.get("source") == "dm":
            line = f"[DM note] {entry.get('content', '')}"
        else:
            line = f"[{entry.get('kind', '')}] {entry.get('title', '')}: {entry.get('content', '')}"
        if total + len(line) > 3000:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


def generate(campaign: dict, kind: str, dm_input: str, recent_log: list[dict] | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"Unknown kind {kind!r}. Must be one of {sorted(KINDS)}.")

    user_msg = _build_user_message(campaign, kind, dm_input)
    if recent_log:
        user_msg += _build_log_block(recent_log)

    raw = _strip_fences(_call_model(SYSTEM_PROMPT, user_msg))
    payload = json.loads(raw)
    errors = validate_generation(payload)

    if errors:
        correction = (
            f"Your previous response had these contract violations: {errors}. "
            f"Return STRICT JSON with exactly these keys and string values: "
            f"{sorted(REQUIRED_KEYS)}. No markdown fences."
        )
        raw2 = _strip_fences(_call_model(SYSTEM_PROMPT, user_msg + "\n\n" + correction))
        payload = json.loads(raw2)
        errors2 = validate_generation(payload)
        if errors2:
            raise ValueError(f"Model failed contract after retry: {errors2}")

    return payload
