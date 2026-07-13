"""
Centralized application configuration.
Loaded once via the `get_settings()` cached singleton and imported everywhere
else in the app — never read os.environ directly outside this module.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # --- LLM Keys ---
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    # --- Search Keys ---
    tavily_api_key: str = Field(default="")
    serper_api_key: str = Field(default="")

    # --- Model routing per agent ---
    designer_model_provider: Literal["openai", "anthropic", "groq"] = "openai"
    designer_model_name: str = "gpt-4o"

    analyst_model_provider: Literal["openai", "anthropic", "groq"] = "anthropic"
    analyst_model_name: str = "claude-3-5-sonnet-20241022"

    researcher_model_provider: Literal["openai", "anthropic", "groq"] = "groq"
    researcher_model_name: str = "llama-3.1-70b-versatile"

    # --- Pipeline limits ---
    max_research_sources: int = 8
    max_slides: int = 12
    output_dir: str = "/tmp/generated_decks"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def output_path(self) -> Path:
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-parsing .env on every import."""
    return Settings()
