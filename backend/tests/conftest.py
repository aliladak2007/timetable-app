import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ["TIMETABLING_APP_ENV"] = "test"
os.environ["TIMETABLING_DATABASE_URL"] = "sqlite://"

from app.core.db import get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
import app.models  # noqa: F401, E402
from app.models.base import Base  # noqa: E402
from app.services.rate_limit import rate_limiter  # noqa: E402


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(engine):
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine):
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter._buckets.clear()
    yield
    rate_limiter._buckets.clear()
