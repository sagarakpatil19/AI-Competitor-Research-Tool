from dataclasses import dataclass

from app.integrations.competitor_discovery_base import DiscoveryCompanyContext


@dataclass(frozen=True)
class DiscoveryQuery:
    query: str
    discovery_method: str


def build_discovery_queries(company: DiscoveryCompanyContext) -> list[DiscoveryQuery]:
    subject = (company.company_name or company.domain or "").strip()
    if not subject:
        return []

    queries = [
        DiscoveryQuery(f"{subject} competitors", "search_competitors"),
        DiscoveryQuery(f"{subject} alternatives", "search_alternatives"),
        DiscoveryQuery(
            f"companies similar to {subject}",
            "search_similar_companies",
        ),
    ]
    if company.industry and company.company_name:
        industry = company.industry.strip()
        if industry:
            queries.append(
                DiscoveryQuery(
                    f"{industry} companies similar to {subject}",
                    "search_industry_similar",
                )
            )

    seen: set[str] = set()
    unique_queries: list[DiscoveryQuery] = []
    for item in queries:
        normalized_query = " ".join(item.query.split())
        if normalized_query and normalized_query.casefold() not in seen:
            seen.add(normalized_query.casefold())
            unique_queries.append(
                DiscoveryQuery(normalized_query, item.discovery_method)
            )
    return unique_queries
