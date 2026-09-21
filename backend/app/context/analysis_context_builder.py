import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.context.analysis_context import (
    AnalysisContext,
    AnalysisContextRequest,
    ContextCompetitor,
    ContextEvidence,
    ContextFact,
    ContextMapping,
    ContextSection,
    ContextSource,
    InternalContextResult,
    SnapshotMetadata,
)
from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_research import CompetitorResearch
from app.models.competitor_research_fact import CompetitorResearchFact
from app.models.competitor_research_fact_evidence import CompetitorResearchFactEvidence
from app.models.competitor_research_section import CompetitorResearchSectionName
from app.models.research_run import ResearchRun
from app.repositories import competitor_evidence as evidence_repository
from app.repositories import competitor_research as research_repository
from app.repositories import competitor_research_fact_evidence as fact_evidence_repository
from app.repositories import competitor_research_facts as fact_repository
from app.repositories import competitor_research_sections as section_repository
from app.repositories import competitor_sources as source_repository
from app.repositories import competitors as competitor_repository
from app.repositories import research_runs as research_run_repository


CANONICALIZATION_VERSION = "m12-context-v1"
VALID_PROCESSING_STATUS = "processed"
VALID_VALIDATION_STATUS = "valid"
SECTION_ORDER = tuple(section.value for section in CompetitorResearchSectionName)


class AnalysisContextError(ValueError):
    """Base error for malformed or invalid M11 context input."""


class AnalysisContextBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, request: AnalysisContextRequest) -> InternalContextResult:
        research_run = research_run_repository.get_research_run(self.db, request.research_run_id)
        if research_run is None:
            raise LookupError("Research run not found")

        execution_ids = self._execution_ids(request)
        executions = research_repository.get_by_ids(self.db, execution_ids)
        executions_by_id = {execution.id: execution for execution in executions}
        missing_ids = [execution_id for execution_id in execution_ids if execution_id not in executions_by_id]
        if missing_ids:
            raise LookupError(f"Competitor research execution not found: {missing_ids[0]}")

        competitors_by_id = self._validate_executions(research_run, executions_by_id.values())
        sections = section_repository.list_by_competitor_research_ids(self.db, execution_ids)
        sections_by_execution = self._validate_sections(execution_ids, sections)
        facts = fact_repository.list_by_competitor_research_ids(self.db, execution_ids)
        links = fact_evidence_repository.list_by_fact_ids(self.db, [fact.id for fact in facts]) if facts else []
        evidence = evidence_repository.list_by_competitor_research_ids(self.db, execution_ids)
        evidence_by_id = {item.id: item for item in evidence}
        valid_evidence = {
            item.id: item
            for item in evidence
            if item.processing_status == VALID_PROCESSING_STATUS
            and item.validation_status == VALID_VALIDATION_STATUS
        }
        links_by_fact = self._group_links(links)
        fact_ids_by_evidence = self._group_fact_ids(links, facts)
        self._validate_fact_provenance(facts, links_by_fact, valid_evidence, evidence_by_id)
        referenced_source_ids = [
            item.source_id
            for item in valid_evidence.values()
            if item.source_id is not None
        ]
        sources = source_repository.get_by_ids(self.db, list(set(referenced_source_ids))) if referenced_source_ids else []
        sources_by_id = {source.id: source for source in sources}
        self._validate_sources(valid_evidence.values(), sources_by_id, executions_by_id)

        competitor_items, competitor_context_by_execution, competitor_mapping = self._build_competitors(
            executions_by_id,
            competitors_by_id,
        )
        fact_items, fact_context_by_id, fact_mapping = self._build_facts(
            facts,
            competitor_context_by_execution,
            links_by_fact,
            valid_evidence,
        )
        source_items, source_context_by_id, source_mapping = self._build_sources(sources)
        evidence_items, evidence_context_by_id, evidence_mapping = self._build_evidence(
            valid_evidence.values(),
            competitor_context_by_execution,
            fact_ids_by_evidence,
            fact_context_by_id,
            source_context_by_id,
        )
        fact_items = [
            fact.model_copy(update={
                "evidence_context_ids": sorted(
                    evidence_context_by_id[link.evidence_id]
                    for link in links_by_fact.get(
                        next(
                            database_id
                            for database_id, context_id in fact_context_by_id.items()
                            if context_id == fact.context_id
                        ),
                        [],
                    )
                    if link.evidence_id in evidence_context_by_id
                )
            })
            for fact in fact_items
        ]
        section_items = self._build_sections(
            execution_ids,
            sections_by_execution,
            competitor_context_by_execution,
            facts,
            valid_evidence,
            fact_ids_by_evidence,
        )
        mapping = ContextMapping(
            competitor_context_to_database_id=competitor_mapping[0],
            competitor_context_to_competitor_id=competitor_mapping[1],
            fact_context_to_database_id=fact_mapping,
            evidence_context_to_database_id=evidence_mapping,
            source_context_to_database_id=source_mapping,
            database_competitor_to_context_id=self._reverse_mapping(competitor_mapping[0]),
            database_fact_to_context_id=self._reverse_mapping(fact_mapping),
            database_evidence_to_context_id=self._reverse_mapping(evidence_mapping),
            database_source_to_context_id=self._reverse_mapping(source_mapping),
        )
        snapshot_payload = self._snapshot_payload(
            request,
            competitor_items,
            section_items,
            fact_items,
            evidence_items,
            source_items,
        )
        snapshot_hash = hashlib.sha256(
            json.dumps(snapshot_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        generated_at = datetime.now(timezone.utc)
        snapshot = SnapshotMetadata(
            input_snapshot_hash=snapshot_hash,
            canonicalization_version=CANONICALIZATION_VERSION,
            contract_version=request.contract_version,
            prompt_version=request.prompt_version,
            generated_at=generated_at,
        )
        return InternalContextResult(
            context=AnalysisContext(
                contract_version=request.contract_version,
                prompt_version=request.prompt_version,
                scope=request.scope,
                competitors=competitor_items,
                sections=section_items,
                facts=fact_items,
                evidence=evidence_items,
                sources=source_items,
                snapshot=snapshot,
            ),
            mapping=mapping,
        )

    def _execution_ids(self, request: AnalysisContextRequest) -> list[int]:
        if request.scope == "competitor":
            return [request.competitor_research_id]  # type: ignore[list-item]
        return list(request.competitor_research_ids)

    def _validate_executions(
        self,
        research_run: ResearchRun,
        executions: object,
    ) -> dict[int, object]:
        execution_list = list(executions)  # type: ignore[arg-type]
        competitors = competitor_repository.get_by_ids(
            self.db,
            [execution.competitor_id for execution in execution_list],
        )
        competitors_by_id: dict[int, object] = {competitor.id: competitor for competitor in competitors}
        for execution in execution_list:
            if execution.research_run_id != research_run.id:
                raise AnalysisContextError("Competitor research execution must belong to the research run")
            competitor = competitors_by_id.get(execution.competitor_id)
            if competitor is None:
                raise AnalysisContextError("Competitor for research execution not found")
            if competitor.research_run_id != research_run.id:
                raise AnalysisContextError("Competitor must belong to the research run")
        return competitors_by_id

    def _validate_sections(
        self,
        execution_ids: list[int],
        sections: list,
    ) -> dict[int, dict[str, object]]:
        grouped: dict[int, dict[str, object]] = {execution_id: {} for execution_id in execution_ids}
        for section in sections:
            if section.section in grouped[section.competitor_research_id]:
                raise AnalysisContextError("Duplicate competitor research section")
            grouped[section.competitor_research_id][section.section] = section
        for execution_id, values in grouped.items():
            if set(values) != set(SECTION_ORDER):
                raise AnalysisContextError("Competitor research execution must contain all six sections")
        return grouped

    @staticmethod
    def _reverse_mapping(mapping: dict[str, int]) -> dict[int, str]:
        reversed_mapping: dict[int, str] = {}
        for context_id, database_id in mapping.items():
            if database_id in reversed_mapping:
                raise AnalysisContextError("Selected entity maps to multiple context IDs")
            reversed_mapping[database_id] = context_id
        return reversed_mapping

    @staticmethod
    def _group_links(links: list[CompetitorResearchFactEvidence]) -> dict[int, list[CompetitorResearchFactEvidence]]:
        grouped: dict[int, list[CompetitorResearchFactEvidence]] = {}
        for link in links:
            grouped.setdefault(link.fact_id, []).append(link)
        return grouped

    @staticmethod
    def _group_fact_ids(
        links: list[CompetitorResearchFactEvidence],
        facts: list[CompetitorResearchFact],
    ) -> dict[int, list[int]]:
        fact_execution = {fact.id: fact.competitor_research_id for fact in facts}
        grouped: dict[int, list[int]] = {}
        for link in links:
            if link.fact_id not in fact_execution:
                raise AnalysisContextError("Fact provenance references an unknown fact")
            grouped.setdefault(link.evidence_id, []).append(link.fact_id)
        return grouped

    @staticmethod
    def _validate_fact_provenance(
        facts: list[CompetitorResearchFact],
        links_by_fact: dict[int, list[CompetitorResearchFactEvidence]],
        valid_evidence: dict[int, CompetitorEvidence],
        evidence_by_id: dict[int, CompetitorEvidence],
    ) -> None:
        for fact in facts:
            links = links_by_fact.get(fact.id, [])
            if not links:
                raise AnalysisContextError(f"Fact provenance is invalid for fact {fact.id}")
            for link in links:
                evidence = evidence_by_id.get(link.evidence_id)
                if evidence is None:
                    raise AnalysisContextError(f"Fact provenance references missing evidence for fact {fact.id}")
                if evidence.competitor_research_id != fact.competitor_research_id:
                    raise AnalysisContextError(f"Fact provenance crosses executions for fact {fact.id}")
                if evidence.processing_status != VALID_PROCESSING_STATUS:
                    raise AnalysisContextError(f"Fact provenance evidence is not processed for fact {fact.id}")
                if evidence.validation_status != VALID_VALIDATION_STATUS:
                    raise AnalysisContextError(f"Fact provenance evidence is not valid for fact {fact.id}")

    @staticmethod
    def _validate_sources(
        evidence: object,
        sources_by_id: dict[int, object],
        executions_by_id: dict[int, object],
    ) -> None:
        for item in evidence:  # type: ignore[union-attr]
            if item.source_id is None:
                continue
            source = sources_by_id.get(item.source_id)
            if source is None or source.competitor_research_id != item.competitor_research_id:
                raise AnalysisContextError("Evidence source relationship is invalid")

    def _build_competitors(self, executions_by_id: dict[int, object], competitors_by_id: dict[int, object]):
        ordered = sorted(
            executions_by_id.values(),
            key=lambda item: (
                (competitors_by_id[item.competitor_id].domain or "").casefold(),
                competitors_by_id[item.competitor_id].name.casefold(),
                item.id,
            ),
        )
        execution_context: dict[int, str] = {}
        competitor_mapping: dict[str, int] = {}
        competitor_id_mapping: dict[str, int] = {}
        items: list[ContextCompetitor] = []
        for number, execution in enumerate(ordered, 1):
            context_id = f"COMPETITOR_{number:03d}"
            competitor = competitors_by_id[execution.competitor_id]
            execution_context[execution.id] = context_id
            competitor_mapping[context_id] = execution.id
            competitor_id_mapping[context_id] = competitor.id
            items.append(ContextCompetitor(
                context_id=context_id,
                name=competitor.name,
                domain=competitor.domain,
                website=competitor.website,
                research_execution_status=execution.status,
            ))
        return items, execution_context, (competitor_mapping, competitor_id_mapping)

    def _build_facts(self, facts, execution_context, links_by_fact, valid_evidence):
        eligible = [
            fact for fact in facts
            if any(link.evidence_id in valid_evidence for link in links_by_fact.get(fact.id, []))
        ]
        ordered = sorted(
            eligible,
            key=lambda fact: (
                execution_context[fact.competitor_research_id],
                fact.section,
                fact.fact_type,
                fact.normalized_key,
                fact.id,
            ),
        )
        context_by_id: dict[int, str] = {}
        mapping: dict[str, int] = {}
        items: list[ContextFact] = []
        for number, fact in enumerate(ordered, 1):
            context_id = f"FACT_{number:03d}"
            context_by_id[fact.id] = context_id
            mapping[context_id] = fact.id
            evidence_ids = sorted(
                link.evidence_id for link in links_by_fact.get(fact.id, []) if link.evidence_id in valid_evidence
            )
            items.append(ContextFact(
                context_id=context_id,
                competitor_context_id=execution_context[fact.competitor_research_id],
                section=fact.section,
                fact_type=fact.fact_type,
                subject=fact.subject,
                value_text=fact.value_text,
                value_numeric=fact.value_numeric,
                currency=fact.currency,
                unit=fact.unit,
                period=fact.period,
                normalized_key=fact.normalized_key,
                evidence_context_ids=[],
            ))
        return items, context_by_id, mapping

    def _build_sources(self, sources):
        ordered = sorted(sources, key=lambda source: (source.canonical_url.casefold(), source.source_type or "", source.id))
        context_by_id: dict[int, str] = {}
        mapping: dict[str, int] = {}
        items: list[ContextSource] = []
        for number, source in enumerate(ordered, 1):
            context_id = f"SOURCE_{number:03d}"
            context_by_id[source.id] = context_id
            mapping[context_id] = source.id
            items.append(ContextSource(
                context_id=context_id,
                canonical_url=source.canonical_url,
                source_type=source.source_type,
                discovery_method=source.discovery_method,
                status=source.status,
                last_http_status=source.last_http_status,
                last_attempted_at=source.last_attempted_at,
                content_hash=source.content_hash,
                domain=urlsplit(source.canonical_url).hostname,
            ))
        return items, context_by_id, mapping

    def _build_evidence(self, evidence, execution_context, fact_ids_by_evidence, fact_context_by_id, source_context_by_id):
        ordered = sorted(evidence, key=lambda item: (execution_context[item.competitor_research_id], item.normalized_content_hash or "", item.source_url, item.id))
        mapping: dict[str, int] = {}
        context_by_id: dict[int, str] = {}
        items: list[ContextEvidence] = []
        for number, item in enumerate(ordered, 1):
            content = item.normalized_content or item.normalized_excerpt
            if not content:
                raise AnalysisContextError(f"Valid evidence has no normalized content: {item.id}")
            context_id = f"EVIDENCE_{number:03d}"
            context_by_id[item.id] = context_id
            mapping[context_id] = item.id
            source_context_id = source_context_by_id.get(item.source_id) if item.source_id is not None else None
            fact_context_ids = sorted(
                fact_context_by_id[fact_id]
                for fact_id in fact_ids_by_evidence.get(item.id, [])
                if fact_id in fact_context_by_id
            )
            items.append(ContextEvidence(
                context_id=context_id,
                competitor_context_id=execution_context[item.competitor_research_id],
                content=content,
                normalized_excerpt=item.normalized_excerpt,
                content_hash=item.normalized_content_hash,
                processing_status=item.processing_status,
                validation_status=item.validation_status,
                source_context_id=source_context_id,
                source_url=item.source_url,
                source_title=item.source_title,
                source_type=item.source_type,
                publisher=item.publisher,
                published_at=item.published_at,
                retrieved_at=item.retrieved_at,
                fact_context_ids=fact_context_ids,
            ))
        return items, context_by_id, mapping

    def _build_sections(self, execution_ids, sections_by_execution, execution_context, facts, valid_evidence, fact_ids_by_evidence):
        facts_by_execution = {execution_id: 0 for execution_id in execution_ids}
        for fact in facts:
            facts_by_execution[fact.competitor_research_id] += 1
        evidence_by_execution = {execution_id: 0 for execution_id in execution_ids}
        without_fact_by_execution = {execution_id: 0 for execution_id in execution_ids}
        for evidence in valid_evidence.values():
            evidence_by_execution[evidence.competitor_research_id] += 1
            if not fact_ids_by_evidence.get(evidence.id):
                without_fact_by_execution[evidence.competitor_research_id] += 1
        items: list[ContextSection] = []
        for execution_id in execution_ids:
            for section_name in SECTION_ORDER:
                section = sections_by_execution[execution_id][section_name]
                section_fact_count = sum(
                    1 for fact in facts if fact.competitor_research_id == execution_id and fact.section == section_name
                )
                items.append(ContextSection(
                    competitor_context_id=execution_context[execution_id],
                    section=section.section,
                    status=section.status,
                    reason=section.reason,
                    fact_count=section_fact_count,
                    valid_evidence_count=evidence_by_execution[execution_id],
                    evidence_without_fact_count=without_fact_by_execution[execution_id],
                ))
        return items

    @staticmethod
    def _snapshot_payload(request, competitors, sections, facts, evidence, sources):
        def normalize(value):
            if isinstance(value, Decimal):
                return format(value, "f")
            if isinstance(value, datetime):
                return value.astimezone(timezone.utc).isoformat()
            if isinstance(value, str):
                return unicodedata.normalize("NFC", value)
            if isinstance(value, list):
                return [normalize(item) for item in value]
            if isinstance(value, dict):
                return {key: normalize(item) for key, item in value.items()}
            return value

        return normalize({
            "canonicalization_version": CANONICALIZATION_VERSION,
            "contract_version": request.contract_version,
            "prompt_version": request.prompt_version,
            "scope": request.scope,
            "competitors": [item.model_dump(mode="python") for item in competitors],
            "sections": [item.model_dump(mode="python") for item in sections],
            "facts": [item.model_dump(mode="python") for item in facts],
            "evidence": [item.model_dump(mode="python") for item in evidence],
            "sources": [item.model_dump(mode="python") for item in sources],
        })


def build_analysis_context(db: Session, request: AnalysisContextRequest) -> InternalContextResult:
    return AnalysisContextBuilder(db).build(request)
