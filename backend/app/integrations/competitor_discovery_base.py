from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DiscoveryCompanyContext:
    company_name: str | None
    domain: str | None
    industry: str | None
    description: str | None


@dataclass(frozen=True)
class RawDiscoveryCandidate:
    candidate_name: str | None
    candidate_url: str
    candidate_domain: str | None
    supporting_result_url: str
    source_title: str | None
    source_snippet: str | None
    provider_name: str
    provider_result_id: str | None
    provider_rank: int | None
    discovery_method: str


class CompetitorDiscoveryProvider(Protocol):
    def discover(self, company: DiscoveryCompanyContext) -> list[RawDiscoveryCandidate]:
        ...


class DiscoveryProviderError(Exception):
    """Base class for safe, provider-neutral discovery failures."""


class DiscoveryProviderTimeoutError(DiscoveryProviderError):
    pass


class DiscoveryProviderRateLimitError(DiscoveryProviderError):
    pass


class DiscoveryProviderAuthenticationError(DiscoveryProviderError):
    pass


class DiscoveryProviderResponseError(DiscoveryProviderError):
    pass
