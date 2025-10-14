from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/api/visuals", tags=["visuals"])

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

@router.get("/coping_summary")
def get_coping_summary():
    file_path = DATA_DIR / "coping_group_summary.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")

    required_cols = {"coping_strategy_group", "n", "rank"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid columns in CSV. Found: {df.columns.tolist()}, Required: {sorted(required_cols)}",
        )

    df = df.sort_values("rank")
    return df.to_dict(orient="records")


@router.get("/lifetime_disorder")
def get_lifetime_disorder():
    file_path = DATA_DIR / "Lifetime_Disorder_Summary.xlsx"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read Excel: {e}")

    required_cols = {"State/Territory", "Lifetime Disorder Proportion (%)"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid columns in Excel. Found: {df.columns.tolist()}, Required: {sorted(required_cols)}",
        )

    df = df.dropna(subset=["State/Territory"])
    df = df.sort_values("Lifetime Disorder Proportion (%)", ascending=False)
    return df.to_dict(orient="records")
