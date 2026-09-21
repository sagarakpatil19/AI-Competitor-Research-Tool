from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx

from app.integrations.competitor_discovery_base import (
    CompetitorDiscoveryProvider,
    DiscoveryCompanyContext,
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderRateLimitError,
    DiscoveryProviderResponseError,
    DiscoveryProviderTimeoutError,
    RawDiscoveryCandidate,
)
from app.integrations.competitor_discovery_queries import build_discovery_queries


TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_PROVIDER_NAME = "tavily"
TAVILY_SEARCH_DEPTH = "basic"
TAVILY_MAX_RESULTS = 5
TAVILY_TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=10.0, write=10.0, pool=5.0)


class TavilyCompetitorDiscoveryProvider(CompetitorDiscoveryProvider):
    provider_name = TAVILY_PROVIDER_NAME

    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else self._configured_api_key()
        self.client = client
        self.timeout = timeout or TAVILY_TIMEOUT

    @staticmethod
    def _configured_api_key() -> str | None:
        from app.core.config import settings

        return settings.tavily_api_key

    def discover(self, company: DiscoveryCompanyContext) -> list[RawDiscoveryCandidate]:
        if not self.api_key or not self.api_key.strip():
            raise DiscoveryProviderAuthenticationError("Tavily API key is not configured")

        client = self.client or httpx.Client(timeout=self.timeout)
        close_client = self.client is None
        candidates: list[RawDiscoveryCandidate] = []
        try:
            for query in build_discovery_queries(company):
                payload = {
                    "query": query.query,
                    "search_depth": TAVILY_SEARCH_DEPTH,
                    "max_results": TAVILY_MAX_RESULTS,
                    "include_answer": False,
                    "include_raw_content": False,
                }
                response = self._search(client, payload)
                candidates.extend(self._parse_results(response, query.discovery_method))
            return candidates
        finally:
            if close_client:
                client.close()

    def _search(self, client: httpx.Client, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = client.post(
                TAVILY_SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise DiscoveryProviderTimeoutError("Tavily search timed out") from exc
        except httpx.ConnectError as exc:
            raise DiscoveryProviderResponseError("Tavily search was unavailable") from exc
        except httpx.TransportError as exc:
            raise DiscoveryProviderResponseError("Tavily search request failed") from exc

        if response.status_code in {401, 403}:
            raise DiscoveryProviderAuthenticationError("Tavily authentication failed")
        if response.status_code == 429:
            raise DiscoveryProviderRateLimitError("Tavily rate limit exceeded")
        if response.status_code >= 500:
            raise DiscoveryProviderResponseError("Tavily service returned an error")
        if response.status_code >= 400:
            raise DiscoveryProviderResponseError("Tavily request was rejected")

        try:
            body = response.json()
        except (TypeError, ValueError) as exc:
            raise DiscoveryProviderResponseError("Tavily returned an invalid response") from exc
        if not isinstance(body, dict) or not isinstance(body.get("results"), list):
            raise DiscoveryProviderResponseError("Tavily returned an invalid response")
        return body

    @staticmethod
    def _parse_results(
        body: dict[str, Any],
        discovery_method: str,
    ) -> list[RawDiscoveryCandidate]:
        candidates: list[RawDiscoveryCandidate] = []
        for rank, result in enumerate(body["results"], start=1):
            if not isinstance(result, dict):
                continue
            result_url = result.get("url")
            if not isinstance(result_url, str):
                continue
            parsed = urlsplit(result_url.strip())
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
                continue
            hostname = parsed.hostname.lower()
            if hostname.startswith("www."):
                hostname = hostname[4:]
            candidates.append(
                RawDiscoveryCandidate(
                    candidate_name=None,
                    candidate_url=result_url.strip(),
                    candidate_domain=hostname,
                    supporting_result_url=result_url.strip(),
                    source_title=_optional_string(result.get("title")),
                    source_snippet=_optional_string(result.get("content")),
                    provider_name=TAVILY_PROVIDER_NAME,
                    provider_result_id=_optional_string(result.get("id")),
                    provider_rank=rank,
                    discovery_method=discovery_method,
                )
            )
        return candidates


def _optional_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
