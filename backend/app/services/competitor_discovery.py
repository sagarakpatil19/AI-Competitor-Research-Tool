from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from app.integrations.competitor_discovery_base import (
    DiscoveryCompanyContext,
    RawDiscoveryCandidate,
)


DISCOVERY_RECEIVED = "received"
DISCOVERY_NORMALIZED = "normalized"
DISCOVERY_DUPLICATE = "duplicate"
DISCOVERY_FAILED = "failed"

VALIDATION_PENDING = "pending"
VALIDATION_VALID = "valid"
VALIDATION_INVALID = "invalid"
VALIDATION_SAME_COMPANY = "same_company"
VALIDATION_REJECTED = "rejected"
VALIDATION_PROMOTED = "promoted"

REASON_INVALID_URL = "invalid_url"
REASON_MISSING_DOMAIN = "missing_domain"
REASON_SAME_COMPANY = "same_company"
REASON_DUPLICATE_DOMAIN = "duplicate_domain"
REASON_DUPLICATE_NAME = "duplicate_name"
REASON_MISSING_CANDIDATE_IDENTITY = "missing_candidate_identity"
REASON_INVALID_PROVENANCE_URL = "invalid_provenance_url"

_HOSTNAME_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)


@dataclass(frozen=True)
class DiscoveryCandidateProvenance:
    supporting_result_url: str
    source_title: str | None
    source_snippet: str | None
    provider_name: str
    provider_result_id: str | None
    provider_rank: int | None
    discovery_method: str


@dataclass(frozen=True)
class ProcessedDiscoveryCandidate:
    candidate_name: str | None
    normalized_name: str | None
    domain: str | None
    canonical_url: str | None
    discovery_method: str
    provider_name: str
    provider_candidate_id: str | None
    provider_rank: int | None
    supporting_result_url: str | None
    source_title: str | None
    source_snippet: str | None
    discovery_status: str
    validation_status: str
    validation_reason: str | None
    supporting_sources: tuple[DiscoveryCandidateProvenance, ...] = ()
    duplicate_count: int = 0


def normalize_domain(domain: str | None) -> str | None:
    if domain is None:
        raise ValueError("Invalid domain")
    value = domain.strip().lower().rstrip(".")
    if value.startswith("www."):
        value = value[4:]
    if not value or "." not in value or len(value) > 253:
        raise ValueError("Invalid domain")
    if any(not _HOSTNAME_LABEL.fullmatch(label) for label in value.split(".")):
        raise ValueError("Invalid domain")
    return value


def normalize_url(url: str) -> tuple[str, str]:
    if not isinstance(url, str):
        raise ValueError("Invalid URL")
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except (AttributeError, ValueError) as exc:
        raise ValueError("Invalid URL") from exc
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid URL")
    hostname = parsed.hostname.lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if not hostname or any(not _HOSTNAME_LABEL.fullmatch(label) for label in hostname.split(".")):
        raise ValueError("Invalid URL")
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    normalized = urlunsplit((scheme, hostname, path, parsed.query, ""))
    return normalized, hostname.split(":", 1)[0]


def normalize_candidate_name(name: str | None) -> tuple[str | None, str | None]:
    if name is None:
        return None, None
    display_name = " ".join(name.split())
    if not display_name:
        return None, None
    return display_name, display_name.casefold()


def process_discovery_candidates(
    company: DiscoveryCompanyContext,
    candidates: list[RawDiscoveryCandidate],
) -> list[ProcessedDiscoveryCandidate]:
    company_domain = _safe_normalize_domain(company.domain)
    _, company_name = normalize_candidate_name(company.company_name)
    processed: list[ProcessedDiscoveryCandidate] = []
    by_identity: dict[tuple[str, str], int] = {}

    normalized_items = [
        _normalize_candidate(raw, company_domain, company_name)
        for raw in candidates
    ]
    normalized_items.sort(key=_candidate_sort_key)

    for item in normalized_items:
        if item.discovery_status == DISCOVERY_FAILED:
            processed.append(item)
            continue

        identity = _candidate_identity(item)
        if identity is None:
            processed.append(
                _with_status(item, DISCOVERY_FAILED, VALIDATION_INVALID, REASON_MISSING_CANDIDATE_IDENTITY)
            )
            continue
        existing_index = by_identity.get(identity)
        if existing_index is None:
            by_identity[identity] = len(processed)
            processed.append(item)
            continue

        existing = processed[existing_index]
        merged_sources = _merge_provenance(existing.supporting_sources, item.supporting_sources)
        processed[existing_index] = _replace_candidate(
            existing,
            supporting_sources=merged_sources,
            duplicate_count=existing.duplicate_count + 1,
        )

    return processed


def _candidate_sort_key(candidate: ProcessedDiscoveryCandidate) -> tuple[str, ...]:
    return (
        candidate.domain or "",
        candidate.normalized_name or "",
        candidate.canonical_url or "",
        candidate.supporting_result_url or "",
        candidate.provider_name,
        candidate.provider_candidate_id or "",
    )


def _normalize_candidate(
    raw: RawDiscoveryCandidate,
    company_domain: str | None,
    company_name: str | None,
) -> ProcessedDiscoveryCandidate:
    candidate_name, normalized_name = normalize_candidate_name(raw.candidate_name)
    try:
        canonical_url, domain = normalize_url(raw.candidate_url)
    except ValueError:
        return _failed_candidate(raw, candidate_name, normalized_name, REASON_INVALID_URL)

    try:
        supporting_url, _ = normalize_url(raw.supporting_result_url)
    except ValueError:
        return _failed_candidate(raw, candidate_name, normalized_name, REASON_INVALID_PROVENANCE_URL)

    provenance = DiscoveryCandidateProvenance(
        supporting_result_url=supporting_url,
        source_title=_clean_optional(raw.source_title),
        source_snippet=_clean_optional(raw.source_snippet),
        provider_name=raw.provider_name.strip(),
        provider_result_id=_clean_optional(raw.provider_result_id),
        provider_rank=raw.provider_rank,
        discovery_method=raw.discovery_method.strip(),
    )
    validation_status = VALIDATION_VALID
    validation_reason = None
    if not candidate_name and not domain:
        validation_status = VALIDATION_INVALID
        validation_reason = REASON_MISSING_CANDIDATE_IDENTITY
    elif company_domain and domain == company_domain:
        validation_status = VALIDATION_SAME_COMPANY
        validation_reason = REASON_SAME_COMPANY
    elif not company_domain and company_name and normalized_name == company_name:
        validation_status = VALIDATION_SAME_COMPANY
        validation_reason = REASON_SAME_COMPANY

    return ProcessedDiscoveryCandidate(
        candidate_name=candidate_name,
        normalized_name=normalized_name,
        domain=domain,
        canonical_url=canonical_url,
        discovery_method=raw.discovery_method.strip(),
        provider_name=raw.provider_name.strip(),
        provider_candidate_id=_clean_optional(raw.provider_result_id),
        provider_rank=raw.provider_rank,
        supporting_result_url=supporting_url,
        source_title=provenance.source_title,
        source_snippet=provenance.source_snippet,
        discovery_status=DISCOVERY_NORMALIZED,
        validation_status=validation_status,
        validation_reason=validation_reason,
        supporting_sources=(provenance,),
    )


def _failed_candidate(
    raw: RawDiscoveryCandidate,
    candidate_name: str | None,
    normalized_name: str | None,
    reason: str,
) -> ProcessedDiscoveryCandidate:
    return ProcessedDiscoveryCandidate(
        candidate_name=candidate_name,
        normalized_name=normalized_name,
        domain=None,
        canonical_url=None,
        discovery_method=raw.discovery_method.strip(),
        provider_name=raw.provider_name.strip(),
        provider_candidate_id=_clean_optional(raw.provider_result_id),
        provider_rank=raw.provider_rank,
        supporting_result_url=None,
        source_title=_clean_optional(raw.source_title),
        source_snippet=_clean_optional(raw.source_snippet),
        discovery_status=DISCOVERY_FAILED,
        validation_status=VALIDATION_INVALID,
        validation_reason=reason,
    )


def _candidate_identity(candidate: ProcessedDiscoveryCandidate) -> tuple[str, str] | None:
    if candidate.domain:
        return "domain", candidate.domain
    if candidate.normalized_name:
        return "name", candidate.normalized_name
    return None


def _safe_normalize_domain(domain: str | None) -> str | None:
    try:
        return normalize_domain(domain)
    except ValueError:
        return None


def _clean_optional(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _merge_provenance(
    first: tuple[DiscoveryCandidateProvenance, ...],
    second: tuple[DiscoveryCandidateProvenance, ...],
) -> tuple[DiscoveryCandidateProvenance, ...]:
    merged = {source.supporting_result_url: source for source in (*first, *second)}
    return tuple(merged[url] for url in sorted(merged))


def _replace_candidate(candidate: ProcessedDiscoveryCandidate, **changes: object) -> ProcessedDiscoveryCandidate:
    values = {
        "candidate_name": candidate.candidate_name,
        "normalized_name": candidate.normalized_name,
        "domain": candidate.domain,
        "canonical_url": candidate.canonical_url,
        "discovery_method": candidate.discovery_method,
        "provider_name": candidate.provider_name,
        "provider_candidate_id": candidate.provider_candidate_id,
        "provider_rank": candidate.provider_rank,
        "supporting_result_url": candidate.supporting_result_url,
        "source_title": candidate.source_title,
        "source_snippet": candidate.source_snippet,
        "discovery_status": candidate.discovery_status,
        "validation_status": candidate.validation_status,
        "validation_reason": candidate.validation_reason,
        "supporting_sources": candidate.supporting_sources,
        "duplicate_count": candidate.duplicate_count,
    }
    values.update(changes)
    return ProcessedDiscoveryCandidate(**values)


def _with_status(
    candidate: ProcessedDiscoveryCandidate,
    discovery_status: str,
    validation_status: str,
    validation_reason: str,
) -> ProcessedDiscoveryCandidate:
    return _replace_candidate(
        candidate,
        discovery_status=discovery_status,
        validation_status=validation_status,
        validation_reason=validation_reason,
    )
