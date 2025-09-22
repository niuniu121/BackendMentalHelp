# BackendMentalHelp/app/main.py
from fastapi import FastAPI, Depends, Query, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import os
import httpx
from urllib.parse import urlencode

from .db import SessionLocal, engine, Base, _Predictor
from .models import FlipCard, Tip, HealthImpact
from sqlalchemy import or_
from .routes_search import router as search_router

from typing import List
import pandas as pd
from pathlib import Path


app = FastAPI(title="Brain Health API", version="1.0.0")

# ========== Speech 模块可选 ==========
ENABLE_SPEECH = os.getenv("ENABLE_SPEECH", "0") == "1"
if ENABLE_SPEECH:
    try:
        from .speech import router as speech_router
        app.include_router(speech_router)
    except Exception as e:
        print(f"Speech router disabled: {e}")

Base.metadata.create_all(bind=engine)

# ========== CORS ==========
origins = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins.split(",")] if origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== DB session dependency ==========
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== Health check ==========
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# ========== Flip Cards ==========
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

# ========== Tips ==========
@app.get("/api/tips/random")
def random_tip(mood: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Tip)
    if mood:
        q = q.filter(Tip.mood_tag == mood)
    row = q.order_by(func.random()).first() or db.query(Tip).order_by(func.random()).first()
    if not row:
        raise HTTPException(status_code=404, detail="No tips seeded")
    return {"id": row.id, "text": row.text, "mood": row.mood_tag}

# ========== Cache for external APIs ==========
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

def _httpx_client():
    return httpx.AsyncClient(timeout=10.0)

def _cache_key(prefix: str, base_url: str, params: dict) -> str:
    return f"{prefix}:{base_url}?{urlencode(sorted(params.items()))}"

def _raise_as_http(e: httpx.HTTPStatusError):
    detail = {"status": e.response.status_code, "url": str(e.request.url)}
    try:
        detail["body"] = e.response.json()
    except Exception:
        detail["body"] = e.response.text
    raise HTTPException(status_code=e.response.status_code, detail=detail)

# ========== External APIs ==========
@app.get("/api/open-meteo")
async def open_meteo(lat: float = Query(...), lon: float = Query(...)):
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "hourly": "uv_index,uv_index_clear_sky,is_day",
        "timezone": "auto",
    }
    key = _cache_key("meteo", base, params)
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", "data": cached, "current": cached.get("current", {}), "hourly": cached.get("hourly", {})}

    async with _httpx_client() as client:
        try:
            r = await client.get(base, params=params)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            _raise_as_http(e)
        data = r.json()

    _cache_set(key, data)
    return {"source": "live", "data": data, "current": data.get("current", {}), "hourly": data.get("hourly", {})}

@app.get("/api/air-quality")
async def air_quality(lat: float = Query(...), lon: float = Query(...)):
    base = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {"latitude": lat, "longitude": lon, "hourly": "pm2_5,pm10,ozone", "timezone": "auto"}
    key = _cache_key("aq", base, params)
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", "data": cached, "hourly": cached.get("hourly", {})}

    async with _httpx_client() as client:
        try:
            r = await client.get(base, params=params)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            _raise_as_http(e)
        data = r.json()

    _cache_set(key, data)
    return {"source": "live", "data": data, "hourly": data.get("hourly", {})}

@app.get("/api/daylight")
async def daylight(lat: float = Query(...), lon: float = Query(...)):
    base = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "daily": "sunrise,sunset", "timezone": "auto"}
    key = _cache_key("dl", base, params)
    cached = _cache_get(key)
    if cached:
        return {"source": "cache", "data": cached, "daily": cached.get("daily", {})}

    async with _httpx_client() as client:
        try:
            r = await client.get(base, params=params)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            _raise_as_http(e)
        data = r.json()

    _cache_set(key, data)
    return {"source": "live", "data": data, "daily": data.get("daily", {})}

# ========== DB Stats ==========
@app.get("/api/db-stats")
def db_stats(db: Session = Depends(get_db)):
    return {"flip_card": db.query(FlipCard).count(), "tip": db.query(Tip).count()}

# ========== AI Model ==========
@app.on_event("startup")
def _load_predictor():
    default_dir = str((Path(__file__).resolve().parents[1] / "model"))
    model_dir = os.getenv("AI_MODEL_DIR", default_dir)
    try:
        app.state.predictor = _Predictor(model_dir)
        print(f"[AI] Predictor loaded from {model_dir}")
    except Exception as e:
        app.state.predictor = None
        print(f"[AI] Predictor failed to load: {e}")

# ========== AI Endpoints ==========
@app.post("/api/ai/predict-json")
def ai_predict_json(payload: List[dict]):
    """前端直接传 list[dict]（PHQ-9 的 9 个问题），这里放宽兼容"""
    pred = getattr(app.state, "predictor", None)
    if pred is None:
        raise HTTPException(status_code=500, detail="Predictor not loaded")

    try:
        df = pd.DataFrame(payload)
        res = pred.predict_df(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"prediction failed: {e}")

    return {"rows": res.to_dict(orient="records"), "count": len(res)}

@app.post("/api/ai/predict-xlsx")
async def ai_predict_xlsx(file: UploadFile = File(...)):
    pred = getattr(app.state, "predictor", None)
    if pred is None:
        raise HTTPException(status_code=500, detail="Predictor not loaded")

    content = await file.read()
    try:
        df = pd.read_excel(io=content)
        res = pred.predict_df(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"read/predict failed: {e}")

    return {"rows": res.to_dict(orient="records"), "count": len(res)}

# ========== Search Router ==========
app.include_router(search_router, prefix="/api")
