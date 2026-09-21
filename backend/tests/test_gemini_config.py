import pytest

from app.ai.errors import ProviderUnavailableError
from app.ai.providers.gemini_config import DEFAULT_GEMINI_MODEL, GeminiProviderConfig


def test_missing_gemini_api_key_is_allowed_until_provider_creation(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    config = GeminiProviderConfig.from_env()

    assert config.api_key is None
    assert config.model_name == DEFAULT_GEMINI_MODEL
    with pytest.raises(ProviderUnavailableError, match="GEMINI_API_KEY"):
        config.require_api_key()


def test_gemini_api_key_and_model_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-gemini-model")

    config = GeminiProviderConfig.from_env()

    assert config.api_key == "test-gemini-key"
    assert config.model_name == "test-gemini-model"
    assert config.require_api_key() == "test-gemini-key"


def test_blank_model_uses_deterministic_default(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "   ")

    config = GeminiProviderConfig.from_env()

    assert config.model_name == DEFAULT_GEMINI_MODEL


def test_api_key_is_not_exposed_in_repr_or_missing_key_error(monkeypatch):
    secret = "test-secret-gemini-key"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    config = GeminiProviderConfig.from_env()

    assert secret not in repr(config)
    assert "api_key=" not in repr(config)

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailableError) as error:
        GeminiProviderConfig.from_env().require_api_key()
    assert secret not in str(error.value)
