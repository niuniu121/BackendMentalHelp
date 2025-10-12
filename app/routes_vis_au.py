# app/routes_visuals.py
from fastapi import APIRouter, HTTPException
import pandas as pd
import os

router = APIRouter(prefix="/api/visuals", tags=["visuals"])


@router.get("/coping_summary")
def get_coping_summary():
    file_path = "/Users/danzhou/Downloads/5120dataset/coping_group_summary.csv"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    df = pd.read_csv(file_path)

    # Validate column names
    required_cols = {"coping_strategy_group", "n", "rank"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"Invalid columns in CSV: {df.columns.tolist()}")

    df = df.sort_values("rank")
    return df.to_dict(orient="records")


@router.get("/lifetime_disorder")
def get_lifetime_disorder():
    file_path = "/Users/danzhou/Downloads/5120dataset/Lifetime_Disorder_Summary.xlsx"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    df = pd.read_excel(file_path)

    required_cols = {"State/Territory", "Lifetime Disorder Proportion (%)"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"Invalid columns in Excel: {df.columns.tolist()}")

    df = df.dropna(subset=["State/Territory"])
    df = df.sort_values("Lifetime Disorder Proportion (%)", ascending=False)

    return df.to_dict(orient="records")
