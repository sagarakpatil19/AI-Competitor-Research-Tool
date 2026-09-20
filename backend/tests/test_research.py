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