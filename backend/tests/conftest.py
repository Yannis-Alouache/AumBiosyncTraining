"""Pytest fixtures: Quart application isolated on a temporary database."""

import pytest

from app import create_app
from app.config import Config
from app.db import init_db
from scripts.seed import DEMO_PASSWORD, seed_database


class TestConfig(Config):
    SECRET_KEY = "test-secret-long-enough-for-hmac-sha256-signing"
    TESTING = True
    JWT_EXPIRATION_HOURS = 1


@pytest.fixture()
async def app(tmp_path):
    config = TestConfig()
    config.DATABASE = str(tmp_path / "test.db")
    application = create_app(config)
    await init_db(config.DATABASE)
    await seed_database(config.DATABASE, dataset="test")
    return application


@pytest.fixture()
async def client(app):
    return app.test_client()


async def token(client, email: str = "admin@aum-bio.fr", password: str = DEMO_PASSWORD) -> str:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    return (await response.get_json())["access_token"]


def auth_headers(token_value: str) -> dict:
    return {"Authorization": f"Bearer {token_value}"}
