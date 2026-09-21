import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str]
    database_url: str
    tavily_api_key: str | None


def _parse_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


settings = Settings(
    cors_origins=_parse_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000")
    ),
    database_url=os.getenv("DATABASE_URL", ""),
    tavily_api_key=os.getenv("TAVILY_API_KEY"),
)

if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL must be set to a PostgreSQL connection string before starting the backend."
    )

if not settings.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
    raise RuntimeError("DATABASE_URL must use PostgreSQL (postgresql+psycopg://...).")
