#!/usr/bin/env python3
"""
ml/scripts/train.py
====================
End-to-end training pipeline for the fake news classifier.

Dataset
-------
Uses the Kaggle "Fake and Real News Dataset":
  https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset

Files expected in ml/data/:
  - Fake.csv  (23,481 rows)
  - True.csv  (21,417 rows)

Download instructions:
  1. Install kaggle CLI:  pip install kaggle
  2. Place your API key at ~/.kaggle/kaggle.json
  3. Run:
     kaggle datasets download -d clmentbisaillon/fake-and-real-news-dataset -p ml/data --unzip

Alternatively, download manually from the URL above and unzip into ml/data/.

Pipeline
--------
  1. Load + label data
  2. Preprocess (clean, lemmatize)
  3. TF-IDF feature extraction
  4. Train Logistic Regression (L2) — fast, accurate baseline
  5. Evaluate with full classification report + confusion matrix
  6. Serialise model artefacts to backend/models/

Usage
-----
  cd fakenews/
  python ml/scripts/train.py [--data-dir ml/data] [--output-dir backend/models]
"""

#!/usr/bin/env python3

import argparse
import logging
import sys
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tqdm import tqdm

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline

# ── Logging ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────

RANDOM_STATE = 42
TEST_SIZE = 0.2


# ── Load Dataset ────────────────────────────────────────

def load_dataset(data_dir: Path) -> pd.DataFrame:
    fake_path = data_dir / "Fake.csv"
    true_path = data_dir / "True.csv"

    if not fake_path.exists() or not true_path.exists():
        raise FileNotFoundError(f"Dataset not found in {data_dir}")

    logger.info("Loading Fake.csv …")
    fake_df = pd.read_csv(fake_path)
    fake_df["label"] = "FAKE"

    logger.info("Loading True.csv …")
    true_df = pd.read_csv(true_path)
    true_df["label"] = "REAL"

    df = pd.concat([fake_df, true_df], ignore_index=True)

    df["title"] = df["title"].fillna("")
    df["text"] = df["text"].fillna("")
    df["content"] = df["title"] + " " + df["text"]

    logger.info("Total samples: %d", len(df))
    return df[["content", "label"]]


# ── Preprocessing (Improved for real-world) ─────────────

def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preprocessing text…")

    tqdm.pandas(desc="Cleaning")
    df["content"] = df["content"].progress_apply(clean_text)

    df = df[df["content"].str.len() > 20].reset_index(drop=True)
    logger.info("After preprocessing: %d samples", len(df))

    return df


# ── Model Pipeline ──────────────────────────────────────

def build_pipeline() -> Pipeline:
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.9,
        stop_words="english",
        sublinear_tf=True,
    )

    classifier = LogisticRegression(
        C=1.0,
        max_iter=2000,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )

    return Pipeline([
        ("tfidf", vectorizer),
        ("clf", classifier),
    ])


# ── Training ────────────────────────────────────────────

def train(df: pd.DataFrame) -> Pipeline:
    X = df["content"].values
    y = df["label"].values

    pipeline = build_pipeline()

    # 🔥 Cross-validation (REAL accuracy)
    logger.info("Running cross-validation…")
    scores = cross_val_score(pipeline, X, y, cv=5, n_jobs=-1)

    logger.info("Cross-val accuracy: %.4f ± %.4f", scores.mean(), scores.std())

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE
    )

    logger.info("Training final model…")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, pos_label="FAKE")

    logger.info("=" * 50)
    logger.info("FINAL RESULTS")
    logger.info("=" * 50)
    logger.info("Accuracy : %.4f", acc)
    logger.info("F1 Score : %.4f", f1)
    logger.info("\n%s", classification_report(y_test, y_pred))

    return pipeline


# ── Save Model ──────────────────────────────────────────

def save_model(pipeline: Pipeline, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "fake_news_model.joblib"
    vectorizer_path = output_dir / "tfidf_vectorizer.joblib"

    joblib.dump(pipeline.named_steps["clf"], model_path)
    joblib.dump(pipeline.named_steps["tfidf"], vectorizer_path)

    logger.info("Saved model → %s", model_path)
    logger.info("Saved vectorizer → %s", vectorizer_path)


# ── CLI ────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="ml/data", type=Path)
    parser.add_argument("--output-dir", default="backend/models", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()

    df = load_dataset(args.data_dir)
    df = preprocess(df)
    pipeline = train(df)
    save_model(pipeline, args.output_dir)

    logger.info("Training complete ✓")


if __name__ == "__main__":
    main()