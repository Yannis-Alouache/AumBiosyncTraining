"""Alert tests: filtered consultation (read-only)."""

from tests.conftest import auth_headers, token


async def test_list_alerts_filtered_by_status(client):
    token_value = await token(client)
    response = await client.get(
        "/api/alerts?status=NEW", headers=auth_headers(token_value)
    )
    body = await response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "FATIGUE_CRITICAL"


async def test_list_alerts_filtered_by_severity(client):
    token_value = await token(client)
    response = await client.get(
        "/api/alerts?severity=WARNING", headers=auth_headers(token_value)
    )
    body = await response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["agent_last_name"] == "BERNARD"


async def test_list_alerts_requires_authentication(client):
    response = await client.get("/api/alerts")
    assert response.status_code == 401
