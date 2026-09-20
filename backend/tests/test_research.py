from app.db.session import SessionLocal
from app.models.competitor import Competitor
from app.models.research_run import ResearchRun


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