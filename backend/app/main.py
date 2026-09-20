from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.companies import router as companies_router
from app.api.routes.competitors import competitor_router, project_router as competitors_router
from app.api.routes.projects import router as projects_router
from app.api.routes.research import router as research_router
from app.core.config import settings
from app import models  # noqa: F401

app = FastAPI(
    title="AI Competitor Research API",
    description="Backend foundation for the AI Competitor Research platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(competitors_router, prefix="/api")
app.include_router(competitor_router, prefix="/api")


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    return {"service": "ai-competitor-research-api", "status": "running"}
