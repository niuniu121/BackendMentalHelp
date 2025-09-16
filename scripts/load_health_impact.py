# scripts/load_health_impact.py
import pandas as pd
from pathlib import Path
import sys, argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from BackendMentalHelp.app.db import SessionLocal, engine
from BackendMentalHelp.app.models import HealthImpact, Base

Base.metadata.create_all(bind=engine)

COL_MAP = {
    "Useful features": "useful_features",
    "Health Risks": "health_risks",
    "Beneficial subject": "beneficial_subject",
    "Usage symptoms": "usage_symptoms",
    "Symptom frequency": "symptom_frequency",
    "Health precautions": "health_precaution",
}

def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)  # 默认 CSV
    return df

def run(file_path: Path):
    df = read_table(file_path).fillna("")
    df = df.rename(columns=COL_MAP)
    keep = list(COL_MAP.values())
    df = df[keep]

    session = SessionLocal()
    try:
        session.query(HealthImpact).delete()
        objs = [HealthImpact(**row._asdict()) for row in df.itertuples(index=False)]
        session.add_all(objs)
        session.commit()
        print(f"Inserted {len(objs)} rows from {file_path}.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", "-f", required=False,
                    default=str((ROOT / "impact_mobile_phone_health.csv").resolve()),
                    help="Path to CSV/XLSX exported from Numbers")
    args = ap.parse_args()
    run(Path(args.file))
