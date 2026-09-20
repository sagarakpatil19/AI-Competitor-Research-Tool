def create_project(client, name="Market map"):
    response = client.post("/api/projects", json={"name": name, "description": "Signals and positioning"})
    assert response.status_code == 201
    return response.json()


def test_project_crud(client):
    project = create_project(client)
    assert client.get("/api/projects").json()[0]["id"] == project["id"]

    updated = client.patch(f"/api/projects/{project['id']}", json={"name": "Updated map"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated map"

    deleted = client.delete(f"/api/projects/{project['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/projects/{project['id']}").status_code == 404


def test_company_crud_and_duplicate_protection(client):
    project = create_project(client)
    company = client.post(
        f"/api/projects/{project['id']}/company",
        json={"name": "Acme", "website": "https://acme.example", "description": "Our company"},
    )
    assert company.status_code == 201
    assert client.get(f"/api/projects/{project['id']}/company").json()["name"] == "Acme"
    assert client.patch(f"/api/projects/{project['id']}/company", json={"name": "Acme Labs"}).status_code == 200
    assert client.post(f"/api/projects/{project['id']}/company", json={"name": "Duplicate"}).status_code == 409


def test_competitor_crud(client):
    project = create_project(client)
    competitor = client.post(
        f"/api/projects/{project['id']}/competitors",
        json={"name": "Rival", "website": "https://rival.example", "description": "A rival"},
    )
    assert competitor.status_code == 201
    competitor_id = competitor.json()["id"]
    assert len(client.get(f"/api/projects/{project['id']}/competitors").json()) == 1
    assert client.get(f"/api/competitors/{competitor_id}").status_code == 200
    assert client.patch(f"/api/competitors/{competitor_id}", json={"description": "Updated"}).status_code == 200
    assert client.delete(f"/api/competitors/{competitor_id}").status_code == 204
    assert client.get(f"/api/competitors/{competitor_id}").status_code == 404


def test_invalid_ids_and_relationships(client):
    assert client.get("/api/projects/999").status_code == 404
    assert client.patch("/api/projects/999", json={"name": "Missing"}).status_code == 404
    assert client.delete("/api/projects/999").status_code == 404
    assert client.get("/api/projects/999/company").status_code == 404
    assert client.post("/api/projects/999/competitors", json={"name": "Rival"}).status_code == 404
    assert client.get("/api/competitors/999").status_code == 404
    assert client.patch("/api/competitors/999", json={"name": "Missing"}).status_code == 404
    assert client.delete("/api/competitors/999").status_code == 404
    project = create_project(client)
    assert client.post(f"/api/projects/{project['id']}/company", json={"name": "Bad", "website": "not-url"}).status_code == 422
