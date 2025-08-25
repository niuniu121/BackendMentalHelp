from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import httpx

from .db import SessionLocal, engine, Base
from .models import FlipCard, Tip
from .speech import router as speech_router

app = FastAPI(title="Brain Health API", version="1.0.0")

# Optional speech router (you can keep it mounted)
app.include_router(speech_router)

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# CORS (dev only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# Flip cards
@app.get("/api/flip-cards")
def get_flip_cards(
    limit: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = db.query(FlipCard).order_by(func.random()).limit(limit).all()
    return [
        {
            "id": r.id,
            "negative_text": r.negative_text,
            "positive_text": r.positive_text,
            "tag": r.tag,
        }
        for r in rows
    ]

# Tips (DB)
@app.get("/api/tips/random")
def random_tip(mood: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Tip)
    if mood:
        q = q.filter(Tip.mood_tag == mood)
    row = q.order_by(func.random()).first() or db.query(Tip).order_by(func.random()).first()
    if not row:
        raise HTTPException(status_code=404, detail="No tips seeded")
    return {"id": row.id, "text": row.text, "mood": row.mood_tag}

# Simple cache
_TTL_SECONDS = 600
_cache: dict[str, tuple[dict, datetime]] = {}

def _cache_get(key: str):
    hit = _cache.get(key)
    if not hit:
        return None
    data, exp = hit
    if datetime.utcnow() > exp:
        _cache.pop(key, None)
        return None
    return data

def _cache_set(key: str, data: dict):
    _cache[key] = (data, datetime.utcnow() + timedelta(seconds=_TTL_SECONDS))

# Base Open-Meteo proxy (kept for backward compatibility)
@app.get("/api/open-meteo")
async def open_meteo(lat: float = Query(...), lon: float = Query(...)):
    key = f"meteo:{round(lat,2)},{round(lon,2)}"
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", "data": cached}

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code"
        "&timezone=auto"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    _cache_set(key, data)
    return {"source": "live", "data": data}

# NEW: Air quality (PM2.5/UV etc.)
@app.get("/api/air-quality")
async def air_quality(lat: float = Query(...), lon: float = Query(...)):
    key = f"aq:{round(lat,2)},{round(lon,2)}"
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", "data": cached}

    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=pm2_5,pm10,uv_index,uv_index_clear_sky,ozone&timezone=auto"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    _cache_set(key, data)
    return {"source": "live", "data": data}

# NEW: Daylight (sunrise/sunset)
@app.get("/api/daylight")
async def daylight(lat: float = Query(...), lon: float = Query(...)):
    key = f"dl:{round(lat,2)},{round(lon,2)}"
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", "data": cached}

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=sunrise,sunset&timezone=auto"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    _cache_set(key, data)
    return {"source": "live", "data": data}

@app.get("/api/db-stats")
def db_stats(db: Session = Depends(get_db)):
    return {
        "flip_card": db.query(FlipCard).count(),
        "tip": db.query(Tip).count(),
    }
