"""Shift planning tests: filtered consultation."""

from tests.conftest import auth_headers, token


async def test_list_shifts_filtered_by_status(client):
    token_value = await token(client)
    response = await client.get(
        "/api/shifts?status=IN_PROGRESS", headers=auth_headers(token_value)
    )
    body = await response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "NIGHT"
    assert body["items"][0]["agent_last_name"] == "DARCY"
    assert body["items"][0]["site_name"].startswith("SDIS 21")


async def test_list_shifts_filtered_by_agent(client):
    token_value = await token(client)
    response = await client.get(
        "/api/shifts?agent_id=1", headers=auth_headers(token_value)
    )
    body = await response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "DAY"
    assert body["page"] == 1
    assert body["pages"] == 1


async def test_list_shifts_requires_authentication(client):
    response = await client.get("/api/shifts")
    assert response.status_code == 401
