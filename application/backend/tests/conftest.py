"""Every test runs against a throwaway SQLite file, never the real PostgreSQL database."""
import os
import pathlib

TEST_DB = pathlib.Path(__file__).parent / "inventrack-test.db"
# Set before importing the app so its engine is created for SQLite
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)


@pytest.fixture()
def keyboard(client):
    """An item that already exists."""
    response = client.post(
        "/api/items",
        json={
            "name": "Mechanical Keyboard",
            "sku": "KB-100",
            "category": "Peripherals",
            "supplier": "KeyCo",
            "quantity": 20,
            "unit_price": 45.5,
            "reorder_level": 5,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def pytest_sessionfinish(session, exitstatus):
    TEST_DB.unlink(missing_ok=True)
