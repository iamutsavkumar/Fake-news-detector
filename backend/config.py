from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # CORS — comma-separated list in .env
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Paths relative to this file's directory (backend/)
    base_dir: Path = Path(__file__).parent
    model_path: Path = Path("models/fake_news_model.joblib")
    vectorizer_path: Path = Path("models/tfidf_vectorizer.joblib")

    scrape_timeout: int = 10  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def abs_model_path(self) -> Path:
        return self.base_dir / self.model_path

    @property
    def abs_vectorizer_path(self) -> Path:
        return self.base_dir / self.vectorizer_path


@lru_cache
def get_settings() -> Settings:
    return Settings()
