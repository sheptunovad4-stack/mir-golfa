"""Read-only tournament and source API for the Golf CIS project."""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MOSCOW = ZoneInfo("Europe/Moscow")


def load_json(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        raise RuntimeError(f"{path} must contain a JSON array")
    return data


class Tournament(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    sport: str
    start_date: date
    end_date: date
    country: str
    location: str
    level: str
    source_url: HttpUrl
    winner: str | None = None
    score: str | None = None
    verified_at: datetime | None = None

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


def tournament_status(item: Tournament, today: date) -> str:
    if today < item.start_date:
        return "scheduled"
    if today > item.end_date:
        return "finished"
    return "live"


app = FastAPI(
    title="Мир Гольфа API",
    description="API календаря турниров и реестра источников. Турниры публикуются только из проверенного JSON.",
    version="1.0.0",
)

origins = [x.strip() for x in os.getenv(
    "GOLF_CIS_CORS_ORIGINS",
    "https://sheptunovad4-stack.github.io,http://localhost:3000,http://127.0.0.1:8000",
).split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "json-read-only", "timezone": "Europe/Moscow"}


@app.get("/api/v1/tournaments")
def list_tournaments(
    country: str | None = None,
    sport: str | None = None,
    region: str | None = None,
    on_date: date | None = Query(default=None, alias="date"),
):
    today = datetime.now(MOSCOW).date()
    rows = [Tournament.model_validate(x) for x in load_json("tournaments.json")]
    if country:
        rows = [x for x in rows if x.country.casefold() == country.casefold()]
    if sport:
        rows = [x for x in rows if x.sport.casefold() == sport.casefold()]
    if region:
        rows = [x for x in rows if region.casefold() in x.location.casefold()]
    if on_date:
        rows = [x for x in rows if x.start_date <= on_date <= x.end_date]
    return [{**x.model_dump(mode="json"), "status": tournament_status(x, today)} for x in rows]


@app.get("/api/v1/tournaments/{tournament_id}")
def get_tournament(tournament_id: str):
    today = datetime.now(MOSCOW).date()
    for raw in load_json("tournaments.json"):
        item = Tournament.model_validate(raw)
        if item.id == tournament_id:
            return {**item.model_dump(mode="json"), "status": tournament_status(item, today)}
    raise HTTPException(status_code=404, detail="Турнир не найден")


@app.get("/api/v1/sources")
def list_sources(country: str | None = None, enabled_only: bool = True):
    rows = load_json("sources.json")
    if enabled_only:
        rows = [x for x in rows if x.get("enabled", True)]
    if country:
        rows = [x for x in rows if x.get("country", "").casefold() == country.casefold()]
    return rows


@app.get("/api/v1/sources/{source_id}")
def get_source(source_id: str):
    for source in load_json("sources.json"):
        if source.get("id") == source_id:
            return source
    raise HTTPException(status_code=404, detail="Источник не найден")
