from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    anthropic_api_key: str = ""
    agent_model: str = "claude-sonnet-4-6"
    classifier_model: str = "claude-haiku-4-5"

    database_url: str = f"sqlite:///{BACKEND_DIR / 'support_agent.db'}"
    chroma_dir: str = str(BACKEND_DIR / "chroma_data")
    knowledge_base_dir: str = str(BACKEND_DIR / "knowledge_base")

    retrieval_confidence_threshold: float = 0.35
    retrieval_top_k: int = 4

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
