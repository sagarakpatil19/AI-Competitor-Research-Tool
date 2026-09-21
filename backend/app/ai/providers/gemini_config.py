import os
from dataclasses import dataclass, field

from app.ai.errors import ProviderUnavailableError


DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


@dataclass(frozen=True, repr=False)
class GeminiProviderConfig:
    """Environment-backed configuration for a future Gemini provider."""

    api_key: str | None = field(default=None, repr=False)
    model_name: str = DEFAULT_GEMINI_MODEL

    @classmethod
    def from_env(cls) -> "GeminiProviderConfig":
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key is not None:
            api_key = api_key.strip() or None
        model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        return cls(api_key=api_key, model_name=model_name or DEFAULT_GEMINI_MODEL)

    def require_api_key(self) -> str:
        if not self.api_key:
            raise ProviderUnavailableError(
                "Gemini API key is not configured; set GEMINI_API_KEY before creating a real provider."
            )
        return self.api_key

    def __repr__(self) -> str:
        return f"GeminiProviderConfig(model_name={self.model_name!r}, api_key_configured={bool(self.api_key)!r})"
