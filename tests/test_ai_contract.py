"""Contract tests for dnd_gm_assist.

Validator tests run immediately (pure functions, no network). The end-to-end test
activates once src/ai_service.py exists; it mocks the model call so no real request
is made.

Run:  pytest -q
"""
import pytest
from src.prompts import validate_generation

VALID = {
    "title": "The Drowned Lantern",
    "content": "A rusted lantern bobs among the reeds, its flame still burning beneath the water.",
    "mechanic": "DC 14 Investigation to notice the flame casts no reflection.",
    "secret": "It marks where Bryn drowned a courier carrying the key's true name.",
    "connects_to": "Same cult sigil as the obsidian key is etched on the lantern's base.",
}


def test_valid_payload_passes():
    assert validate_generation(VALID) == []


def test_missing_key_fails():
    bad = {k: v for k, v in VALID.items() if k != "content"}
    assert any("missing" in e for e in validate_generation(bad))


def test_fields_must_be_strings():
    assert any("title" in e for e in validate_generation({**VALID, "title": 7}))


def test_optional_fields_may_be_empty():
    assert validate_generation({**VALID, "mechanic": "", "secret": "", "connects_to": ""}) == []


def test_generate_returns_valid_contract(monkeypatch):
    """ai_service.generate() must produce a payload that passes the contract.

    Convention (see CLAUDE.md): ai_service exposes _call_model(system, user) -> str,
    patched here so no real API call is made.
    """
    ai_service = pytest.importorskip("src.ai_service")

    fake_json = '{"title":"x","content":"y","mechanic":"","secret":"","connects_to":""}'
    monkeypatch.setattr(ai_service, "_call_model", lambda system, user: fake_json, raising=False)

    campaign = {
        "name": "The Obsidian Key", "party_level": 5, "current_location": "The Whispering Swamps",
        "tone": "dark & gritty", "recent_events": "Defeated the swamp-witch.", "known_npcs": "Bryn",
    }
    out = ai_service.generate(campaign, kind="loot", dm_input="party opens the witch's chest")
    assert validate_generation(out) == []
