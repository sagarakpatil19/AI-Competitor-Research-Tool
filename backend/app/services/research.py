import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.company_research import CompanyResearch
from app.models.competitor import Competitor
from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_research import CompetitorResearch
from app.models.competitor_source import CompetitorSource
from app.integrations.source_retriever import (
    HttpxSourceRetriever,
    MAX_EXCERPT_LENGTH,
    RetrievalError,
    SourceRetriever,
    canonicalize_url,
)
from app.models.research_run import ResearchInputType, ResearchRun, ResearchRunStatus
from app.repositories import company_research as company_research_repository
from app.repositories import competitors as competitor_repository
from app.repositories import competitor_research as competitor_research_repository
from app.repositories import competitor_evidence as competitor_evidence_repository
from app.repositories import competitor_sources as competitor_source_repository
from app.repositories import research_runs as research_run_repository


DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$",
    re.IGNORECASE,
)

source_retriever: SourceRetriever = HttpxSourceRetriever()

PROCESSING_PENDING = "pending"
PROCESSING_PROCESSED = "processed"
PROCESSING_FAILED = "failed"
VALIDATION_PENDING = "pending"
VALIDATION_VALID = "valid"
VALIDATION_INVALID = "invalid"
VALIDATION_UNUSABLE = "unusable"
VALIDATION_DUPLICATE = "duplicate"
MAX_VALIDATION_REASON_LENGTH = 1000
MIN_MEANINGFUL_CONTENT_LENGTH = 32


class SourceCollectionError(ValueError):
    def __init__(self, category: str, reason: str, http_status: int | None = None) -> None:
        super().__init__(reason)
        self.category = category
        self.http_status = http_status


def _normalize_domain(hostname: str) -> str:
    normalized_domain = hostname.rstrip(".").lower()
    if normalized_domain.startswith("www."):
        normalized_domain = normalized_domain[4:]
    return normalized_domain


def classify_input(input_value: str) -> tuple[ResearchInputType, str | None]:
    normalized_input = input_value.strip()
    if not normalized_input:
        raise ValueError("Company name or URL must not be empty")

    parsed = urlparse(normalized_input)
    if parsed.scheme:
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Input must be a valid HTTP/HTTPS URL, domain, or company name")
        hostname = parsed.hostname
        if hostname is None or not DOMAIN_PATTERN.fullmatch(hostname):
            raise ValueError("Input must be a valid HTTP/HTTPS URL, domain, or company name")
        return ResearchInputType.URL, _normalize_domain(hostname)

    domain_candidate = normalized_input.rstrip(".")
    if DOMAIN_PATTERN.fullmatch(domain_candidate):
        return ResearchInputType.DOMAIN, _normalize_domain(domain_candidate)

    if "/" in normalized_input or "?" in normalized_input or "#" in normalized_input:
        raise ValueError("Input must be a valid HTTP/HTTPS URL, domain, or company name")

    return ResearchInputType.COMPANY_NAME, None


def create_research_run(db: Session, input_value: str) -> ResearchRun:
    normalized_input = input_value.strip()
    if not normalized_input:
        raise ValueError("Company name or URL must not be empty")

    research_run = ResearchRun(
        input_value=normalized_input,
        status=ResearchRunStatus.SUBMITTED,
    )
    return research_run_repository.create_research_run(db, research_run)


def get_research_run(db: Session, research_id: int) -> ResearchRun | None:
    return research_run_repository.get_research_run(db, research_id)


def resolve_research_run(db: Session, research_run: ResearchRun) -> ResearchRun:
    input_type, resolved_domain = classify_input(research_run.input_value)
    research_run.status = ResearchRunStatus.RESOLVING
    research_run.input_type = input_type
    research_run.resolved_domain = resolved_domain
    return research_run_repository.save_research_run(db, research_run)


def understand_company(db: Session, research_run: ResearchRun) -> CompanyResearch:
    if research_run.input_type is None or research_run.status != ResearchRunStatus.RESOLVING:
        raise ValueError("Research input must be resolved before company understanding")

    if research_run.input_type in {ResearchInputType.URL, ResearchInputType.DOMAIN}:
        if research_run.resolved_domain is None:
            raise ValueError("A resolved domain is required for this research input")

    company_research = company_research_repository.get_by_research_run_id(db, research_run.id)
    if company_research is None:
        company_research = CompanyResearch(research_run_id=research_run.id)

    company_research.company_name = (
        research_run.input_value
        if research_run.input_type == ResearchInputType.COMPANY_NAME
        else company_research.company_name
    )
    company_research.domain = research_run.resolved_domain

    if company_research.id is None:
        company_research = company_research_repository.create_company_research(db, company_research)
    else:
        company_research = company_research_repository.save_company_research(db, company_research)

    return company_research


def discover_competitors(db: Session, research_run: ResearchRun, candidates) -> list[Competitor]:
    if research_run.status != ResearchRunStatus.RESOLVING:
        raise ValueError("Company understanding must be completed before competitor discovery")

    if company_research_repository.get_by_research_run_id(db, research_run.id) is None:
        raise ValueError("Company understanding must be completed before competitor discovery")

    normalized_candidates: list[tuple[str, str]] = []
    seen_domains: set[str] = set()
    for candidate in candidates:
        name = candidate.name.strip()
        domain = candidate.domain.strip().rstrip(".")
        if not name:
            raise ValueError("Competitor name must not be empty")
        if not domain or not DOMAIN_PATTERN.fullmatch(domain):
            raise ValueError("Competitor domain must be a valid domain")
        normalized_domain = _normalize_domain(domain)
        if normalized_domain in seen_domains:
            continue
        seen_domains.add(normalized_domain)
        normalized_candidates.append((name, normalized_domain))

    if not normalized_candidates:
        raise ValueError("At least one competitor candidate is required")

    competitors: list[Competitor] = []
    for name, domain in normalized_candidates:
        competitor = competitor_repository.get_research_competitor_by_domain(
            db,
            research_run.id,
            domain,
        )
        if competitor is None:
            competitor = competitor_repository.create_competitor(
                db,
                Competitor(
                    research_run_id=research_run.id,
                    name=name,
                    domain=domain,
                ),
            )
        competitors.append(competitor)

    return competitors


def research_competitors(
    db: Session,
    research_run: ResearchRun,
    competitor_ids: list[int],
) -> list[CompetitorResearch]:
    if research_run.input_type is None or research_run.status != ResearchRunStatus.RESOLVING:
        raise ValueError("Research input must be resolved before competitor research")

    if company_research_repository.get_by_research_run_id(db, research_run.id) is None:
        raise ValueError("Company understanding must be completed before competitor research")

    unique_ids = list(dict.fromkeys(competitor_ids))
    competitors = competitor_repository.get_by_ids(db, unique_ids)
    competitors_by_id = {competitor.id: competitor for competitor in competitors}
    if len(competitors_by_id) != len(unique_ids):
        raise ValueError("All competitor IDs must exist")
    if any(competitor.research_run_id != research_run.id for competitor in competitors):
        raise ValueError("All competitors must belong to the research run")

    existing = competitor_research_repository.get_by_competitor_ids(db, unique_ids)
    existing_by_competitor_id = {item.competitor_id: item for item in existing}
    results: list[CompetitorResearch] = []
    for competitor_id in unique_ids:
        foundation = existing_by_competitor_id.get(competitor_id)
        if foundation is None:
            foundation = competitor_research_repository.create_competitor_research(
                db,
                CompetitorResearch(
                    competitor_id=competitor_id,
                    research_run_id=research_run.id,
                ),
            )
        results.append(foundation)
    return results


def update_competitor_research(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
    updates: dict[str, str | None],
) -> CompetitorResearch:
    if research_run.input_type is None or research_run.status != ResearchRunStatus.RESOLVING:
        raise ValueError("Research input must be resolved before competitor research")

    if company_research_repository.get_by_research_run_id(db, research_run.id) is None:
        raise ValueError("Company understanding must be completed before competitor research")

    competitor = competitor_repository.get_competitor(db, competitor_id)
    if competitor is None:
        raise ValueError("Competitor not found")
    if competitor.research_run_id != research_run.id:
        raise ValueError("Competitor must belong to the research run")

    competitor_research = competitor_research_repository.get_by_competitor_id(db, competitor_id)
    if competitor_research is None:
        raise ValueError("Competitor research foundation not found")
    if not updates:
        raise ValueError("At least one research field must be supplied")

    for field, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError(f"{field} must not be empty")
        setattr(competitor_research, field, value)

    return competitor_research_repository.save_competitor_research(db, competitor_research)


def _require_competitor_research(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
) -> CompetitorResearch:
    if company_research_repository.get_by_research_run_id(db, research_run.id) is None:
        raise ValueError("Company understanding must be completed before evidence collection")

    competitor = competitor_repository.get_competitor(db, competitor_id)
    if competitor is None:
        raise ValueError("Competitor not found")
    if competitor.research_run_id != research_run.id:
        raise ValueError("Competitor must belong to the research run")

    competitor_research = competitor_research_repository.get_by_competitor_id(db, competitor_id)
    if competitor_research is None:
        raise ValueError("Competitor research foundation not found")
    return competitor_research


def create_competitor_evidence(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
    evidence_data: dict,
) -> CompetitorEvidence:
    competitor_research = _require_competitor_research(db, research_run, competitor_id)
    evidence_data["source_url"] = str(evidence_data["source_url"])
    for field in ("source_title", "source_type", "publisher"):
        value = evidence_data.get(field)
        if value is not None:
            normalized_value = value.strip()
            if not normalized_value:
                raise ValueError(f"{field} must not be empty")
            evidence_data[field] = normalized_value

    evidence = CompetitorEvidence(
        competitor_research_id=competitor_research.id,
        **evidence_data,
    )
    return competitor_evidence_repository.create_evidence(db, evidence)


def _normalize_evidence_content(content: str | None) -> str:
    if content is None:
        return ""
    normalized = unicodedata.normalize("NFKC", content).replace("\r\n", "\n").replace("\r", "\n")
    normalized = "".join(
        character
        for character in normalized
        if character in {"\n", "\t"} or not unicodedata.category(character).startswith("C")
    )
    return re.sub(r"\s+", " ", normalized).strip()


def _bounded_reason(reason: str) -> str:
    return reason[:MAX_VALIDATION_REASON_LENGTH]


def process_competitor_evidence(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
    evidence_id: int,
) -> CompetitorEvidence:
    competitor = competitor_repository.get_competitor(db, competitor_id)
    if competitor is None:
        raise LookupError("Competitor not found")
    if competitor.research_run_id != research_run.id:
        raise ValueError("Competitor must belong to the research run")
    competitor_research = _require_competitor_research(db, research_run, competitor_id)
    evidence = competitor_evidence_repository.get_evidence(db, evidence_id)
    if evidence is None:
        raise LookupError("Evidence not found")
    if evidence.competitor_research_id != competitor_research.id:
        raise ValueError("Evidence must belong to the competitor research")

    try:
        normalized_content = _normalize_evidence_content(evidence.content)
        normalized_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        evidence.normalized_content = normalized_content
        evidence.normalized_excerpt = normalized_content[:MAX_EXCERPT_LENGTH]
        evidence.normalized_content_hash = normalized_hash
        evidence.processing_error = None
        evidence.processed_at = datetime.now(timezone.utc)
        evidence.processing_status = PROCESSING_PROCESSED
        evidence.validation_status = VALIDATION_PENDING
        evidence.validation_reason = None

        if evidence.source_id is not None:
            source = evidence.source
            if source is None or source.competitor_research_id != competitor_research.id:
                evidence.validation_status = VALIDATION_INVALID
                evidence.validation_reason = _bounded_reason("Evidence source relationship is invalid")
            else:
                try:
                    canonicalize_url(evidence.source_url)
                except ValueError:
                    evidence.validation_status = VALIDATION_INVALID
                    evidence.validation_reason = _bounded_reason("Evidence source URL is invalid")
        if evidence.validation_status == VALIDATION_PENDING and not normalized_content:
            evidence.validation_status = VALIDATION_UNUSABLE
            evidence.validation_reason = _bounded_reason("Evidence content is empty")
        elif evidence.validation_status == VALIDATION_PENDING and len(normalized_content) < MIN_MEANINGFUL_CONTENT_LENGTH:
            evidence.validation_status = VALIDATION_UNUSABLE
            evidence.validation_reason = _bounded_reason("Evidence content is below the minimum meaningful length")
        elif evidence.validation_status == VALIDATION_PENDING:
            duplicate = competitor_evidence_repository.get_by_normalized_hash(
                db,
                competitor_research.id,
                normalized_hash,
                exclude_evidence_id=evidence.id,
            )
            if duplicate is not None:
                evidence.validation_status = VALIDATION_DUPLICATE
                evidence.validation_reason = _bounded_reason(f"Duplicate of evidence {duplicate.id}")
            else:
                evidence.validation_status = VALIDATION_VALID
    except UnicodeError:
        evidence.processing_status = PROCESSING_FAILED
        evidence.validation_status = VALIDATION_PENDING
        evidence.processing_error = "Evidence content could not be normalized"
        evidence.validation_reason = None
    except Exception:
        db.rollback()
        raise

    try:
        return competitor_evidence_repository.save_evidence(db, evidence)
    except Exception:
        db.rollback()
        raise


def register_competitor_source(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
    source_data: dict,
) -> tuple[CompetitorSource, bool]:
    competitor_research = _require_competitor_research(db, research_run, competitor_id)
    try:
        canonical_url = canonicalize_url(str(source_data["source_url"]))
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    for field in ("source_type", "discovery_method"):
        value = source_data.get(field)
        if value is not None:
            normalized_value = value.strip()
            if not normalized_value:
                raise ValueError(f"{field} must not be empty")
            source_data[field] = normalized_value
    if source_data.get("discovery_method") is None:
        source_data["discovery_method"] = "manual"

    existing = competitor_source_repository.get_by_canonical_url(
        db,
        competitor_research.id,
        canonical_url,
    )
    if existing is not None:
        return existing, False

    source = CompetitorSource(
        competitor_research_id=competitor_research.id,
        canonical_url=canonical_url,
        source_type=source_data.get("source_type"),
        discovery_method=source_data.get("discovery_method"),
    )
    return competitor_source_repository.create_source(db, source), True


def list_competitor_sources(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
) -> list[CompetitorSource]:
    competitor_research = _require_competitor_research(db, research_run, competitor_id)
    return competitor_source_repository.get_by_competitor_research_id(db, competitor_research.id)


def collect_competitor_source(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
    source_id: int,
) -> tuple[CompetitorSource, CompetitorEvidence]:
    competitor_research = _require_competitor_research(db, research_run, competitor_id)
    source = competitor_source_repository.get_source(db, source_id)
    if source is None:
        raise ValueError("Source not found")
    if source.competitor_research_id != competitor_research.id:
        raise ValueError("Source must belong to the competitor research")

    source.status = "fetching"
    source.attempt_count += 1
    source.last_attempted_at = datetime.now(timezone.utc)
    source.failure_category = None
    source.failure_reason = None
    competitor_source_repository.save_source(db, source)

    try:
        retrieved = source_retriever.retrieve(source.canonical_url)
    except RetrievalError as exc:
        source.status = "failed"
        source.last_http_status = exc.http_status
        source.failure_category = exc.category
        source.failure_reason = exc.reason
        competitor_source_repository.save_source(db, source)
        response_status = 502 if exc.category not in {"invalid_url", "unsafe_destination", "unsupported_scheme"} else 422
        raise SourceCollectionError(exc.category, exc.reason, response_status) from exc

    source.status = "collected"
    source.last_http_status = retrieved.http_status
    source.content_hash = retrieved.content_hash
    source.failure_category = None
    source.failure_reason = None
    competitor_source_repository.save_source(db, source)

    existing_evidence = competitor_evidence_repository.get_by_source_id(db, source.id)
    evidence = existing_evidence[0] if existing_evidence else None
    if evidence is None:
        evidence = CompetitorEvidence(
            competitor_research_id=competitor_research.id,
            source_id=source.id,
            source_url=retrieved.final_url,
            source_title=retrieved.source_title,
            source_type=source.source_type,
            retrieved_at=retrieved.retrieved_at,
            content=retrieved.content,
            content_excerpt=retrieved.content_excerpt,
        )
        evidence = competitor_evidence_repository.create_evidence(db, evidence)
    elif evidence.content != retrieved.content:
        evidence.source_url = retrieved.final_url
        evidence.source_title = retrieved.source_title
        evidence.retrieved_at = retrieved.retrieved_at
        evidence.content = retrieved.content
        evidence.content_excerpt = retrieved.content_excerpt
        evidence.processing_status = PROCESSING_PENDING
        evidence.validation_status = VALIDATION_PENDING
        evidence.processing_error = None
        evidence.validation_reason = None
        evidence.normalized_content = None
        evidence.normalized_excerpt = None
        evidence.normalized_content_hash = None
        evidence.processed_at = None
        evidence = competitor_evidence_repository.save_evidence(db, evidence)

    return source, process_competitor_evidence(db, research_run, competitor_id, evidence.id)


def list_competitor_evidence(
    db: Session,
    research_run: ResearchRun,
    competitor_id: int,
) -> list[CompetitorEvidence]:
    competitor_research = _require_competitor_research(db, research_run, competitor_id)
    return competitor_evidence_repository.list_by_competitor_research_id(
        db,
        competitor_research.id,
    )