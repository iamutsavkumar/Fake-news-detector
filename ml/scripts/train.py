#!/usr/bin/env python3
"""
FINAL training pipeline for fake news detection
"""

import argparse
import logging
import re
from pathlib import Path

import joblib
import pandas as pd
from tqdm import tqdm

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

# ── Logging ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

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
    fake_df["label"] = 0  # FAKE

    logger.info("Loading True.csv …")
    true_df = pd.read_csv(true_path)
    true_df["label"] = 1  # REAL

    df = pd.concat([fake_df, true_df], ignore_index=True)

    df["title"] = df["title"].fillna("")
    df["text"] = df["text"].fillna("")
    df["content"] = df["title"] + " " + df["text"]

    logger.info("Total samples: %d", len(df))
    return df[["content", "label"]]


# ── Preprocessing ───────────────────────────────────────

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


# ── FIXED: Balanced Dataset ─────────────────────────────

def balance_dataset(df: pd.DataFrame) -> pd.DataFrame:
    fake = df[df["label"] == 0]
    real = df[df["label"] == 1]

    # 🔥 Safe balancing using minimum class size
    min_size = min(len(fake), len(real))

    fake_balanced = resample(
        fake,
        replace=False,
        n_samples=min_size,
        random_state=RANDOM_STATE
    )

    real_balanced = resample(
        real,
        replace=False,
        n_samples=min_size,
        random_state=RANDOM_STATE
    )

    df_balanced = pd.concat([fake_balanced, real_balanced])
    df_balanced = df_balanced.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    logger.info("Balanced dataset: %d samples", len(df_balanced))
    return df_balanced


# ── Model Pipeline ──────────────────────────────────────

def build_pipeline() -> Pipeline:
    vectorizer = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
        stop_words="english"
    )

    classifier = SGDClassifier(
        loss="log_loss",
        max_iter=1000,
        class_weight="balanced",
        random_state=RANDOM_STATE
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

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE
    )

    logger.info("Training model…")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

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
    df = balance_dataset(df)  # ✅ FIXED VERSION

    pipeline = train(df)
    save_model(pipeline, args.output_dir)

    logger.info("Training complete ✓")


if __name__ == "__main__":
    main()