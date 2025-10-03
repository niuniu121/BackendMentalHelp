from fastapi import APIRouter
import sqlite3
import pandas as pd

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

DB_PATH = "app.db"

@router.get("/sleep_distribution")
def sleep_distribution():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT ROUND(sleep_hours) as sleep_bucket, COUNT(*) as count
        FROM student_wide
        WHERE sleep_hours IS NOT NULL
        GROUP BY ROUND(sleep_hours)
        ORDER BY sleep_bucket
    """, conn)
    return df.to_dict(orient="records")

@router.get("/stress_distribution")
def stress_distribution():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT stress_level, COUNT(*) as count
        FROM student_wide
        WHERE stress_level IS NOT NULL
        GROUP BY stress_level
        ORDER BY stress_level
    """, conn)
    return df.to_dict(orient="records")

@router.get("/diet_vs_happiness")
def diet_vs_happiness():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT diet_type, AVG(happiness_score) as avg_happiness, COUNT(*) as n
        FROM student_wide
        WHERE diet_type IS NOT NULL AND happiness_score IS NOT NULL
        GROUP BY diet_type
        HAVING n >= 10
    """, conn)
    return df.to_dict(orient="records")

@router.get("/screen_vs_stress")
def screen_vs_stress():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT ROUND(screen_time) as screen_bucket, AVG(stress_level) as avg_stress, COUNT(*) as n
        FROM student_wide
        WHERE screen_time IS NOT NULL AND stress_level IS NOT NULL
        GROUP BY ROUND(screen_time)
        HAVING n >= 10
        ORDER BY screen_bucket
    """, conn)
    return df.to_dict(orient="records")
