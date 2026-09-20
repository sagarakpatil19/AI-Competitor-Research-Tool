# AI Competitor Research

A production-oriented foundation for an AI-powered competitor research SaaS application.

## Project structure

- `frontend/` - Next.js, TypeScript, React, Tailwind CSS, and App Router UI.
- `backend/` - FastAPI service with a modular API layout.

## Start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API health check is available at `http://localhost:8000/api/health`.

Before starting the backend, configure PostgreSQL:

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend\.env` with your PostgreSQL credentials. The application requires `DATABASE_URL` and does not use or create a SQLite `app.db` file.

## Start the frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`.

The frontend reads `NEXT_PUBLIC_API_URL` and calls `${NEXT_PUBLIC_API_URL}/api/health` when the dashboard loads. Copy `.env.example` to `.env.local` in either project only when you need to override the defaults.

Database migrations are managed by Alembic. From `backend`, run `alembic upgrade head` to apply migrations, `alembic revision --autogenerate -m "describe the change"` to create one, and `alembic downgrade -1` to roll back one revision. Always set the PostgreSQL `DATABASE_URL` first.

## Current scope

This foundation intentionally does not include authentication, persistence, research integrations, AI analysis, reports, Redis, payments, or deployment configuration.
