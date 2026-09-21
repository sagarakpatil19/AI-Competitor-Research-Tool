import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_research import CompetitorResearch
from app.models.competitor_research_fact import CompetitorResearchFact
from app.models.competitor_research_fact_evidence import CompetitorResearchFactEvidence
from app.models.competitor_research_section import (
    CompetitorResearchSection,
    CompetitorResearchSectionName,
    CompetitorResearchSectionStatus,
)
from app.models.research_run import ResearchRun
from app.repositories import competitor_evidence as competitor_evidence_repository
from app.repositories import competitor_research_fact_evidence as fact_evidence_repository
from app.repositories import competitor_research_sections as section_repository


SECTIONS = tuple(section.value for section in CompetitorResearchSectionName)
PROCESSING_PROCESSED = "processed"
VALIDATION_VALID = "valid"

_PRICE_PATTERN = re.compile(
    r"(?P<symbol>[$\u20ac\u00a3])\s*(?P<amount>\d+(?:[.,]\d{1,2})?)"
    r"(?:\s*(?:per|/)\s*(?P<unit>user|seat|person|month|year|annual|week))?"
    r"(?:\s*(?:per|/)\s*(?P<period>user|seat|person|month|year|annual|week))?",
    re.IGNORECASE,
)
_PER_PRICE_PATTERN = re.compile(
    r"(?P<symbol>[$\u20ac\u00a3])\s*(?P<amount>\d+(?:[.,]\d{1,2})?)\s*"
    r"(?:per|/)\s*(?P<unit>user|seat|person|month|year|annual|week)",
    re.IGNORECASE,
)
_FOUNDED_PATTERN = re.compile(r"\b(?:founded|established|launched)\s+(?:in\s+)?(?P<year>18\d{2}|19\d{2}|20\d{2})\b", re.IGNORECASE)
_RATING_PATTERN = re.compile(r"\b(?P<rating>\d(?:\.\d{1,2})?)\s*(?:/\s*5|out of 5)\b", re.IGNORECASE)
_REVIEW_COUNT_PATTERN = re.compile(r"\b(?P<count>[\d,]+)\s+(?:customer\s+)?reviews?\b", re.IGNORECASE)
_LIST_PATTERN = re.compile(
    r"\b(?:offers?|provides?|includes?|supports?)\s+(?P<items>[A-Za-z0-9][^.!?;]*)",
    re.IGNORECASE,
)
_FOR_PATTERN = re.compile(r"\b(?:designed|built|made|created|intended)\s+for\s+(?P<audience>[^.!?;]+)", re.IGNORECASE)
_REVIEW_PLATFORM_PATTERN = re.compile(
    r"\b(?:on|from|via)\s+(?P<platform>G2|Capterra|Trustpilot|Google Reviews|Yelp)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _FactCandidate:
    section: str
    fact_type: str
    subject: str | None
    value_text: str | None
    value_numeric: Decimal | None
    currency: str | None
    unit: str | None
    period: str | None
    citation_excerpt: str


def _content(evidence: CompetitorEvidence) -> str:
    return (evidence.normalized_content or evidence.content or "").strip()


def _excerpt(content: str, start: int, end: int) -> str:
    sentence_start = max(content.rfind(".", 0, start), content.rfind("!", 0, start), content.rfind("?", 0, start)) + 1
    sentence_end_candidates = [position for position in (content.find(".", end), content.find("!", end), content.find("?", end)) if position >= 0]
    sentence_end = min(sentence_end_candidates, default=len(content)) + (1 if sentence_end_candidates else 0)
    return content[sentence_start:sentence_end].strip()[:1000]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ,:")


def _token(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")


def _currency(symbol: str) -> str:
    return {
        "$": "USD",
        "\u20ac": "EUR",
        "\u00a3": "GBP",
    }[symbol]


def _split_items(value: str) -> list[str]:
    value = re.sub(r"\s+and\s+", ",", value, flags=re.IGNORECASE)
    return [_clean(item) for item in value.split(",") if _clean(item)]


def _extract_company_overview_facts(content: str) -> list[_FactCandidate]:
    facts: list[_FactCandidate] = []
    for match in _FOUNDED_PATTERN.finditer(content):
        facts.append(_FactCandidate(
            "company_overview", "founded_year", None, None, Decimal(match.group("year")), None, None, None,
            _excerpt(content, match.start(), match.end()),
        ))
    return facts


def _extract_product_facts(content: str) -> list[_FactCandidate]:
    facts: list[_FactCandidate] = []
    for match in _LIST_PATTERN.finditer(content):
        if not re.match(r"offers?", match.group(0), re.IGNORECASE):
            continue
        for item in _split_items(match.group("items")):
            facts.append(_FactCandidate(
                "products", "product", item, None, None, None, None, None,
                _excerpt(content, match.start(), match.end()),
            ))
    return facts


def _extract_feature_facts(content: str) -> list[_FactCandidate]:
    facts: list[_FactCandidate] = []
    for match in _LIST_PATTERN.finditer(content):
        if not re.match(r"supports?", match.group(0), re.IGNORECASE):
            continue
        for item in _split_items(match.group("items")):
            facts.append(_FactCandidate(
                "features", "feature", item, None, None, None, None, None,
                _excerpt(content, match.start(), match.end()),
            ))
    return facts


def _extract_pricing_facts(content: str) -> list[_FactCandidate]:
    facts: list[_FactCandidate] = []
    for match in _PRICE_PATTERN.finditer(content):
        amount = Decimal(match.group("amount").replace(",", "."))
        unit = match.group("unit")
        period = match.group("period")
        if unit is None and period is not None:
            unit, period = period, None
        facts.append(_FactCandidate(
            "pricing", "starting_price" if re.search(r"starting|from|plans?", _excerpt(content, match.start(), match.end()), re.IGNORECASE) else "price",
            None, None, amount, _currency(match.group("symbol")), unit, period,
            _excerpt(content, match.start(), match.end()),
        ))
    for match in re.finditer(r"\bfree\b", content, re.IGNORECASE):
        facts.append(_FactCandidate(
            "pricing", "free_plan", None, "Free", None, None, None, None,
            _excerpt(content, match.start(), match.end()),
        ))
    return facts


def _extract_target_audience_facts(content: str) -> list[_FactCandidate]:
    return [
        _FactCandidate("target_audience", "audience", _clean(match.group("audience")), None, None, None, None, None,
                       _excerpt(content, match.start(), match.end()))
        for match in _FOR_PATTERN.finditer(content)
    ]


def _extract_customer_feedback_facts(content: str, evidence: CompetitorEvidence) -> list[_FactCandidate]:
    facts: list[_FactCandidate] = []
    for match in _REVIEW_PLATFORM_PATTERN.finditer(content):
        facts.append(_FactCandidate(
            "customer_feedback", "review_platform", _clean(match.group("platform")), None, None, None, None, None,
            _excerpt(content, match.start(), match.end()),
        ))
    for match in _REVIEW_COUNT_PATTERN.finditer(content):
        facts.append(_FactCandidate(
            "customer_feedback", "review_count", None, None, Decimal(match.group("count").replace(",", "")), None, "reviews", None,
            _excerpt(content, match.start(), match.end()),
        ))
    for match in _RATING_PATTERN.finditer(content):
        facts.append(_FactCandidate(
            "customer_feedback", "rating", None, None, Decimal(match.group("rating")), None, "rating", "5",
            _excerpt(content, match.start(), match.end()),
        ))
    if evidence.source_type and evidence.source_type.lower() in {"review", "review_site"} and not facts:
        facts.append(_FactCandidate(
            "customer_feedback", "review_source", None, evidence.source_title or evidence.source_url, None, None, None, None,
            _excerpt(content, 0, min(len(content), 160)),
        ))
    return facts


EXTRACTORS = (
    _extract_company_overview_facts,
    _extract_product_facts,
    _extract_feature_facts,
    _extract_pricing_facts,
    _extract_target_audience_facts,
)


def _extract_facts(evidence: CompetitorEvidence) -> list[_FactCandidate]:
    content = _content(evidence)
    if not content:
        return []
    facts: list[_FactCandidate] = []
    for extractor in EXTRACTORS:
        facts.extend(extractor(content))
    facts.extend(_extract_customer_feedback_facts(content, evidence))
    return facts


def _base_key(candidate: _FactCandidate) -> str:
    parts = [candidate.section, candidate.fact_type]
    if candidate.subject:
        parts.append(_token(candidate.subject))
    if candidate.unit:
        parts.append(_token(candidate.unit))
    if candidate.period:
        parts.append(_token(candidate.period))
    return ":".join(parts)


def _candidate_value(candidate: _FactCandidate) -> str:
    return ":".join(
        value for value in (
            str(candidate.value_numeric) if candidate.value_numeric is not None else None,
            _token(candidate.value_text),
            candidate.currency,
        ) if value
    )


def _fact_matches_candidate(fact: CompetitorResearchFact, candidate: _FactCandidate) -> bool:
    return (
        fact.subject == candidate.subject
        and fact.value_text == candidate.value_text
        and fact.value_numeric == candidate.value_numeric
        and fact.currency == candidate.currency
        and fact.unit == candidate.unit
        and fact.period == candidate.period
    )


def _get_or_create_fact(db: Session, execution_id: int, candidate: _FactCandidate) -> CompetitorResearchFact:
    key = _base_key(candidate)
    fact = db.scalar(select(CompetitorResearchFact).where(
        CompetitorResearchFact.competitor_research_id == execution_id,
        CompetitorResearchFact.normalized_key == key,
    ))
    if fact is not None and not _fact_matches_candidate(fact, candidate):
        key = f"{key}:value:{_token(_candidate_value(candidate))}"
        fact = db.scalar(select(CompetitorResearchFact).where(
            CompetitorResearchFact.competitor_research_id == execution_id,
            CompetitorResearchFact.normalized_key == key,
        ))
    if fact is None:
        fact = CompetitorResearchFact(
            competitor_research_id=execution_id,
            section=candidate.section,
            fact_type=candidate.fact_type,
            subject=candidate.subject,
            value_text=candidate.value_text,
            value_numeric=candidate.value_numeric,
            currency=candidate.currency,
            unit=candidate.unit,
            period=candidate.period,
            normalized_key=key,
        )
        db.add(fact)
        db.flush()
    return fact


def _ensure_sections(db: Session, execution_id: int) -> dict[str, CompetitorResearchSection]:
    sections = {
        section.section: section
        for section in section_repository.list_by_competitor_research_id(db, execution_id)
    }
    for section_name in SECTIONS:
        if section_name not in sections:
            section = CompetitorResearchSection(
                competitor_research_id=execution_id,
                section=section_name,
            )
            db.add(section)
            db.flush()
            sections[section_name] = section
    return sections


def structure_competitor_research(
    db: Session,
    research_run: ResearchRun,
    competitor_research_id: int,
) -> CompetitorResearch:
    execution = db.get(CompetitorResearch, competitor_research_id)
    if execution is None:
        raise LookupError("Competitor research execution not found")
    if execution.research_run_id != research_run.id:
        raise ValueError("Competitor research execution must belong to the research run")

    sections = _ensure_sections(db, execution.id)
    evidence_items = competitor_evidence_repository.list_by_competitor_research_id(db, execution.id)
    valid_evidence = [
        evidence for evidence in evidence_items
        if evidence.processing_status == PROCESSING_PROCESSED
        and evidence.validation_status == VALIDATION_VALID
    ]

    try:
        execution.status = "structuring"
        db.flush()
        for evidence in valid_evidence:
            for candidate in _extract_facts(evidence):
                fact = _get_or_create_fact(db, execution.id, candidate)
                if fact_evidence_repository.get_link(db, fact.id, evidence.id) is None:
                    fact_evidence_repository.create_link(
                        db,
                        CompetitorResearchFactEvidence(
                            fact_id=fact.id,
                            evidence_id=evidence.id,
                            citation_excerpt=candidate.citation_excerpt,
                        ),
                    )

        for section_name, section in sections.items():
            fact_count = db.scalar(select(func.count(CompetitorResearchFact.id)).where(
                CompetitorResearchFact.competitor_research_id == execution.id,
                CompetitorResearchFact.section == section_name,
            )) or 0
            section.fact_count = fact_count
            if fact_count:
                section.status = CompetitorResearchSectionStatus.STRUCTURED.value
                section.reason = None
            elif valid_evidence:
                section.status = CompetitorResearchSectionStatus.NO_EVIDENCE.value
                section.reason = "No deterministic structured fact was extracted from valid evidence."
            else:
                section.reason = "No valid evidence was available for structuring."

        execution.status = "completed"
        execution.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(execution)
        return execution
    except Exception:
        db.rollback()
        raise
