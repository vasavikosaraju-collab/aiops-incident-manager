"""
train_model.py

Trains a ticket-routing classifier that predicts which support team
should handle an incoming IT ticket, based on its free-text
description.

Pipeline:
    TF-IDF Vectorizer -> Random Forest Classifier

Why this pipeline:
- TF-IDF is a simple, fast, interpretable way to turn short ticket
  descriptions into numeric features. It works well for small/medium
  datasets without needing GPU resources or embeddings.
- Random Forest is robust to noisy/sparse TF-IDF features, doesn't
  require feature scaling, gives feature importances for
  explainability, and trains quickly even on a laptop.
- This is intentionally a "good enough, explainable" baseline rather
  than a large language model. The README discusses how this could
  be swapped for a transformer-based classifier or an LLM-based
  router as a future improvement.

Usage:
    python train_model.py
"""

import json
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score


DATA_PATH = "ticket_dataset.csv"
MODEL_OUT = "../backend/ml_router/trained_model/ticket_router.pkl"
METRICS_OUT = "../backend/ml_router/trained_model/metrics.json"


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} labeled tickets")
    print(df["team"].value_counts())

    X = df["description"]
    y = df["team"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=2000,
        )),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    print(f"\nTest accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred))

    joblib.dump(pipeline, MODEL_OUT)
    print(f"\nSaved trained pipeline to {MODEL_OUT}")

    with open(METRICS_OUT, "w") as f:
        json.dump({
            "accuracy": accuracy,
            "n_train": len(X_train),
            "n_test": len(X_test),
            "classes": sorted(y.unique().tolist()),
            "classification_report": report,
        }, f, indent=2)
    print(f"Saved metrics to {METRICS_OUT}")


if __name__ == "__main__":
    main()
