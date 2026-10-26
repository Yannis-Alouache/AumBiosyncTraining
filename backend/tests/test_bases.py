"""Base route tests: sites and liveness probe."""

from tests.conftest import auth_headers, token


async def test_list_sites(client):
    token_value = await token(client)
    response = await client.get("/api/sites", headers=auth_headers(token_value))
    assert response.status_code == 200
    body = await response.get_json()
    assert body["items"][0]["agent_count"] == 3


async def test_list_sites_requires_authentication(client):
    response = await client.get("/api/sites")
    assert response.status_code == 401


async def test_health_without_authentication(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = await response.get_json()
    assert body["status"] == "ok"
