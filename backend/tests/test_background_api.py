from datetime import datetime, timezone
from types import SimpleNamespace

from app.ai.errors import ProviderResponseError
from app.api.routes import research as research_routes
from app.background.commands import AIAnalysisCommand, CompetitorDiscoveryCommand, SourceCollectionCommand
from app.background.runtime import BackgroundRuntime
from app.integrations.source_retriever import RetrievedSource
from app.main import app
from app.services import research as research_service


def _create_research_run(client, company="Acme"):
    return client.post("/api/research", json={"company": company}).json()["research_id"]


def _poll_operation(client, submission):
    response = client.get(submission.json()["status_url"])
    assert response.status_code == 200
    return response.json()


def _create_competitor_research_execution(client):
    research_run_id = _create_research_run(client)
    assert client.post(f"/api/research/{research_run_id}/resolve").status_code == 200
    assert client.post(f"/api/research/{research_run_id}/understand").status_code == 200
    competitor = client.post(
        f"/api/research/{research_run_id}/discover",
        json={"competitors": [{"name": "Example", "domain": "example.com"}]},
    ).json()["competitors"][0]
    submission = client.post(
        f"/api/research/{research_run_id}/research",
        json={"competitor_ids": [competitor["id"]]},
    )
    operation = _poll_operation(client, submission)
    execution = operation["result"]["competitor_research"][0]
    return research_run_id, competitor, execution


def test_discovery_submission_returns_accepted_and_exposes_queued_command(client, monkeypatch):
    research_run_id = _create_research_run(client)
    runtime: BackgroundRuntime = app.state.background_runtime
    process_pending = runtime.process_pending
    monkeypatch.setattr(runtime, "process_pending", lambda: None)

    response = client.post(f"/api/research-runs/{research_run_id}/competitor-discovery")

    assert response.status_code == 202
    body = response.json()
    assert body["research_run_id"] == research_run_id
    assert body["operation"] == "competitor_discovery"
    assert body["status"] == "queued"
    assert body["status_url"] == response.headers["location"]
    assert len(runtime.queue) == 1
    command = next(iter(runtime.queue))
    assert isinstance(command, CompetitorDiscoveryCommand)
    assert command.research_run_id == research_run_id
    assert command.logical_id == body["logical_id"]

    runtime.dispatcher.competitor_discovery_service = lambda db, run_id: SimpleNamespace(id=501)
    process_pending()
    operation = _poll_operation(client, response)
    assert operation["status"] == "completed"
    assert operation["result"] == {"id": 501}


def test_failed_operation_is_observable_as_failed(client):
    research_run_id = _create_research_run(client)
    runtime: BackgroundRuntime = app.state.background_runtime

    def fail_discovery(db, run_id):
        raise ValueError("invalid discovery request")

    runtime.dispatcher.competitor_discovery_service = fail_discovery
    response = client.post(f"/api/research-runs/{research_run_id}/competitor-discovery")

    assert response.status_code == 202
    operation = _poll_operation(client, response)
    assert operation["status"] == "failed"
    assert operation["failure_category"] == "validation"
    assert operation["failure_reason"] == "invalid discovery request"
    assert operation["result"] is None


def test_retry_succeeds_with_same_logical_identity(client):
    research_run_id = _create_research_run(client)
    runtime: BackgroundRuntime = app.state.background_runtime
    calls = []

    def flaky_discovery(db, run_id):
        calls.append(run_id)
        if len(calls) == 1:
            raise TimeoutError("temporary network issue")
        return SimpleNamespace(id=502)

    runtime.dispatcher.competitor_discovery_service = flaky_discovery
    response = client.post(f"/api/research-runs/{research_run_id}/competitor-discovery")

    assert response.status_code == 202
    operation = _poll_operation(client, response)
    assert len(calls) == 2
    assert operation["status"] == "completed"
    assert operation["attempt_count"] == 2
    assert operation["logical_id"] == response.json()["logical_id"]


def test_duplicate_submission_returns_existing_operation_without_reexecution(client):
    research_run_id = _create_research_run(client)
    runtime: BackgroundRuntime = app.state.background_runtime
    calls = []

    def discovery(db, run_id):
        calls.append(run_id)
        return SimpleNamespace(id=503)

    runtime.dispatcher.competitor_discovery_service = discovery
    endpoint = f"/api/research-runs/{research_run_id}/competitor-discovery"
    first = client.post(endpoint)
    second = client.post(endpoint)

    assert first.status_code == second.status_code == 202
    assert first.json()["logical_id"] == second.json()["logical_id"]
    assert _poll_operation(client, second)["status"] == "completed"
    assert calls == [research_run_id]


def test_ai_analysis_submission_uses_command_and_existing_analysis_reference(client, monkeypatch):
    research_run_id = _create_research_run(client)
    client.post(f"/api/research/{research_run_id}/resolve")
    client.post(f"/api/research/{research_run_id}/understand")
    competitor = client.post(
        f"/api/research/{research_run_id}/discover",
        json={"competitors": [{"name": "Example", "domain": "example.com"}]},
    ).json()["competitors"][0]
    research_submission = client.post(
        f"/api/research/{research_run_id}/research",
        json={"competitor_ids": [competitor["id"]]},
    )
    execution_id = _poll_operation(client, research_submission)["result"]["competitor_research"][0]["id"]

    class FakeAIProvider:
        def analyze(self, context):
            raise AssertionError("The mocked analysis service must prevent provider calls")

    monkeypatch.setattr(research_routes, "create_ai_provider", FakeAIProvider)
    runtime: BackgroundRuntime = app.state.background_runtime
    runtime.dispatcher.ai_analysis_service = lambda *args, **kwargs: SimpleNamespace(id=504)
    response = client.post(
        f"/api/research/{research_run_id}/ai-analysis",
        json={"scope": "competitor", "competitor_research_id": execution_id},
    )

    assert response.status_code == 202
    operation = _poll_operation(client, response)
    command = runtime.get_operation(operation["logical_id"]).command
    assert isinstance(command, AIAnalysisCommand)
    assert command.research_run_id == research_run_id
    assert command.competitor_research_id == execution_id
    assert operation["status"] == "completed"
    assert operation["result"] == {"id": 504}


def test_missing_research_and_unknown_operation_return_not_found(client):
    missing_submission = client.post("/api/research-runs/999999/competitor-discovery")
    missing_status = client.get("/api/background-operations/unknown-logical-id")

    assert missing_submission.status_code == 404
    assert missing_status.status_code == 404


def test_retryable_failure_exhaustion_becomes_terminal(client, monkeypatch):
    research_run_id = _create_research_run(client)
    runtime: BackgroundRuntime = app.state.background_runtime
    calls = []
    enqueued_logical_ids = []
    original_enqueue = runtime.queue.enqueue

    def track_enqueue(command):
        enqueued_logical_ids.append(command.logical_id)
        original_enqueue(command)

    monkeypatch.setattr(runtime.queue, "enqueue", track_enqueue)

    def unavailable_discovery(db, run_id):
        calls.append(run_id)
        raise TimeoutError("temporary network issue")

    runtime.dispatcher.competitor_discovery_service = unavailable_discovery
    response = client.post(f"/api/research-runs/{research_run_id}/competitor-discovery")

    assert response.status_code == 202
    submitted = response.json()
    operation = _poll_operation(client, response)
    assert submitted["status"] == "queued"
    assert operation["status"] == "failed"
    assert operation["attempt_count"] == operation["max_attempts"] == 3
    assert operation["failure_category"] == "network"
    assert operation["failure_reason"] == "temporary network issue"
    assert operation["logical_id"] == submitted["logical_id"]
    assert enqueued_logical_ids == [submitted["logical_id"]] * 3
    assert calls == [research_run_id] * operation["max_attempts"]
    assert len(runtime.queue) == 0


def test_permanent_ai_provider_failure_is_not_retried(client, monkeypatch):
    research_run_id, _, execution = _create_competitor_research_execution(client)

    class FakeAIProvider:
        def analyze(self, context):
            raise AssertionError("The mocked analysis service must prevent provider calls")

    monkeypatch.setattr(research_routes, "create_ai_provider", FakeAIProvider)
    runtime: BackgroundRuntime = app.state.background_runtime
    calls = []

    def permanent_failure(*args, **kwargs):
        calls.append((args, kwargs))
        raise ProviderResponseError("provider returned an unusable response")

    runtime.dispatcher.ai_analysis_service = permanent_failure
    payload = {"scope": "competitor", "competitor_research_id": execution["id"]}
    endpoint = f"/api/research/{research_run_id}/ai-analysis"
    response = client.post(endpoint, json=payload)

    assert response.status_code == 202
    submitted = response.json()
    operation = _poll_operation(client, response)
    assert operation["status"] == "failed"
    assert operation["failure_category"] == "providerresponseerror"
    assert operation["failure_reason"] == "provider returned an unusable response"
    assert operation["attempt_count"] == 1
    assert operation["logical_id"] == submitted["logical_id"]
    assert len(calls) == 1
    assert len(runtime.queue) == 0

    duplicate = client.post(endpoint, json=payload)
    assert duplicate.status_code == 202
    assert duplicate.json()["logical_id"] == submitted["logical_id"]
    assert _poll_operation(client, duplicate)["status"] == "failed"
    assert len(calls) == 1


def test_duplicate_submission_while_queued_is_enqueued_and_executed_once(client, monkeypatch):
    research_run_id = _create_research_run(client)
    runtime: BackgroundRuntime = app.state.background_runtime
    process_pending = runtime.process_pending
    calls = []

    def discovery(db, run_id):
        calls.append(run_id)
        return SimpleNamespace(id=505)

    runtime.dispatcher.competitor_discovery_service = discovery
    monkeypatch.setattr(runtime, "process_pending", lambda: None)
    endpoint = f"/api/research-runs/{research_run_id}/competitor-discovery"

    first = client.post(endpoint)
    second = client.post(endpoint)

    assert first.status_code == second.status_code == 202
    assert first.json()["logical_id"] == second.json()["logical_id"]
    assert len(runtime.queue) == 1
    assert calls == []

    process_pending()
    operation = _poll_operation(client, second)
    assert operation["status"] == "completed"
    assert operation["logical_id"] == first.json()["logical_id"]
    assert calls == [research_run_id]
    assert len(runtime.queue) == 0


def test_source_collection_uses_background_lifecycle_and_returns_domain_result(client, monkeypatch):
    research_run_id, competitor, execution = _create_competitor_research_execution(client)
    source_endpoint = (
        f"/api/research/{research_run_id}/competitors/{competitor['id']}"
        "/research/sources"
    )
    source = client.post(
        source_endpoint,
        json={"source_url": "https://example.com/article"},
    ).json()["source"]

    class FakeRetriever:
        def retrieve(self, url):
            content = "A sufficiently long source document for validating collected evidence."
            return RetrievedSource(
                final_url=url,
                http_status=200,
                content_type="text/plain",
                content=content,
                content_excerpt=content,
                content_hash="a" * 64,
                retrieved_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr(research_service, "source_retriever", FakeRetriever())
    runtime: BackgroundRuntime = app.state.background_runtime
    endpoint = f"{source_endpoint}/{source['id']}/collect"
    response = client.post(endpoint)

    assert response.status_code == 202
    submitted = response.json()
    operation = _poll_operation(client, response)
    command = runtime.get_operation(operation["logical_id"]).command
    assert isinstance(command, SourceCollectionCommand)
    assert command.research_run_id == research_run_id
    assert command.competitor_research_id == execution["id"]
    assert command.source_id == source["id"]
    assert submitted["logical_id"] == command.logical_id
    assert operation["operation"] == "source_collection"
    assert operation["status"] == "completed"
    assert operation["result"]["source"]["id"] == source["id"]
    assert operation["result"]["source"]["status"] == "collected"
    assert operation["result"]["evidence"]["source_id"] == source["id"]
    assert operation["result"]["evidence"]["competitor_research_id"] == execution["id"]