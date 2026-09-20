import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.company_research import CompanyResearch
from app.models.competitor import Competitor
from app.models.competitor_research import CompetitorResearch
from app.models.research_run import ResearchInputType, ResearchRun, ResearchRunStatus
from app.repositories import company_research as company_research_repository
from app.repositories import competitors as competitor_repository
from app.repositories import competitor_research as competitor_research_repository
from app.repositories import research_runs as research_run_repository


DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$",
    re.IGNORECASE,
)


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
                CompetitorResearch(competitor_id=competitor_id),
            )
        results.append(foundation)
    return results