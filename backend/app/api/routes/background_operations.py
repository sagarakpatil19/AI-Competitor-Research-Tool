from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.background.commands import (
    AIAnalysisCommand,
    BackgroundCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.background.runtime import BackgroundOperation, BackgroundRuntime, get_background_runtime
from app.api.response_mappers.research import (
    competitor_evidence_to_response,
    competitor_research_to_response,
    competitor_source_to_response,
)
from app.db.session import get_db
from app.models.ai_analysis import AIAnalysis
from app.models.competitor_discovery_candidate import CompetitorDiscoveryCandidate
from app.models.competitor_discovery_run import CompetitorDiscoveryRun
from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_research import CompetitorResearch
from app.models.competitor_source import CompetitorSource
from app.schemas.background_operation import BackgroundOperationResponse
from app.schemas.competitor_discovery_api import CompetitorDiscoveryApiResponse

router = APIRouter(prefix="/background-operations", tags=["background-operations"])


def _result_to_response(command: BackgroundCommand, result: Any, db: Session) -> dict[str, Any] | list[Any] | None:
    if result is None:
        return None
    if isinstance(command, CompetitorDiscoveryCommand):
        discovery_run = db.get(CompetitorDiscoveryRun, result.id)
        if discovery_run is None:
            return {"id": result.id}
        candidates = list(
            db.scalars(
                select(CompetitorDiscoveryCandidate)
                .where(CompetitorDiscoveryCandidate.discovery_run_id == discovery_run.id)
                .order_by(CompetitorDiscoveryCandidate.created_at.asc(), CompetitorDiscoveryCandidate.id.asc())
            ).all()
        )
        return CompetitorDiscoveryApiResponse(
            research_run=discovery_run,
            candidates=candidates,
        ).model_dump(mode="json")
    if isinstance(command, CompetitorResearchCommand):
        return {
            "competitor_research": [
                competitor_research_to_response(execution).model_dump(mode="json")
                for execution_id in (item.id for item in result)
                if (execution := db.get(CompetitorResearch, execution_id)) is not None
            ]
        }
    if isinstance(command, SourceCollectionCommand):
        source_result, evidence_result = result
        source = db.get(CompetitorSource, source_result.id)
        evidence = db.get(CompetitorEvidence, evidence_result.id)
        return {
            "source": competitor_source_to_response(source).model_dump(mode="json") if source else None,
            "evidence": competitor_evidence_to_response(evidence).model_dump(mode="json") if evidence else None,
        }
    if isinstance(command, AIAnalysisCommand):
        analysis = db.get(AIAnalysis, result.id)
        if analysis is None:
            return {"id": result.id}
        return {
            field: getattr(analysis, field)
            for field in (
                "id",
                "research_run_id",
                "competitor_research_id",
                "scope",
                "status",
                "provider_name",
                "model_name",
                "prompt_version",
                "contract_version",
                "input_snapshot_hash",
                "started_at",
                "completed_at",
                "failure_reason",
                "created_at",
                "updated_at",
            )
        }
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return [item if isinstance(item, dict) else {"id": item.id} for item in result]
    return {"id": result.id} if hasattr(result, "id") else {"value": str(result)}


def operation_to_response(
    operation: BackgroundOperation,
    db: Session | None = None,
) -> BackgroundOperationResponse:
    result = None
    if db is not None and operation.status == "completed":
        result = _result_to_response(operation.command, operation.result, db)
    return BackgroundOperationResponse(
        logical_id=operation.logical_id,
        research_run_id=operation.research_run_id,
        operation=operation.operation,
        status=operation.status,
        attempt_count=operation.attempt_count,
        max_attempts=operation.max_attempts,
        resource_reference=operation.resource_reference,
        result=result,
        failure_category=operation.failure_category,
        failure_reason=operation.failure_reason,
        status_url=f"/api/background-operations/{operation.logical_id}",
    )


@router.get("/{logical_id}", response_model=BackgroundOperationResponse)
def get_background_operation(
    logical_id: str,
    db: Session = Depends(get_db),
    runtime: BackgroundRuntime = Depends(get_background_runtime),
) -> BackgroundOperationResponse:
    operation = runtime.get_operation(logical_id)
    if operation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background operation not found")
    return operation_to_response(operation, db)