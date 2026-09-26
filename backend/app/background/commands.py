from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from app.ai.provider import AIProvider


@dataclass(frozen=True)
class BackgroundCommand:
    """Base background command payload."""

    command_type: str = field(init=False)
    attempt_count: int = field(default=1, kw_only=True)
    max_attempts: int = field(default=3, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.attempt_count, int) or isinstance(self.attempt_count, bool):
            raise ValueError("attempt_count must be an integer")
        if self.attempt_count < 1:
            raise ValueError("attempt_count must be a positive integer")
        if not isinstance(self.max_attempts, int) or isinstance(self.max_attempts, bool):
            raise ValueError("max_attempts must be an integer")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be a positive integer")
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count must not exceed max_attempts")

    @property
    def logical_id(self) -> str:
        payload = json.dumps(self._logical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _logical_payload(self) -> dict[str, Any]:
        return {"command_type": self.command_type}

    def with_retry_attempt(self, attempt_number: int | None = None) -> "BackgroundCommand":
        next_attempt = self.attempt_count + 1 if attempt_number is None else attempt_number
        if next_attempt < 1:
            raise ValueError("attempt_count must be a positive integer")
        if next_attempt > self.max_attempts:
            raise ValueError("attempt_count must not exceed max_attempts")
        values: dict[str, Any] = {}
        for field_name, field_value in self.__dict__.items():
            if field_name in {"command_type", "attempt_count", "max_attempts"}:
                continue
            values[field_name] = field_value
        values["attempt_count"] = next_attempt
        values["max_attempts"] = self.max_attempts
        return self.__class__(**values)

    def _validate_positive_int(self, value: int, field_name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class CompetitorDiscoveryCommand(BackgroundCommand):
    research_run_id: int
    command_type: str = field(init=False, default="competitor_discovery")

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_positive_int(self.research_run_id, "research_run_id")

    def _logical_payload(self) -> dict[str, Any]:
        return {
            "command_type": self.command_type,
            "research_run_id": self.research_run_id,
        }


@dataclass(frozen=True)
class CompetitorResearchCommand(BackgroundCommand):
    research_run_id: int
    competitor_ids: list[int]
    command_type: str = field(init=False, default="competitor_research")

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_positive_int(self.research_run_id, "research_run_id")
        if not self.competitor_ids:
            raise ValueError("competitor_ids must not be empty")
        for competitor_id in self.competitor_ids:
            self._validate_positive_int(competitor_id, "competitor_id")

    def _logical_payload(self) -> dict[str, Any]:
        return {
            "command_type": self.command_type,
            "research_run_id": self.research_run_id,
            "competitor_ids": sorted(set(self.competitor_ids)),
        }


@dataclass(frozen=True)
class SourceCollectionCommand(BackgroundCommand):
    research_run_id: int
    competitor_id: int
    competitor_research_id: int
    source_id: int
    command_type: str = field(init=False, default="source_collection")

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_positive_int(self.research_run_id, "research_run_id")
        self._validate_positive_int(self.competitor_id, "competitor_id")
        self._validate_positive_int(self.competitor_research_id, "competitor_research_id")
        self._validate_positive_int(self.source_id, "source_id")

    def _logical_payload(self) -> dict[str, Any]:
        return {
            "command_type": self.command_type,
            "research_run_id": self.research_run_id,
            "competitor_id": self.competitor_id,
            "competitor_research_id": self.competitor_research_id,
            "source_id": self.source_id,
        }


@dataclass(frozen=True)
class AIAnalysisCommand(BackgroundCommand):
    research_run_id: int
    scope: str
    provider: AIProvider
    contract_version: str = "contract-v1"
    prompt_version: str = "prompt-v1"
    competitor_research_id: int | None = None
    competitor_research_ids: list[int] | None = None
    command_type: str = field(init=False, default="ai_analysis")

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_positive_int(self.research_run_id, "research_run_id")
        if self.scope not in {"competitor", "research_run"}:
            raise ValueError("scope must be 'competitor' or 'research_run'")
        if self.scope == "competitor":
            if self.competitor_research_id is None:
                raise ValueError("competitor_research_id is required for competitor scope")
            self._validate_positive_int(self.competitor_research_id, "competitor_research_id")
        else:
            if not self.competitor_research_ids:
                raise ValueError("competitor_research_ids is required for research_run scope")
            for competitor_research_id in self.competitor_research_ids:
                self._validate_positive_int(competitor_research_id, "competitor_research_id")

    def _logical_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "command_type": self.command_type,
            "research_run_id": self.research_run_id,
            "scope": self.scope,
            "provider_name": type(self.provider).__name__,
            "contract_version": self.contract_version,
            "prompt_version": self.prompt_version,
        }
        if self.scope == "competitor":
            payload["competitor_research_id"] = self.competitor_research_id
        else:
            payload["competitor_research_ids"] = sorted(set(self.competitor_research_ids or []))
        return payload
