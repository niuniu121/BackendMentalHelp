import os
import re
import joblib
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========= AI Predict: text preprocess & predictor =========
def _preprocess_text(text: str | None) -> str:
    if text is None:
        return ""
    s = str(text).lower()
    s = re.sub(r"[^a-zA-Z0-9\s]", "", s)
    return " ".join(s.split())


class _Predictor:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.model = joblib.load(Path(model_dir) / "random_forest_model.pkl")
        self.scaler = joblib.load(Path(model_dir) / "scaler.pkl")
        # optional
        le_path = Path(model_dir) / "label_encoder.pkl"
        tfidf_path = Path(model_dir) / "tfidf_vectorizer.pkl"
        self.le = joblib.load(le_path) if le_path.exists() else None
        self.tfidf = joblib.load(tfidf_path) if tfidf_path.exists() else None

    def predict_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Steps:
          1) If TF-IDF is available: merge all object columns -> TF-IDF features.
             Else factorize object columns.
          2) Auto-align columns to training-time feature names (order + fill missing).
          3) Scale -> predict -> probabilities -> friendly output.
        """

        # --- 1) text handling ---
        if self.tfidf is not None:
            text_cols = df.select_dtypes(include=["object"]).columns
            if len(text_cols) > 0:
                combined = [
                    " ".join(_preprocess_text(df.iloc[i][c]) for c in text_cols)
                    for i in range(len(df))
                ]
                X_text = self.tfidf.transform(combined).toarray()
                tf_cols = [f"tfidf_{i}" for i in range(X_text.shape[1])]
                df = df.drop(columns=text_cols)
                df = pd.concat(
                    [df.reset_index(drop=True),
                     pd.DataFrame(X_text, columns=tf_cols, index=df.index)],
                    axis=1
                )
        else:
            # simple encode for any remaining object columns
            cat_cols = df.select_dtypes(include=["object"]).columns
            for c in cat_cols:
                df[c] = pd.factorize(df[c])[0]

        df = df.apply(pd.to_numeric, errors="coerce")
        # NaN 兜底
        df = df.fillna(0)

        # --- 2) auto align with training feature names ---
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

        # --- 3) scale & predict ---
        X = self.scaler.transform(df)
        y = self.model.predict(X)
        proba = self.model.predict_proba(X)

        # decode label if encoder exists
        if self.le is not None:
            try:
                y_label = self.le.inverse_transform(y)
            except Exception:
                y_label = y
        else:
            y_label = y

        out = pd.DataFrame({"predicted_class_code": y, "predicted_class": y_label})
        for i, cls in enumerate(self.model.classes_):
            if self.le is not None:
                try:
                    cls_name = self.le.inverse_transform([cls])[0]
                except Exception:
                    cls_name = f"class_{cls}"
            else:
                cls_name = f"class_{cls}"
            out[f"probability_{cls_name}"] = proba[:, i]
        return out
