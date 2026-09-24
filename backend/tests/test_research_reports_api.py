from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import AIAnalysis, AIComparison, AIStatement, Competitor, CompetitorResearch, ResearchReport, ResearchRun
from app.schemas.research_report_api import ResearchReportResponse
from app.services import research_reports as report_service


def create_completed_analysis(
    *,
    input_value: str,
    scope: str = "research_run",
    status: str = "completed",
) -> tuple[int, int]:
    with SessionLocal() as db:
        research_run = ResearchRun(input_value=input_value)
        db.add(research_run)
        db.flush()
        competitor_research_id = None
        if scope == "competitor":
            competitor = Competitor(
                research_run_id=research_run.id,
                name="Test competitor",
                domain=f"competitor-{research_run.id}.example",
            )
            db.add(competitor)
            db.flush()
            competitor_research = CompetitorResearch(
                competitor_id=competitor.id,
                research_run_id=research_run.id,
            )
            db.add(competitor_research)
            db.flush()
            competitor_research_id = competitor_research.id
        analysis = AIAnalysis(
            research_run_id=research_run.id,
            competitor_research_id=competitor_research_id,
            scope=scope,
            status=status,
            provider_name="test-provider",
            model_name="test-model",
            prompt_version="prompt-v1",
            contract_version="contract-v1",
            completed_at=datetime.now(timezone.utc) if status == "completed" else None,
        )
        db.add(analysis)
        db.commit()
        return research_run.id, analysis.id


def add_findings(analysis_id: int) -> None:
    with SessionLocal() as db:
        db.add(
            AIStatement(
                analysis_id=analysis_id,
                statement_type="observation",
                text="Pricing is clearly documented.",
                support_status="supported",
                section="pricing",
            )
        )
        db.add(
            AIComparison(
                analysis_id=analysis_id,
                comparison_type="pricing",
                dimension="starting_price",
                statement="Pricing comparison is available.",
                support_status="supported",
            )
        )
        db.commit()


def test_report_routes_are_registered():
    from app.main import app

    paths = set(app.openapi()["paths"])
    assert "/api/research-runs/{research_run_id}/reports" in paths
    assert "/api/research-runs/{research_run_id}/reports/{report_id}" in paths


def test_generate_and_read_report_with_nested_sections_and_references(client):
    research_run_id, analysis_id = create_completed_analysis(input_value="M13 API company")
    add_findings(analysis_id)

    generated = client.post(
        f"/api/research-runs/{research_run_id}/reports",
        json={"analysis_id": analysis_id},
    )

    assert generated.status_code == 201
    generated_body = ResearchReportResponse.model_validate(generated.json())
    assert generated_body.status == "completed"
    assert generated_body.analysis_id == analysis_id
    assert len(generated_body.sections) == 8
    pricing = next(section for section in generated_body.sections if section.section == "pricing")
    comparisons = next(section for section in generated_body.sections if section.section == "comparisons")
    assert pricing.items[0].statement is not None
    assert pricing.items[0].statement.analysis_id == analysis_id
    assert comparisons.items[0].comparison is not None
    assert comparisons.items[0].comparison.analysis_id == analysis_id

    retrieved = client.get(
        f"/api/research-runs/{research_run_id}/reports/{generated_body.id}"
    )
    assert retrieved.status_code == 200
    assert ResearchReportResponse.model_validate(retrieved.json()).id == generated_body.id


def test_report_history_preserves_versions_and_analysis_selection(client):
    research_run_id, analysis_id = create_completed_analysis(input_value="M13 history company")

    first = client.post(
        f"/api/research-runs/{research_run_id}/reports",
        json={"analysis_id": analysis_id},
    )
    second = client.post(
        f"/api/research-runs/{research_run_id}/reports",
        json={"analysis_id": analysis_id},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    history = client.get(f"/api/research-runs/{research_run_id}/reports")
    assert history.status_code == 200
    assert [(item["version"], item["analysis_id"]) for item in history.json()] == [(1, analysis_id), (2, analysis_id)]


def test_generation_rejects_missing_cross_run_and_competitor_analysis(client):
    first_run_id, first_analysis_id = create_completed_analysis(input_value="M13 first company")
    second_run_id, second_analysis_id = create_completed_analysis(input_value="M13 second company")
    _, competitor_analysis_id = create_completed_analysis(
        input_value="M13 competitor scope",
        scope="competitor",
    )

    missing = client.post(
        f"/api/research-runs/{first_run_id}/reports",
        json={"analysis_id": 999999},
    )
    assert missing.status_code == 404

    cross_run = client.post(
        f"/api/research-runs/{first_run_id}/reports",
        json={"analysis_id": second_analysis_id},
    )
    assert cross_run.status_code == 422

    competitor = client.post(
        f"/api/research-runs/{first_run_id}/reports",
        json={"analysis_id": competitor_analysis_id},
    )
    assert competitor.status_code == 422

    with SessionLocal() as db:
        assert db.scalars(select(ResearchReport).where(ResearchReport.research_run_id == first_run_id)).all() == []


def test_generation_rejects_non_completed_analysis(client):
    research_run_id, pending_analysis_id = create_completed_analysis(
        input_value="M13 pending company",
        status="pending",
    )
    response = client.post(
        f"/api/research-runs/{research_run_id}/reports",
        json={"analysis_id": pending_analysis_id},
    )
    assert response.status_code == 422


def test_persisted_failed_report_is_returned_as_report_response(client, monkeypatch):
    research_run_id, analysis_id = create_completed_analysis(input_value="M13 failed company")

    def failed_generation(db, *, research_run_id, analysis_id):
        report = ResearchReport(
            research_run_id=research_run_id,
            analysis_id=analysis_id,
            status="failed",
            version=1,
            failure_reason="composition failed",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    monkeypatch.setattr(report_service, "generate_report", failed_generation)
    response = client.post(
        f"/api/research-runs/{research_run_id}/reports",
        json={"analysis_id": analysis_id},
    )

    assert response.status_code == 201
    body = ResearchReportResponse.model_validate(response.json())
    assert body.status == "failed"
    assert body.failure_reason == "composition failed"


def test_cross_run_report_retrieval_is_not_exposed(client):
    first_run_id, analysis_id = create_completed_analysis(input_value="M13 retrieval first")
    second_run_id, _ = create_completed_analysis(input_value="M13 retrieval second")
    generated = client.post(
        f"/api/research-runs/{first_run_id}/reports",
        json={"analysis_id": analysis_id},
    ).json()

    response = client.get(
        f"/api/research-runs/{second_run_id}/reports/{generated['id']}"
    )
    assert response.status_code == 404
