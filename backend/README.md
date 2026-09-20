# Backend

FastAPI service for the AI Competitor Research platform.

## PostgreSQL configuration

The backend requires `DATABASE_URL` and only accepts PostgreSQL. Copy `.env.example` to `.env` and replace `USER` and `PASSWORD` with your local PostgreSQL credentials. No SQLite application database is used.

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The health endpoint is available at `http://localhost:8000/api/health`.

## Alembic migrations

Set `DATABASE_URL` in the backend environment before running migrations:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_competitor_research"
alembic upgrade head
```

Create a migration after changing models:

```powershell
alembic revision --autogenerate -m "describe the change"
```

Roll back one revision:

```powershell
alembic downgrade -1
```

Alembic is the schema source of truth. The application does not call `metadata.create_all`.

Integration tests require `TEST_DATABASE_URL`, pointing to a separate PostgreSQL test database with the Alembic migrations already applied. Tests never fall back to SQLite, never call `metadata.create_all`, and never use the development database unless explicitly configured that way.

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_competitor_research_test"
pytest -q
```

If `TEST_DATABASE_URL` is absent, the integration tests are skipped rather than pretending PostgreSQL behavior was validated with another database.
