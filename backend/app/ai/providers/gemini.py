import json
from typing import Any

from pydantic import ValidationError

from app.ai.contracts import ProviderAnalysisResult, validate_provider_result
from app.ai.errors import (
    ProviderInvalidOutputError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.ai.providers.gemini_config import GeminiProviderConfig
from app.context.analysis_context import AnalysisContext


class GeminiProvider:
    """Concrete Gemini provider using only provider-facing AnalysisContext data."""

    def __init__(
        self,
        config: GeminiProviderConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = config or GeminiProviderConfig.from_env()
        self._client = client

    def analyze(self, context: AnalysisContext) -> ProviderAnalysisResult:
        client = self._get_client()
        instruction = self._build_instruction(context)
        try:
            response = client.models.generate_content(
                model=self.config.model_name,
                contents=instruction,
                config=self._response_config(),
            )
        except Exception as exc:
            raise self._map_provider_error(exc) from None

        try:
            result = self._parse_response(response)
            return validate_provider_result(context, result)
        except ProviderInvalidOutputError:
            raise
        except ValidationError as exc:
            raise ProviderInvalidOutputError("Gemini returned invalid structured output") from exc
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderInvalidOutputError("Gemini returned invalid structured output") from exc

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        api_key = self.config.require_api_key()
        try:
            from google import genai

            self._client = genai.Client(api_key=api_key)
            return self._client
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProviderUnavailableError("Gemini client is unavailable") from exc

    @staticmethod
    def _response_config() -> Any:
        from google.genai import types

        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ProviderAnalysisResult,
        )

    @staticmethod
    def _parse_response(response: Any) -> ProviderAnalysisResult:
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, ProviderAnalysisResult):
                return parsed
            return ProviderAnalysisResult.model_validate(parsed)

        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise ProviderInvalidOutputError("Gemini returned no structured output")
        return ProviderAnalysisResult.model_validate_json(text)

    @staticmethod
    def _build_instruction(context: AnalysisContext) -> str:
        serialized_context = json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return (
            "Analyze only the supplied evidence and deterministic facts. "
            "Do not invent facts, evidence, sources, prices, competitors, or unsupported conclusions. "
            "Missing evidence is not negative evidence. Preserve conflicting facts without resolving them. "
            "Use evidence_gap when evidence is insufficient. Distinguish observation from feedback_insight. "
            "Produce comparisons only when scope is research_run. Cite only the supplied semantic context IDs. "
            "Return only the requested structured JSON result.\n\n"
            f"Analysis context:\n{serialized_context}"
        )

    @staticmethod
    def _map_provider_error(error: Exception) -> Exception:
        error_type = type(error).__name__.lower()
        error_text = str(error).lower()
        if "timeout" in error_type or "timeout" in error_text:
            return ProviderTimeoutError("Gemini request timed out")
        if any(term in error_type or term in error_text for term in ("auth", "api key", "permission", "unauthorized")):
            return ProviderUnavailableError("Gemini authentication or configuration failed")
        if any(term in error_type or term in error_text for term in ("rate", "quota", "unavailable", "serviceunavailable")):
            return ProviderUnavailableError("Gemini provider is unavailable")
        return ProviderResponseError("Gemini provider request failed")
