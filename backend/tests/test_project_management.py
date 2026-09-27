from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.competitor import Competitor


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
    website = "https://acme.example/company"
    company = client.post(
        f"/api/projects/{project['id']}/company",
        json={"name": "Acme", "website": website, "description": "Our company"},
    )
    assert company.status_code == 201
    assert company.json()["website"] == website
    company_url = f"/api/projects/{project['id']}/company"
    assert client.get(company_url).json()["name"] == "Acme"
    assert client.get(company_url).json()["website"] == website
    updated_website = "https://acme.example/company-updated"
    updated = client.patch(
        company_url,
        json={"name": "Acme Labs", "website": updated_website},
    )
    assert updated.status_code == 200
    assert updated.json()["website"] == updated_website
    assert client.get(company_url).json()["website"] == updated_website
    assert client.post(f"/api/projects/{project['id']}/company", json={"name": "Duplicate"}).status_code == 409


def test_competitor_crud(client):
    project = create_project(client)
    website = "https://rival.example/company"
    competitor = client.post(
        f"/api/projects/{project['id']}/competitors",
        json={"name": "Rival", "website": website, "description": "A rival"},
    )
    assert competitor.status_code == 201
    assert competitor.json()["website"] == website
    competitor_id = competitor.json()["id"]
    project_competitors_url = f"/api/projects/{project['id']}/competitors"
    assert len(client.get(project_competitors_url).json()) == 1
    competitor_url = f"/api/competitors/{competitor_id}"
    assert client.get(competitor_url).status_code == 200
    assert client.get(competitor_url).json()["website"] == website
    updated_website = "https://rival.example/company-updated"
    updated = client.patch(
        competitor_url,
        json={"description": "Updated", "website": updated_website},
    )
    assert updated.status_code == 200
    assert updated.json()["website"] == updated_website
    assert client.get(competitor_url).json()["website"] == updated_website
    assert client.delete(f"/api/competitors/{competitor_id}").status_code == 204
    assert client.get(competitor_url).status_code == 404


def test_invalid_ids_and_relationships(client):
    db = SessionLocal()
    try:
        missing_competitor_id = (db.query(func.max(Competitor.id)).scalar() or 0) + 1
    finally:
        db.close()

    assert client.get("/api/projects/999").status_code == 404
    assert client.patch("/api/projects/999", json={"name": "Missing"}).status_code == 404
    assert client.delete("/api/projects/999").status_code == 404
    assert client.get("/api/projects/999/company").status_code == 404
    assert client.post("/api/projects/999/competitors", json={"name": "Rival"}).status_code == 404
    assert client.get(f"/api/competitors/{missing_competitor_id}").status_code == 404
    assert client.patch(f"/api/competitors/{missing_competitor_id}", json={"name": "Missing"}).status_code == 404
    assert client.delete(f"/api/competitors/{missing_competitor_id}").status_code == 404
    project = create_project(client)
    assert client.post(f"/api/projects/{project['id']}/company", json={"name": "Bad", "website": "not-url"}).status_code == 422
