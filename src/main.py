from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src import database, ai_service
from src.prompts import KINDS

import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(lifespan=lifespan)


# ---------- request bodies ----------

class CampaignCreate(BaseModel):
    name: str
    system: str | None = None
    setting: str | None = None
    tone: str | None = None
    party_level: int | None = None
    current_location: str | None = None
    recent_events: str | None = None
    known_npcs: str | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    system: str | None = None
    setting: str | None = None
    tone: str | None = None
    party_level: int | None = None
    current_location: str | None = None
    recent_events: str | None = None
    known_npcs: str | None = None


class GenerateRequest(BaseModel):
    campaign_id: int
    kind: str
    dm_input: str = ""


class NoteRequest(BaseModel):
    campaign_id: int
    content: str


class SaveRequest(BaseModel):
    campaign_id: int
    kind: str
    dm_input: str = ""
    title: str = ""
    content: str = ""
    mechanic: str = ""
    secret: str = ""
    connects_to: str = ""


# ---------- helpers ----------

def _require_campaign(campaign_id: int) -> dict:
    campaign = database.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return campaign


# ---------- routes ----------

@app.get("/api/campaigns")
def get_campaigns():
    return database.list_campaigns()


@app.post("/api/campaigns")
def post_campaigns(body: CampaignCreate):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    return database.create_campaign(body.model_dump(exclude_none=True))


@app.get("/api/campaign/{campaign_id}")
def get_campaign(campaign_id: int):
    return _require_campaign(campaign_id)


@app.put("/api/campaign/{campaign_id}")
def put_campaign(campaign_id: int, body: CampaignUpdate):
    _require_campaign(campaign_id)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return database.update_campaign(campaign_id, fields)


@app.post("/api/generate")
def post_generate(body: GenerateRequest):
    if body.kind not in KINDS:
        raise HTTPException(status_code=400, detail=f"Invalid kind {body.kind!r}. Must be one of {sorted(KINDS)}")
    campaign = _require_campaign(body.campaign_id)
    recent_log = database.get_log(body.campaign_id)
    return ai_service.generate(campaign, body.kind, body.dm_input, recent_log=recent_log)


@app.post("/api/note")
def post_note(body: NoteRequest):
    _require_campaign(body.campaign_id)
    database.save_note(body.campaign_id, body.content)
    return database.get_log(body.campaign_id)


@app.post("/api/save")
def post_save(body: SaveRequest):
    _require_campaign(body.campaign_id)
    return database.save_generation(body.model_dump())


@app.get("/api/campaign/{campaign_id}/log")
def get_log(campaign_id: int):
    _require_campaign(campaign_id)
    return database.get_log(campaign_id)


# ---------- static files (last, catches "/") ----------

_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
