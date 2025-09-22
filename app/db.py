import os
import re
import joblib
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Any


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _preprocess_text(text: str | None) -> str:
    if text is None:
        return ""
    s = str(text).lower()
    s = re.sub(r"[^a-zA-Z0-9\s]", "", s)
    return " ".join(s.split())


class AIPredictRecord(BaseModel):
    little_interest_or_pleasure_in_doing_things: str
    feeling_down_depressed_or_hopeless: str
    trouble_falling_or_staying_asleep_or_rsleeping_too_much: str
    feeling_tired_or_having_little_energy: str
    poor_appetite_or_overeating: str
    Feeling_bad_about_yourself_or_that_you_are_a_failure_or_have_let_yourself_or_your_family_down: str
    Trouble_concentrating_on_things_such_as_reading_the_newspaper_or_watching_television: str
    Moving_or_speaking_so_slowly_that_other_people_could_have_noticed_Or_the_opposite_being_so_fidgety_or_restless_that_you_have_been_moving_around_a_lot_more_than_usual: str
    Thoughts_that_you_would_be_better_off_dead_or_thoughts_of_hurting_yourself_in_some_way: str


class _Predictor:
    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)

        try:
            self.model = joblib.load(self.model_dir / "best_model.pkl")
        except FileNotFoundError:
            self.model = joblib.load(self.model_dir / "random_forest_model.pkl")

        self.scaler = joblib.load(self.model_dir / "scaler.pkl")
        self.le = joblib.load(self.model_dir / "label_encoder.pkl")

        tfidf_path = self.model_dir / "tfidf_vectorizer.pkl"
        self.tfidf = joblib.load(tfidf_path) if tfidf_path.exists() else None

    def predict_df(self, payload: Any) -> pd.DataFrame:
        # Accept: list[AIPredictRecord], list[dict], dict, pd.DataFrame
        if isinstance(payload, pd.DataFrame):
            df = payload.copy()
        else:
            rows: list[dict] = []
            if isinstance(payload, dict):
                rows = [payload]
            elif isinstance(payload, list):
                for p in payload:
                    if hasattr(p, "model_dump"):
                        rows.append(p.model_dump())
                    elif isinstance(p, dict):
                        rows.append(p)
                    else:
                        raise TypeError(f"Unsupported payload item type: {type(p)}")
            else:
                raise TypeError(f"Unsupported payload type: {type(payload)}")
            df = pd.DataFrame(rows)

        if "negative_thoughts_text" in df.columns and "text" not in df.columns:
            df = df.rename(columns={"negative_thoughts_text": "text"})

        if self.tfidf is not None:
            text_cols = df.select_dtypes(include=["object"]).columns
            if len(text_cols) > 0:
                combined_text = []
                for idx in range(len(df)):
                    text_parts = []
                    for col in text_cols:
                        text_parts.append(_preprocess_text(df.iloc[idx][col]))
                    combined_text.append(" ".join(text_parts))

                tfidf_features = self.tfidf.transform(combined_text)
                feature_names = [f"tfidf_{i}" for i in range(tfidf_features.shape[1])]
                tfidf_df = pd.DataFrame(tfidf_features.toarray(), columns=feature_names, index=df.index)

                df = df.drop(columns=text_cols)
                df = pd.concat([df, tfidf_df], axis=1)
        else:
            cat_cols = df.select_dtypes(include=["object"]).columns
            for c in cat_cols:
                df[c] = pd.factorize(df[c])[0]

        df = df.apply(pd.to_numeric, errors="coerce").fillna(0)

        expected = None
        if hasattr(self.scaler, "feature_names_in_"):
            expected = list(self.scaler.feature_names_in_)
        elif hasattr(self.model, "feature_names_in_"):
            expected = list(self.model.feature_names_in_)

        if expected is not None:
            for col in expected:
                if col not in df.columns:
                    df[col] = 0
            df = df.reindex(columns=expected)

        X = self.scaler.transform(df)
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        predictions_decoded = self.le.inverse_transform(predictions)

        out = pd.DataFrame({"predicted_class_code": predictions, "predicted_class": predictions_decoded})

        for i, cls in enumerate(self.model.classes_):
            try:
                cls_name = self.le.inverse_transform([cls])[0]
            except Exception:
                cls_name = f"class_{cls}"
            out[f"probability_{cls_name}"] = probabilities[:, i]

        return out


if __name__ == "__main__":
    predictor = _Predictor("../model")
    payload = [
        AIPredictRecord(
            little_interest_or_pleasure_in_doing_things="Not at all",
            feeling_down_depressed_or_hopeless="Not at all",
            trouble_falling_or_staying_asleep_or_rsleeping_too_much="More than half the days",
            feeling_tired_or_having_little_energy="Several days",
            poor_appetite_or_overeating="More than half the days",
            Feeling_bad_about_yourself_or_that_you_are_a_failure_or_have_let_yourself_or_your_family_down="More than half the days",
            Trouble_concentrating_on_things_such_as_reading_the_newspaper_or_watching_television="Several days",
            Moving_or_speaking_so_slowly_that_other_people_could_have_noticed_Or_the_opposite_being_so_fidgety_or_restless_that_you_have_been_moving_around_a_lot_more_than_usual="Nearly every day",
            Thoughts_that_you_would_be_better_off_dead_or_thoughts_of_hurting_yourself_in_some_way="More than half the days"
        )
    ]
    out = predictor.predict_df(payload)
    print(out.to_dict(orient="records"))
