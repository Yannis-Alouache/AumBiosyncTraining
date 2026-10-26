"""Authentication tests: login, token, current profile."""

from tests.conftest import auth_headers, token


async def test_login_returns_token_and_profile(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@aum-bio.fr", "password": "OpsReady2026!"},
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["access_token"]
    assert body["user"]["role"] == "ADMIN"
    assert "password_hash" not in body["user"]


async def test_login_wrong_password(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@aum-bio.fr", "password": "wrong"},
    )
    assert response.status_code == 401
    assert (await response.get_json())["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_unknown_email(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@aum-bio.fr", "password": "OpsReady2026!"},
    )
    assert response.status_code == 401


async def test_me_without_token_rejected(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    assert (await response.get_json())["error"]["code"] == "MISSING_TOKEN"


async def test_me_with_forged_token_rejected(client):
    response = await client.get("/api/auth/me", headers=auth_headers("forged-token"))
    assert response.status_code == 401


async def test_me_returns_profile(client):
    token_value = await token(client)
    response = await client.get("/api/auth/me", headers=auth_headers(token_value))
    assert response.status_code == 200
    assert (await response.get_json())["user"]["email"] == "admin@aum-bio.fr"
