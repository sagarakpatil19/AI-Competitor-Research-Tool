import json
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.ai.contracts import (
    ComparisonRole,
    EvidenceReferenceRole,
    FactReferenceRole,
    ProviderAnalysisResult,
    StatementType,
    SupportStatus,
    validate_provider_result,
)
from app.ai.errors import (
    ProviderInvalidOutputError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.ai.providers.gemini_config import GeminiProviderConfig
from app.context.analysis_context import AnalysisContext


class _FactRoleAssignment(BaseModel):
    context_id: str
    role: FactReferenceRole


class _EvidenceRoleAssignment(BaseModel):
    context_id: str
    role: EvidenceReferenceRole


class _CompetitorRoleAssignment(BaseModel):
    context_id: str
    role: ComparisonRole


class _AIStatementWireResult(BaseModel):
    statement_id: str = Field(min_length=1)
    statement_type: StatementType
    text: str = Field(min_length=1)
    support_status: SupportStatus
    competitor_context_id: str | None = None
    fact_context_ids: list[str] = Field(default_factory=list)
    evidence_context_ids: list[str] = Field(default_factory=list)
    source_context_ids: list[str] = Field(default_factory=list)
    fact_roles: list[_FactRoleAssignment] = Field(default_factory=list)
    evidence_roles: list[_EvidenceRoleAssignment] = Field(default_factory=list)


class _AIComparisonWireResult(BaseModel):
    comparison_id: str = Field(min_length=1)
    comparison_type: str = Field(min_length=1, max_length=32)
    dimension: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1)
    support_status: SupportStatus
    competitor_context_ids: list[str] = Field(min_length=2)
    fact_context_ids: list[str] = Field(default_factory=list)
    evidence_context_ids: list[str] = Field(default_factory=list)
    source_context_ids: list[str] = Field(default_factory=list)
    competitor_roles: list[_CompetitorRoleAssignment] = Field(default_factory=list)


class _ProviderAnalysisWireResult(BaseModel):
    scope: Literal["competitor", "research_run"]
    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=255)
    statements: list[_AIStatementWireResult] = Field(default_factory=list)
    comparisons: list[_AIComparisonWireResult] = Field(default_factory=list)


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
        except (TypeError, ValueError, ValidationError) as exc:
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
            response_schema=_ProviderAnalysisWireResult,
        )

    @staticmethod
    def _parse_response(response: Any) -> ProviderAnalysisResult:
        if response is None:
            raise ProviderInvalidOutputError("Gemini returned no structured output")

        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            return GeminiProvider._parse_wire_result(parsed)

        text = getattr(response, "text", None)
        if not isinstance(text, str):
            raise ProviderInvalidOutputError("Gemini returned no structured output")
        normalized_text = text.strip()
        if not normalized_text:
            raise ProviderInvalidOutputError("Gemini returned no structured output")

        try:
            payload = json.loads(normalized_text)
        except json.JSONDecodeError as exc:
            raise ProviderInvalidOutputError("Gemini returned invalid structured output") from exc

        if payload is None:
            raise ProviderInvalidOutputError("Gemini returned no structured output")

        return GeminiProvider._parse_wire_result(payload)

    @staticmethod
    def _parse_wire_result(payload: Any) -> ProviderAnalysisResult:
        try:
            wire_result = _ProviderAnalysisWireResult.model_validate(payload)
            result_data = wire_result.model_dump()
            for statement in result_data["statements"]:
                statement["fact_roles"] = _role_assignments_to_dict(statement["fact_roles"], "fact")
                statement["evidence_roles"] = _role_assignments_to_dict(
                    statement["evidence_roles"],
                    "evidence",
                )
            for comparison in result_data["comparisons"]:
                comparison["competitor_roles"] = _role_assignments_to_dict(
                    comparison["competitor_roles"],
                    "competitor",
                )
            return ProviderAnalysisResult.model_validate(result_data)
        except ProviderInvalidOutputError:
            raise
        except (TypeError, ValueError, ValidationError) as exc:
            raise ProviderInvalidOutputError("Gemini returned invalid structured output") from exc

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

    def _map_provider_error(self, error: Exception) -> Exception:
        error_type = type(error).__name__.lower()
        sanitized_error = self._redact_secret(str(error), self.config.api_key)
        error_text = sanitized_error.lower()

        if "timeout" in error_type or "timeout" in error_text:
            return ProviderTimeoutError("Gemini request timed out")
        if any(term in error_type or term in error_text for term in ("auth", "api key", "permission", "unauthorized", "forbidden", "credentials")):
            return ProviderUnavailableError("Gemini authentication or configuration failed")
        if any(term in error_type or term in error_text for term in ("rate", "quota", "unavailable", "serviceunavailable", "429", "503")):
            return ProviderUnavailableError("Gemini provider is unavailable")
        return ProviderResponseError("Gemini provider request failed")

    @staticmethod
    def _redact_secret(message: str, secret: str | None) -> str:
        if not message or not secret:
            return message
        return message.replace(secret, "[REDACTED]")


def _role_assignments_to_dict(
    assignments: list[dict[str, str]],
    role_kind: str,
) -> dict[str, str]:
    roles: dict[str, str] = {}
    for assignment in assignments:
        context_id = assignment["context_id"]
        if context_id in roles:
            raise ProviderInvalidOutputError(
                f"Gemini returned duplicate {role_kind} role context ID"
            )
        roles[context_id] = assignment["role"]
    return roles
