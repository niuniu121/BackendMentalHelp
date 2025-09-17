# BackendMentalHelp/app/routes_search.py
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import select, func, or_, MetaData, Table
from sqlalchemy.orm import Session
from .db import engine, SessionLocal
from .models import HealthImpact  # ORM 模型

router = APIRouter()

# ---- DB session dependency（独立于 main.py，避免循环依赖）----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== 方案 A：ORM 版（你的字段精确匹配，返回结构不变）=====
@router.get("/search-disease")
def search_disease(
    q: str = Query(..., min_length=1, description="The search keyword"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    like = f"%{q}%"
    base_filter = or_(
        func.lower(HealthImpact.useful_features).like(func.lower(like)),
        func.lower(HealthImpact.health_risks).like(func.lower(like)),
        func.lower(HealthImpact.beneficial_subject).like(func.lower(like)),
        func.lower(HealthImpact.usage_symptoms).like(func.lower(like)),
        func.lower(HealthImpact.symptom_frequency).like(func.lower(like)),
        func.lower(HealthImpact.health_precaution).like(func.lower(like)),
    )

    total = db.query(HealthImpact).filter(base_filter).count()
    rows = (
        db.query(HealthImpact)
        .filter(base_filter)
        .order_by(HealthImpact.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items = [
        {
            "id": r.id,
            "useful_features": r.useful_features,
            "health_risks": r.health_risks,
            "beneficial_subject": r.beneficial_subject,
            "usage_symptoms": r.usage_symptoms,
            "symptom_frequency": r.symptom_frequency,
            "health_precaution": r.health_precaution,
        }
        for r in rows
    ]

    return {
        "q": q,
        "limit": limit,
        "offset": offset,
        "total": total,
        "count": len(items),
        "items": items,
    }

