from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.session import SessionLocal
from app.integrations.source_retriever import RetrievedSource
from app.models.competitor import Competitor
from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_source import CompetitorSource
from app.models.research_run import ResearchRun
from app.services import research as research_service


def test_create_research_run(client):
    response = client.post("/api/research", json={"company": "notion.so"})

    assert response.status_code == 201
    body = response.json()
    assert body["research_id"]
    assert body["input_value"] == "notion.so"
    assert body["status"] == "submitted"
    assert body["input_type"] is None
    assert body["resolved_domain"] is None
    assert body["created_at"]
    assert body["updated_at"]


def test_create_research_run_rejects_empty_input(client):
    response = client.post("/api/research", json={"company": "   "})

    assert response.status_code == 422


def test_get_research_run(client):
    created = client.post("/api/research", json={"company": "Acme"}).json()

    response = client.get(f"/api/research/{created['research_id']}")

    assert response.status_code == 200
    assert response.json()["research_id"] == created["research_id"]
    assert response.json()["status"] == "submitted"


def test_get_nonexistent_research_run_returns_not_found(client):
    response = client.get("/api/research/999999")

    assert response.status_code == 404


def test_new_research_run_starts_submitted(client):
    response = client.post("/api/research", json={"company": "Example Company"})

    assert response.json()["status"] == "submitted"


def test_resolve_url(client):
    created = client.post(
        "/api/research",
        json={"company": "https://www.notion.so/product"},
    ).json()

    response = client.post(f"/api/research/{created['research_id']}/resolve")

    assert response.status_code == 200
    assert response.json()["input_type"] == "url"
    assert response.json()["resolved_domain"] == "notion.so"
    assert response.json()["status"] == "resolving"
    assert response.json()["input_value"] == "https://www.notion.so/product"


def test_resolve_domain(client):
    created = client.post("/api/research", json={"company": "notion.so"}).json()

    response = client.post(f"/api/research/{created['research_id']}/resolve")

    assert response.status_code == 200
    assert response.json()["input_type"] == "domain"
    assert response.json()["resolved_domain"] == "notion.so"
    assert response.json()["status"] == "resolving"


def test_resolve_www_url(client):
    created = client.post(
        "/api/research",
        json={"company": "https://www.notion.so"},
    ).json()

    response = client.post(f"/api/research/{created['research_id']}/resolve")

    assert response.json()["resolved_domain"] == "notion.so"


def test_resolve_company_name(client):
    created = client.post("/api/research", json={"company": "Notion"}).json()

    response = client.post(f"/api/research/{created['research_id']}/resolve")

    assert response.status_code == 200
    assert response.json()["input_type"] == "company_name"
    assert response.json()["resolved_domain"] is None
    assert response.json()["status"] == "resolving"


def test_resolve_nonexistent_research_run_returns_not_found(client):
    response = client.post("/api/research/999999/resolve")

    assert response.status_code == 404


def test_understand_company_creates_foundation(client):
    created = client.post(
        "/api/research",
        json={"company": "https://www.notion.so/product"},
    ).json()
    client.post(f"/api/research/{created['research_id']}/resolve")

    response = client.post(f"/api/research/{created['research_id']}/understand")

    assert response.status_code == 200
    body = response.json()
    assert body["research"]["research_id"] == created["research_id"]
    assert body["research"]["status"] == "resolving"
    assert body["company_research"]["research_run_id"] == created["research_id"]
    assert body["company_research"]["domain"] == "notion.so"
    assert body["company_research"]["company_name"] is None
    assert body["company_research"]["description"] is None
    assert body["company_research"]["industry"] is None


def test_understand_company_name_without_domain(client):
    created = client.post("/api/research", json={"company": "Notion"}).json()
    client.post(f"/api/research/{created['research_id']}/resolve")

    response = client.post(f"/api/research/{created['research_id']}/understand")

    assert response.status_code == 200
    assert response.json()["company_research"]["company_name"] == "Notion"
    assert response.json()["company_research"]["domain"] is None
    assert response.json()["research"]["status"] == "resolving"


def test_understand_unresolved_research_run_is_rejected(client):
    created = client.post("/api/research", json={"company": "notion.so"}).json()

    response = client.post(f"/api/research/{created['research_id']}/understand")

    assert response.status_code == 422


def test_understand_nonexistent_research_run_returns_not_found(client):
    response = client.post("/api/research/999999/understand")

    assert response.status_code == 404


def resolve_and_understand(client, company="Notion"):
    created = client.post("/api/research", json={"company": company}).json()
    client.post(f"/api/research/{created['research_id']}/resolve")
    client.post(f"/api/research/{created['research_id']}/understand")
    return created


def test_discover_competitors_creates_foundation(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["research"]["research_id"] == research["research_id"]
    assert body["research"]["status"] == "resolving"
    assert len(body["competitors"]) == 1
    assert body["competitors"][0]["research_run_id"] == research["research_id"]
    assert body["competitors"][0]["name"] == "Slack"
    assert body["competitors"][0]["domain"] == "slack.com"


def test_discover_competitors_supports_multiple_candidates(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={
            "competitors": [
                {"name": "Slack", "domain": "slack.com"},
                {"name": "Evernote", "domain": "evernote.com"},
            ]
        },
    )

    assert response.status_code == 200
    assert [item["domain"] for item in response.json()["competitors"]] == [
        "slack.com",
        "evernote.com",
    ]


def test_discover_competitors_normalizes_domain(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": " WWW.SLACK.COM. "}]},
    )

    assert response.status_code == 200
    assert response.json()["competitors"][0]["domain"] == "slack.com"


def test_discover_competitors_deduplicates_candidates(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={
            "competitors": [
                {"name": "Slack", "domain": "slack.com"},
                {"name": "Slack duplicate", "domain": "WWW.SLACK.COM"},
            ]
        },
    )

    assert response.status_code == 200
    assert len(response.json()["competitors"]) == 1


def test_discover_competitors_deduplicates_existing_record(client):
    research = resolve_and_understand(client)
    endpoint = f"/api/research/{research['research_id']}/discover"
    payload = {"competitors": [{"name": "Slack", "domain": "slack.com"}]}

    first = client.post(endpoint, json=payload)
    second = client.post(endpoint, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["competitors"][0]["id"] == first.json()["competitors"][0]["id"]


def test_discover_competitors_rejects_empty_list(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": []},
    )

    assert response.status_code == 422


def test_discover_competitors_rejects_missing_name(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"domain": "slack.com"}]},
    )

    assert response.status_code == 422


def test_discover_competitors_rejects_missing_domain(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack"}]},
    )

    assert response.status_code == 422


def test_discover_competitors_rejects_unresolved_research_run(client):
    research = client.post("/api/research", json={"company": "Notion"}).json()

    response = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    )

    assert response.status_code == 422


def test_discover_nonexistent_research_run_returns_not_found(client):
    response = client.post(
        "/api/research/999999/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    )

    assert response.status_code == 404


def test_research_competitors_creates_foundations(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={
            "competitors": [
                {"name": "Slack", "domain": "slack.com"},
                {"name": "Evernote", "domain": "evernote.com"},
            ]
        },
    ).json()
    competitor_ids = [item["id"] for item in discovered["competitors"]]

    response = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": competitor_ids},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["research"]["research_id"] == research["research_id"]
    assert body["research"]["status"] == "resolving"
    assert [item["competitor_id"] for item in body["competitor_research"]] == competitor_ids
    assert all(item["description"] is None for item in body["competitor_research"])
    assert all(item["industry"] is None for item in body["competitor_research"])
    assert all(item["products_services"] is None for item in body["competitor_research"])
    assert all(item["target_customers"] is None for item in body["competitor_research"])
    assert all(item["business_model"] is None for item in body["competitor_research"])


def test_research_competitors_deduplicates_ids(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    ).json()
    competitor_id = discovered["competitors"][0]["id"]

    response = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": [competitor_id, competitor_id]},
    )

    assert response.status_code == 200
    assert len(response.json()["competitor_research"]) == 1


def test_research_competitors_reuses_existing_foundation(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    ).json()
    competitor_id = discovered["competitors"][0]["id"]
    endpoint = f"/api/research/{research['research_id']}/research"

    first = client.post(endpoint, json={"competitor_ids": [competitor_id]}).json()
    second = client.post(endpoint, json={"competitor_ids": [competitor_id]}).json()

    assert second["competitor_research"][0]["id"] == first["competitor_research"][0]["id"]


def test_research_competitors_rejects_empty_ids(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": []},
    )

    assert response.status_code == 422


def test_research_competitors_rejects_nonexistent_competitor(client):
    research = resolve_and_understand(client)

    response = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": [999999]},
    )

    assert response.status_code == 422


def test_research_competitors_rejects_competitor_from_another_run(client):
    first_research = resolve_and_understand(client, "Notion")
    second_research = resolve_and_understand(client, "Acme")
    discovered = client.post(
        f"/api/research/{first_research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    ).json()
    competitor_id = discovered["competitors"][0]["id"]

    response = client.post(
        f"/api/research/{second_research['research_id']}/research",
        json={"competitor_ids": [competitor_id]},
    )

    assert response.status_code == 422


def test_research_competitors_rejects_missing_company_research(client):
    research = client.post("/api/research", json={"company": "Notion"}).json()
    client.post(f"/api/research/{research['research_id']}/resolve")

    db = SessionLocal()
    try:
        competitor = Competitor(
            research_run_id=research["research_id"],
            name="Slack",
            domain="slack.com",
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
    finally:
        db.close()

    discovered = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": [competitor.id]},
    )

    assert discovered.status_code == 422


def test_research_competitors_rejects_missing_research_run(client):
    response = client.post(
        "/api/research/999999/research",
        json={"competitor_ids": [1]},
    )

    assert response.status_code == 404


def create_competitor_research_foundation(client, company="Notion"):
    research = resolve_and_understand(client, company)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    ).json()
    competitor_id = discovered["competitors"][0]["id"]
    researched = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": [competitor_id]},
    )
    assert researched.status_code == 200
    foundation = researched.json()["competitor_research"][0]
    return research, competitor_id, foundation


def test_update_competitor_research_full_payload(client):
    research, competitor_id, foundation = create_competitor_research_foundation(client)
    payload = {
        "description": "Project management and collaboration platform",
        "industry": "Software / Productivity",
        "products_services": "Project management, team collaboration, task tracking",
        "target_customers": "Teams and organizations",
        "business_model": "Subscription SaaS",
    }

    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["research"]["status"] == "resolving"
    assert body["competitor_research"]["id"] == foundation["id"]
    assert body["competitor_research"]["competitor_id"] == competitor_id
    for field, value in payload.items():
        assert body["competitor_research"][field] == value


def test_update_competitor_research_partial_payload_preserves_other_fields(client):
    research, competitor_id, _ = create_competitor_research_foundation(client)
    client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research",
        json={
            "description": "Existing description",
            "industry": "Existing industry",
        },
    )

    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research",
        json={"industry": "Updated industry"},
    )

    assert response.status_code == 200
    body = response.json()["competitor_research"]
    assert body["description"] == "Existing description"
    assert body["industry"] == "Updated industry"
    assert body["products_services"] is None


def test_update_competitor_research_supports_sequential_updates(client):
    research, competitor_id, foundation = create_competitor_research_foundation(client)
    endpoint = f"/api/research/{research['research_id']}/competitors/{competitor_id}/research"

    first = client.patch(endpoint, json={"industry": "Productivity"}).json()
    second = client.patch(endpoint, json={"business_model": "Subscription"}).json()

    assert first["competitor_research"]["id"] == foundation["id"]
    assert second["competitor_research"]["id"] == foundation["id"]
    assert second["competitor_research"]["industry"] == "Productivity"
    assert second["competitor_research"]["business_model"] == "Subscription"


def test_update_competitor_research_preserves_ids_and_timestamps(client):
    research, competitor_id, foundation = create_competitor_research_foundation(client)
    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research",
        json={"industry": "Productivity"},
    )

    body = response.json()
    assert body["competitor_research"]["id"] == foundation["id"]
    assert body["competitor_research"]["competitor_id"] == competitor_id
    assert body["competitor_research"]["created_at"] == foundation["created_at"]
    assert body["competitor_research"]["updated_at"]


def test_update_competitor_research_rejects_missing_research_run(client):
    response = client.patch(
        "/api/research/999999/competitors/1/research",
        json={"industry": "Productivity"},
    )

    assert response.status_code == 404


def test_update_competitor_research_rejects_missing_company_research(client):
    research = client.post("/api/research", json={"company": "Notion"}).json()
    client.post(f"/api/research/{research['research_id']}/resolve")
    db = SessionLocal()
    try:
        competitor = Competitor(
            research_run_id=research["research_id"],
            name="Slack",
            domain="slack.com",
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
    finally:
        db.close()

    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor.id}/research",
        json={"industry": "Productivity"},
    )

    assert response.status_code == 422


def test_update_competitor_research_rejects_missing_competitor(client):
    research, _, _ = create_competitor_research_foundation(client)

    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/999999/research",
        json={"industry": "Productivity"},
    )

    assert response.status_code == 422


def test_update_competitor_research_rejects_competitor_from_another_run(client):
    first_research, competitor_id, _ = create_competitor_research_foundation(client, "Notion")
    second_research, _, _ = create_competitor_research_foundation(client, "Acme")

    response = client.patch(
        f"/api/research/{second_research['research_id']}/competitors/{competitor_id}/research",
        json={"industry": "Productivity"},
    )

    assert first_research["research_id"] != second_research["research_id"]
    assert response.status_code == 422


def test_update_competitor_research_rejects_missing_foundation(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    ).json()
    competitor_id = discovered["competitors"][0]["id"]

    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research",
        json={"industry": "Productivity"},
    )

    assert response.status_code == 422


def test_update_competitor_research_rejects_empty_update(client):
    research, competitor_id, _ = create_competitor_research_foundation(client)

    response = client.patch(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research",
        json={},
    )

    assert response.status_code == 422


def create_evidence_foundation(client, company="Notion"):
    research, competitor_id, foundation = create_competitor_research_foundation(client, company)
    endpoint = f"/api/research/{research['research_id']}/competitors/{competitor_id}/research/evidence"
    return research, competitor_id, foundation, endpoint


def test_create_evidence_persists_source_and_content(client):
    research, competitor_id, foundation, endpoint = create_evidence_foundation(client)
    payload = {
        "source_url": "https://example.com/article",
        "source_title": "Example Article",
        "source_type": "article",
        "publisher": "Example Publisher",
        "published_at": "2026-09-20T12:00:00Z",
        "retrieved_at": "2026-09-21T12:00:00Z",
        "content": "Observed source content.",
        "content_excerpt": "Relevant excerpt.",
    }

    response = client.post(endpoint, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["research"]["research_id"] == research["research_id"]
    assert body["research"]["status"] == "resolving"
    assert set(body) == {"research", "evidence"}
    evidence = body["evidence"]
    assert evidence["competitor_research_id"] == foundation["id"]
    assert evidence["source_url"] == "https://example.com/article"
    assert evidence["source_title"] == "Example Article"
    assert evidence["source_type"] == "article"
    assert evidence["publisher"] == "Example Publisher"
    assert evidence["content"] == "Observed source content."
    assert evidence["content_excerpt"] == "Relevant excerpt."
    assert evidence["id"]
    assert evidence["created_at"]
    assert evidence["updated_at"]


def test_list_evidence_returns_records_for_competitor_research(client):
    research, _, foundation, endpoint = create_evidence_foundation(client)
    client.post(endpoint, json={"source_url": "https://example.com/one"})
    client.post(endpoint, json={"source_url": "https://example.com/two"})

    response = client.get(endpoint)

    assert response.status_code == 200
    body = response.json()
    assert body["research"]["research_id"] == research["research_id"]
    assert body["research"]["status"] == "resolving"
    assert len(body["evidence"]) == 2
    assert all(item["competitor_research_id"] == foundation["id"] for item in body["evidence"])


def test_evidence_metadata_whitespace_is_trimmed(client):
    _, _, _, endpoint = create_evidence_foundation(client)

    response = client.post(
        endpoint,
        json={
            "source_url": "https://example.com/article",
            "source_title": "  Example Title  ",
            "source_type": "  article  ",
            "publisher": "  Example Publisher  ",
        },
    )

    assert response.status_code == 201
    evidence = response.json()["evidence"]
    assert evidence["source_title"] == "Example Title"
    assert evidence["source_type"] == "article"
    assert evidence["publisher"] == "Example Publisher"


def test_evidence_rejects_empty_or_invalid_source_url(client):
    _, _, _, endpoint = create_evidence_foundation(client)

    empty_response = client.post(endpoint, json={"source_url": "   "})
    invalid_response = client.post(endpoint, json={"source_url": "ftp://example.com/file"})

    assert empty_response.status_code == 422
    assert invalid_response.status_code == 422


def test_evidence_requires_source_url(client):
    _, _, _, endpoint = create_evidence_foundation(client)

    response = client.post(endpoint, json={"source_title": "Missing URL"})

    assert response.status_code == 422


def test_evidence_rejects_empty_optional_metadata(client):
    _, _, _, endpoint = create_evidence_foundation(client)

    response = client.post(
        endpoint,
        json={"source_url": "https://example.com", "publisher": "   "},
    )

    assert response.status_code == 422


def test_new_evidence_is_pending_and_processing_exposes_structured_fields(client):
    research, competitor_id, _, endpoint = create_evidence_foundation(client)
    created = client.post(
        endpoint,
        json={"source_url": "https://example.com", "content": "Pending raw content"},
    )

    assert created.status_code == 201
    evidence = created.json()["evidence"]
    assert evidence["processing_status"] == "pending"
    assert evidence["validation_status"] == "pending"
    assert evidence["normalized_content"] is None

    process_endpoint = f"{endpoint}/{evidence['id']}/process"
    processed = client.post(process_endpoint)

    assert processed.status_code == 200
    result = processed.json()["evidence"]
    assert result["competitor_research_id"]
    assert result["processing_status"] == "processed"
    assert result["validation_status"] == "unusable"
    assert result["processed_at"]
    assert research["research_id"]
    assert competitor_id


def test_processing_normalizes_content_and_hashes_deterministically(client):
    _, _, _, endpoint = create_evidence_foundation(client)
    raw_content = "  Product\r\n\tstrategy\x00 with   useful punctuation!  " + ("x" * 40)
    created = client.post(endpoint, json={"source_url": "https://example.com", "content": raw_content})
    evidence_id = created.json()["evidence"]["id"]

    first = client.post(f"{endpoint}/{evidence_id}/process").json()["evidence"]
    second = client.post(f"{endpoint}/{evidence_id}/process").json()["evidence"]

    assert first["normalized_content"] == "Product strategy with useful punctuation! " + ("x" * 40)
    assert first["normalized_content_hash"] == second["normalized_content_hash"]
    assert first["normalized_content"] == second["normalized_content"]
    assert first["normalized_excerpt"] == first["normalized_content"][:1000]
    assert first["validation_status"] == "valid"


@pytest.mark.parametrize("content", ["", "   \r\n\t", "short content"])
def test_processing_marks_empty_and_below_threshold_content_unusable(client, content):
    _, _, _, endpoint = create_evidence_foundation(client)
    created = client.post(endpoint, json={"source_url": "https://example.com", "content": content})
    evidence_id = created.json()["evidence"]["id"]

    response = client.post(f"{endpoint}/{evidence_id}/process")

    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert evidence["processing_status"] == "processed"
    assert evidence["validation_status"] == "unusable"
    assert evidence["validation_reason"]


def test_processing_marks_duplicate_only_within_competitor_research(client):
    _, _, _, endpoint = create_evidence_foundation(client)
    content = "This is sufficiently meaningful evidence content for validation."
    first = client.post(endpoint, json={"source_url": "https://example.com/one", "content": content})
    second = client.post(endpoint, json={"source_url": "https://example.com/two", "content": content})

    assert client.post(f"{endpoint}/{first.json()['evidence']['id']}/process").json()["evidence"]["validation_status"] == "valid"
    duplicate = client.post(f"{endpoint}/{second.json()['evidence']['id']}/process")

    assert duplicate.status_code == 200
    assert duplicate.json()["evidence"]["validation_status"] == "duplicate"


def test_same_content_is_allowed_for_different_competitors(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={
            "competitors": [
                {"name": "Slack", "domain": "slack.com"},
                {"name": "Evernote", "domain": "evernote.com"},
            ],
        },
    ).json()
    competitor_ids = [item["id"] for item in discovered["competitors"]]
    client.post(f"/api/research/{research['research_id']}/research", json={"competitor_ids": competitor_ids})
    content = "The same source-backed evidence is valid for this separate competitor."
    endpoints = [
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research/evidence"
        for competitor_id in competitor_ids
    ]
    first = client.post(endpoints[0], json={"source_url": "https://example.com", "content": content}).json()["evidence"]
    second = client.post(endpoints[1], json={"source_url": "https://example.com", "content": content}).json()["evidence"]

    first_processed = client.post(f"{endpoints[0]}/{first['id']}/process").json()["evidence"]
    second_processed = client.post(f"{endpoints[1]}/{second['id']}/process").json()["evidence"]

    assert first_processed["validation_status"] == "valid"
    assert second_processed["validation_status"] == "valid"


def test_processing_marks_invalid_source_relationship(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={
            "competitors": [
                {"name": "Slack", "domain": "slack.com"},
                {"name": "Evernote", "domain": "evernote.com"},
            ],
        },
    ).json()
    competitor_ids = [item["id"] for item in discovered["competitors"]]
    foundations = client.post(
        f"/api/research/{research['research_id']}/research",
        json={"competitor_ids": competitor_ids},
    ).json()["competitor_research"]
    source_endpoint = f"/api/research/{research['research_id']}/competitors/{competitor_ids[1]}/research/sources"
    source = client.post(source_endpoint, json={"source_url": "https://example.com"}).json()["source"]
    db = SessionLocal()
    try:
        evidence = CompetitorEvidence(
            competitor_research_id=foundations[0]["id"],
            source_id=source["id"],
            source_url="https://example.com",
            content="This evidence has enough meaningful content to validate.",
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        evidence_id = evidence.id
    finally:
        db.close()

    process_endpoint = (
        f"/api/research/{research['research_id']}/competitors/{competitor_ids[0]}"
        f"/research/evidence/{evidence_id}/process"
    )
    response = client.post(process_endpoint)

    assert response.status_code == 200
    assert response.json()["evidence"]["validation_status"] == "invalid"


def test_processing_rejects_missing_and_cross_research_evidence(client):
    research, competitor_id, _, endpoint = create_evidence_foundation(client)
    missing = client.post(f"{endpoint}/999999/process")
    assert missing.status_code == 404

    other_research, other_competitor_id, _, other_endpoint = create_evidence_foundation(client, "Acme")
    created = client.post(other_endpoint, json={"source_url": "https://example.com", "content": "Evidence for another research run."})
    cross_endpoint = f"{endpoint}/{created.json()['evidence']['id']}/process"
    cross = client.post(cross_endpoint)

    assert cross.status_code == 422
    assert research["research_id"] != other_research["research_id"]
    assert competitor_id != other_competitor_id


def test_processing_failure_persists_and_can_be_retried(client, monkeypatch):
    _, _, _, endpoint = create_evidence_foundation(client)
    created = client.post(
        endpoint,
        json={"source_url": "https://example.com", "content": "This content is long enough to process successfully."},
    )
    evidence_id = created.json()["evidence"]["id"]
    monkeypatch.setattr(
        research_service,
        "_normalize_evidence_content",
        lambda content: (_ for _ in ()).throw(UnicodeError("normalizer failed")),
    )

    failed = client.post(f"{endpoint}/{evidence_id}/process")
    assert failed.status_code == 200
    assert failed.json()["evidence"]["processing_status"] == "failed"
    assert failed.json()["evidence"]["validation_status"] == "pending"
    assert failed.json()["evidence"]["processing_error"] == "Evidence content could not be normalized"

    monkeypatch.undo()
    retried = client.post(f"{endpoint}/{evidence_id}/process")
    assert retried.json()["evidence"]["processing_status"] == "processed"
    assert retried.json()["evidence"]["validation_status"] == "valid"


def test_evidence_rejects_missing_research_run(client):
    response = client.post(
        "/api/research/999999/competitors/1/research/evidence",
        json={"source_url": "https://example.com"},
    )

    assert response.status_code == 404


def test_evidence_rejects_missing_company_research(client):
    research = client.post("/api/research", json={"company": "Notion"}).json()
    client.post(f"/api/research/{research['research_id']}/resolve")
    db = SessionLocal()
    try:
        competitor = Competitor(
            research_run_id=research["research_id"],
            name="Slack",
            domain="slack.com",
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
    finally:
        db.close()

    response = client.post(
        f"/api/research/{research['research_id']}/competitors/{competitor.id}/research/evidence",
        json={"source_url": "https://example.com"},
    )

    assert response.status_code == 422


def test_evidence_rejects_missing_competitor(client):
    research, _, _, _ = create_evidence_foundation(client)

    response = client.post(
        f"/api/research/{research['research_id']}/competitors/999999/research/evidence",
        json={"source_url": "https://example.com"},
    )

    assert response.status_code == 422


def test_evidence_rejects_cross_run_competitor(client):
    first_research, first_competitor_id, _, _ = create_evidence_foundation(client, "Notion")
    second_research, _, _, second_endpoint = create_evidence_foundation(client, "Acme")

    cross_run_endpoint = (
        f"/api/research/{second_research['research_id']}/competitors/"
        f"{first_competitor_id}/research/evidence"
    )
    response = client.post(cross_run_endpoint, json={"source_url": "https://example.com"})

    assert first_research["research_id"] != second_research["research_id"]
    assert second_endpoint != cross_run_endpoint
    assert response.status_code == 422


def test_evidence_rejects_missing_competitor_research(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={"competitors": [{"name": "Slack", "domain": "slack.com"}]},
    ).json()
    competitor_id = discovered["competitors"][0]["id"]

    response = client.post(
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research/evidence",
        json={"source_url": "https://example.com"},
    )

    assert response.status_code == 422


def create_source_foundation(client, company="Notion"):
    research, competitor_id, foundation = create_competitor_research_foundation(client, company)
    endpoint = f"/api/research/{research['research_id']}/competitors/{competitor_id}/research/sources"
    return research, competitor_id, foundation, endpoint


def test_register_http_source(client):
    research, competitor_id, foundation, endpoint = create_source_foundation(client)

    response = client.post(
        endpoint,
        json={
            "source_url": "http://example.com/article",
            "source_type": "article",
            "discovery_method": "manual",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["research"]["research_id"] == research["research_id"]
    assert body["source"]["competitor_research_id"] == foundation["id"]
    assert body["source"]["canonical_url"] == "http://example.com/article"
    assert body["source"]["status"] == "discovered"
    assert body["source"]["attempt_count"] == 0
    assert competitor_id


def test_register_source_canonicalizes_and_deduplicates(client):
    _, _, _, endpoint = create_source_foundation(client)
    first = client.post(endpoint, json={"source_url": "HTTPS://Example.COM:443/article#section"})
    second = client.post(endpoint, json={"source_url": "https://example.com/article"})

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["source"]["id"] == second.json()["source"]["id"]
    assert second.json()["source"]["canonical_url"] == "https://example.com/article"


def test_register_source_allows_same_url_for_different_competitors(client):
    research = resolve_and_understand(client)
    discovered = client.post(
        f"/api/research/{research['research_id']}/discover",
        json={
            "competitors": [
                {"name": "Slack", "domain": "slack.com"},
                {"name": "Evernote", "domain": "evernote.com"},
            ]
        },
    ).json()
    competitor_ids = [item["id"] for item in discovered["competitors"]]
    client.post(f"/api/research/{research['research_id']}/research", json={"competitor_ids": competitor_ids})
    endpoints = [
        f"/api/research/{research['research_id']}/competitors/{competitor_id}/research/sources"
        for competitor_id in competitor_ids
    ]

    first = client.post(endpoints[0], json={"source_url": "https://example.com"})
    second = client.post(endpoints[1], json={"source_url": "https://example.com"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["source"]["id"] != second.json()["source"]["id"]


def test_list_sources_is_ordered_and_scoped(client):
    research, _, foundation, endpoint = create_source_foundation(client)
    client.post(endpoint, json={"source_url": "https://example.com/b"})
    client.post(endpoint, json={"source_url": "https://example.com/a"})

    response = client.get(endpoint)

    assert response.status_code == 200
    assert [item["canonical_url"] for item in response.json()["sources"]] == [
        "https://example.com/b",
        "https://example.com/a",
    ]
    assert all(item["competitor_research_id"] == foundation["id"] for item in response.json()["sources"])
    assert response.json()["research"]["status"] == "resolving"


def test_register_source_rejects_invalid_url(client):
    _, _, _, endpoint = create_source_foundation(client)

    empty = client.post(endpoint, json={"source_url": "   "})
    ftp = client.post(endpoint, json={"source_url": "ftp://example.com/file"})

    assert empty.status_code == 422
    assert ftp.status_code == 422


class FakeSourceRetriever:
    def retrieve(self, url: str) -> RetrievedSource:
        content = "Example collected content"
        return RetrievedSource(
            final_url=url,
            http_status=200,
            content_type="text/plain",
            content=content,
            content_excerpt=content,
            content_hash="a" * 64,
            retrieved_at=datetime.now(timezone.utc),
            source_title="Collected title",
        )


def test_collect_source_creates_evidence_and_updates_state(client, monkeypatch):
    research, competitor_id, foundation, endpoint = create_source_foundation(client)
    registered = client.post(endpoint, json={"source_url": "https://example.com/article"}).json()["source"]
    monkeypatch.setattr(research_service, "source_retriever", FakeSourceRetriever())

    response = client.post(
        f"{endpoint}/{registered['id']}/collect"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["research"]["status"] == "resolving"
    assert body["source"]["status"] == "collected"
    assert body["source"]["attempt_count"] == 1
    assert body["source"]["last_http_status"] == 200
    assert body["source"]["content_hash"] == "a" * 64
    assert body["evidence"]["source_id"] == registered["id"]
    assert body["evidence"]["competitor_research_id"] == foundation["id"]
    assert body["evidence"]["content"] == "Example collected content"
    assert competitor_id


def test_repeated_identical_source_collection_reuses_evidence(client, monkeypatch):
    _, competitor_id, _, endpoint = create_source_foundation(client)
    registered = client.post(endpoint, json={"source_url": "https://example.com/article"}).json()["source"]
    monkeypatch.setattr(research_service, "source_retriever", FakeSourceRetriever())
    collect_endpoint = f"{endpoint}/{registered['id']}/collect"

    first = client.post(collect_endpoint)
    second = client.post(collect_endpoint)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["evidence"]["id"] == second.json()["evidence"]["id"]
    db = SessionLocal()
    try:
        evidence = list(
            db.scalars(
                select(CompetitorEvidence).where(
                    CompetitorEvidence.source_id == registered["id"]
                )
            ).all()
        )
    finally:
        db.close()
    assert len(evidence) == 1
    assert competitor_id


def test_changed_source_content_reprocesses_existing_evidence(client, monkeypatch):
    _, _, _, endpoint = create_source_foundation(client)
    registered = client.post(endpoint, json={"source_url": "https://example.com/article"}).json()["source"]

    class ChangingRetriever:
        content = "Initial source content that is sufficiently meaningful for validation."

        def retrieve(self, url: str) -> RetrievedSource:
            return RetrievedSource(
                final_url=url,
                http_status=200,
                content_type="text/plain",
                content=self.content,
                content_excerpt=self.content[:1000],
                content_hash="a" * 64,
                retrieved_at=datetime.now(timezone.utc),
            )

    retriever = ChangingRetriever()
    monkeypatch.setattr(research_service, "source_retriever", retriever)
    collect_endpoint = f"{endpoint}/{registered['id']}/collect"
    first = client.post(collect_endpoint).json()["evidence"]
    retriever.content = "Changed source content that is also sufficiently meaningful for validation."
    second = client.post(collect_endpoint).json()["evidence"]

    assert first["id"] == second["id"]
    assert second["content"] != first["content"]
    assert second["processing_status"] == "processed"
    assert second["validation_status"] == "valid"


def test_collect_source_rejects_cross_competitor_source(client):
    first_research, first_competitor_id, _, first_endpoint = create_source_foundation(client, "Notion")
    second_research, _, _, _ = create_source_foundation(client, "Acme")
    registered = client.post(first_endpoint, json={"source_url": "https://example.com"}).json()["source"]

    response = client.post(
        f"/api/research/{second_research['research_id']}/competitors/{first_competitor_id}/research/sources/{registered['id']}/collect"
    )

    assert first_research["research_id"] != second_research["research_id"]
    assert response.status_code == 422


def test_collect_source_failure_persists_failed_state_without_evidence(client, monkeypatch):
    from app.integrations.source_retriever import RetrievalError

    _, _, _, endpoint = create_source_foundation(client)
    registered = client.post(endpoint, json={"source_url": "https://example.com"}).json()["source"]

    class FailedRetriever:
        def retrieve(self, url: str) -> RetrievedSource:
            raise RetrievalError("timeout", "Source request timed out")

    monkeypatch.setattr(research_service, "source_retriever", FailedRetriever())
    response = client.post(f"{endpoint}/{registered['id']}/collect")

    assert response.status_code == 502
    assert response.json()["detail"] == "Source request timed out"

    db = SessionLocal()
    try:
        source = db.get(CompetitorSource, registered["id"])
        evidence = list(
            db.scalars(
                select(CompetitorEvidence).where(CompetitorEvidence.source_id == registered["id"])
            ).all()
        )
    finally:
        db.close()

    assert source is not None
    assert source.status == "failed"
    assert source.attempt_count == 1
    assert source.last_attempted_at is not None
    assert source.failure_category == "timeout"
    assert source.failure_reason == "Source request timed out"
    assert source.last_http_status is None
    assert evidence == []


@pytest.mark.parametrize(
    ("status_code", "category"),
    [(404, "http_4xx"), (403, "http_4xx"), (500, "http_5xx"), (503, "http_5xx")],
)
def test_collect_source_persists_http_failure_state(client, monkeypatch, status_code, category):
    _, _, _, endpoint = create_source_foundation(client)
    registered = client.post(endpoint, json={"source_url": "https://example.com"}).json()["source"]

    class HttpFailureRetriever:
        def retrieve(self, url: str) -> RetrievedSource:
            from app.integrations.source_retriever import RetrievalError

            raise RetrievalError(category, f"Source returned HTTP {status_code}", status_code)

    monkeypatch.setattr(research_service, "source_retriever", HttpFailureRetriever())
    response = client.post(f"{endpoint}/{registered['id']}/collect")

    assert response.status_code == 502
    db = SessionLocal()
    try:
        source = db.get(CompetitorSource, registered["id"])
        evidence = list(
            db.scalars(
                select(CompetitorEvidence).where(CompetitorEvidence.source_id == registered["id"])
            ).all()
        )
    finally:
        db.close()

    assert source is not None
    assert source.status == "failed"
    assert source.attempt_count == 1
    assert source.last_attempted_at is not None
    assert source.failure_category == category
    assert source.last_http_status == status_code
    assert evidence == []


def test_collect_source_persists_unsupported_content_failure(client, monkeypatch):
    _, _, _, endpoint = create_source_foundation(client)
    registered = client.post(endpoint, json={"source_url": "https://example.com"}).json()["source"]

    class UnsupportedContentRetriever:
        def retrieve(self, url: str) -> RetrievedSource:
            from app.integrations.source_retriever import RetrievalError

            raise RetrievalError("unsupported_content_type", "Source content type is not supported", 200)

    monkeypatch.setattr(research_service, "source_retriever", UnsupportedContentRetriever())
    response = client.post(f"{endpoint}/{registered['id']}/collect")

    assert response.status_code == 422
    db = SessionLocal()
    try:
        source = db.get(CompetitorSource, registered["id"])
        evidence = list(
            db.scalars(
                select(CompetitorEvidence).where(CompetitorEvidence.source_id == registered["id"])
            ).all()
        )
    finally:
        db.close()

    assert source is not None
    assert source.status == "failed"
    assert source.failure_category == "unsupported_content_type"
    assert source.last_http_status == 200
    assert evidence == []