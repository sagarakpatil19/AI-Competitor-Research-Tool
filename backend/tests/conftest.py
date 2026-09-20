import os

import pytest

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip(
        "Set TEST_DATABASE_URL to a dedicated PostgreSQL test database with migrations applied.",
        allow_module_level=True,
    )

if TEST_DATABASE_URL == os.getenv("DATABASE_URL"):
    pytest.skip(
        "TEST_DATABASE_URL must point to a separate PostgreSQL database from DATABASE_URL.",
        allow_module_level=True,
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
