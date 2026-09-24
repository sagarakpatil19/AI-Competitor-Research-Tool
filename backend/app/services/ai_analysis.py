from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ai.contracts import ProviderAnalysisResult, validate_provider_result
from app.ai.provider import AIProvider
from app.context.analysis_context import AnalysisContextRequest
from app.context.analysis_context_builder import build_analysis_context
from app.models.ai_analysis import AIAnalysis
from app.models.ai_analysis_input_evidence import AIAnalysisInputEvidence
from app.models.ai_analysis_input_fact import AIAnalysisInputFact
from app.models.ai_comparison import AIComparison
from app.models.ai_comparison_competitor import AIComparisonCompetitor
from app.models.ai_statement import AIStatement
from app.models.ai_statement_evidence import AIStatementEvidence
from app.models.ai_statement_fact import AIStatementFact


def execute_ai_analysis(
    db: Session,
    research_run_id: int,
    *,
    provider: AIProvider,
    scope: str,
    competitor_research_id: int | None = None,
    competitor_research_ids: list[int] | None = None,
    contract_version: str = "contract-v1",
    prompt_version: str = "prompt-v1",
) -> AIAnalysis:
    if provider is None:
        raise ValueError("AI provider is required")

    requested_scope = scope
    if requested_scope == "competitor":
        if competitor_research_id is None:
            raise ValueError("Competitor scope requires competitor_research_id")
        selected_ids: list[int] = [competitor_research_id]
    elif requested_scope == "research_run":
        selected_ids = list(competitor_research_ids or [])
        if not selected_ids:
            raise ValueError("Research-run scope requires explicit competitor_research_ids")
    else:
        raise ValueError("Scope must be 'competitor' or 'research_run'")

    request = AnalysisContextRequest(
        scope=requested_scope,
        research_run_id=research_run_id,
        competitor_research_id=competitor_research_id if requested_scope == "competitor" else None,
        competitor_research_ids=selected_ids if requested_scope == "research_run" else [],
        contract_version=contract_version,
        prompt_version=prompt_version,
    )

    analysis = AIAnalysis(
        research_run_id=research_run_id,
        competitor_research_id=competitor_research_id,
        scope=requested_scope,
        status="pending",
        provider_name=_provider_name(provider),
        model_name="unknown",
        prompt_version=prompt_version,
        contract_version=contract_version,
    )
    db.add(analysis)
    db.flush()

    try:
        analysis.status = "running"
        analysis.started_at = datetime.now(timezone.utc)
        context_result = build_analysis_context(db, request)
        context = context_result.context
        provider_result = provider.analyze(context)
        validated = validate_provider_result(context, provider_result)

        analysis.provider_name = validated.provider
        analysis.model_name = validated.model
        analysis.input_snapshot_hash = context.snapshot.input_snapshot_hash
        analysis.status = "completed"
        analysis.completed_at = datetime.now(timezone.utc)

        _persist_input_facts(db, analysis.id, context_result.mapping.fact_context_to_database_id, context.facts)
        _persist_input_evidence(db, analysis.id, context_result.mapping.evidence_context_to_database_id, context.evidence)
        _persist_statements(db, analysis.id, context_result.mapping, validated)
        _persist_comparisons(db, analysis.id, context_result.mapping, validated)

        db.commit()
        db.refresh(analysis)
        return analysis
    except Exception as exc:
        failure_reason = str(exc)[:1000]
        db.rollback()
        analysis = AIAnalysis(
            research_run_id=research_run_id,
            competitor_research_id=competitor_research_id,
            scope=requested_scope,
            status="failed",
            provider_name=_provider_name(provider),
            model_name="unknown",
            prompt_version=prompt_version,
            contract_version=contract_version,
            failure_reason=failure_reason,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis


def _provider_name(provider: AIProvider) -> str:
    value = getattr(provider, "provider_name", None)
    if value:
        return str(value)[:100]
    return getattr(provider.__class__, "__name__", "unknown")[:100]


def _persist_input_facts(
    db: Session,
    analysis_id: int,
    fact_context_to_database_id: dict[str, int],
    facts: list[Any],
) -> None:
    for fact in facts:
        db.add(AIAnalysisInputFact(analysis_id=analysis_id, fact_id=fact_context_to_database_id[fact.context_id]))


def _persist_input_evidence(
    db: Session,
    analysis_id: int,
    evidence_context_to_database_id: dict[str, int],
    evidence: list[Any],
) -> None:
    for item in evidence:
        db.add(
            AIAnalysisInputEvidence(
                analysis_id=analysis_id,
                evidence_id=evidence_context_to_database_id[item.context_id],
                content_hash=item.content_hash,
                normalized_excerpt=item.normalized_excerpt,
            )
        )


def _persist_statements(db: Session, analysis_id: int, mapping: Any, result: ProviderAnalysisResult) -> None:
    for statement in result.statements:
        competitor_research_id = None
        if statement.competitor_context_id:
            competitor_research_id = mapping.competitor_context_to_database_id.get(statement.competitor_context_id)
        elif statement.fact_context_ids or statement.evidence_context_ids:
            candidate_ids = []
            for context_id in statement.fact_context_ids:
                candidate_ids.append(mapping.fact_context_to_database_id.get(context_id))
            for context_id in statement.evidence_context_ids:
                candidate_ids.append(mapping.evidence_context_to_database_id.get(context_id))
            unique = {item for item in candidate_ids if item is not None}
            if len(unique) == 1:
                competitor_research_id = _resolve_competitor_research_for_fact_or_evidence(db, unique.pop())

        saved = AIStatement(
            analysis_id=analysis_id,
            statement_type=statement.statement_type,
            text=statement.text,
            support_status=statement.support_status,
            competitor_research_id=competitor_research_id,
        )
        db.add(saved)
        db.flush()

        for context_id in statement.fact_context_ids:
            db.add(AIStatementFact(
                statement_id=saved.id,
                fact_id=mapping.fact_context_to_database_id[context_id],
                role=statement.fact_roles.get(context_id, "context"),
            ))

        for context_id in statement.evidence_context_ids:
            db.add(AIStatementEvidence(
                statement_id=saved.id,
                evidence_id=mapping.evidence_context_to_database_id[context_id],
                role=statement.evidence_roles.get(context_id, "context"),
            ))


def _resolve_competitor_research_for_fact_or_evidence(db: Session, database_id: int) -> int | None:
    from app.models.competitor_research_fact import CompetitorResearchFact
    from app.models.competitor_evidence import CompetitorEvidence

    fact = db.get(CompetitorResearchFact, database_id)
    if fact is not None:
        return fact.competitor_research_id
    evidence = db.get(CompetitorEvidence, database_id)
    if evidence is not None:
        return evidence.competitor_research_id
    return None


def _persist_comparisons(db: Session, analysis_id: int, mapping: Any, result: ProviderAnalysisResult) -> None:
    for comparison in result.comparisons:
        comparison_row = AIComparison(
            analysis_id=analysis_id,
            comparison_type=comparison.comparison_type,
            dimension=comparison.dimension,
            statement=comparison.statement,
            support_status=comparison.support_status,
        )
        db.add(comparison_row)
        db.flush()

        roles = dict(comparison.competitor_roles)
        ordered_context_ids = comparison.competitor_context_ids
        for index, context_id in enumerate(ordered_context_ids):
            if context_id in roles:
                continue
            if index == 0:
                roles[context_id] = "subject"
            elif index == 1 and len(ordered_context_ids) > 2:
                roles[context_id] = "baseline"
            else:
                roles[context_id] = "compared"

        for context_id in ordered_context_ids:
            db.add(AIComparisonCompetitor(
                comparison_id=comparison_row.id,
                competitor_research_id=mapping.competitor_context_to_database_id[context_id],
                role=roles.get(context_id, "compared"),
            ))
