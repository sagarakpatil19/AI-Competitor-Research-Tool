import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.company_research import CompanyResearch
from app.models.research_run import ResearchInputType, ResearchRun, ResearchRunStatus
from app.repositories import company_research as company_research_repository
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