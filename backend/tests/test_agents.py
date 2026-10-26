"""Agent registry tests: filtered consultation."""

from tests.conftest import auth_headers, token


async def test_list_agents(client):
    token_value = await token(client)
    response = await client.get("/api/agents", headers=auth_headers(token_value))
    assert response.status_code == 200
    body = await response.get_json()
    assert body["total"] == 3
    assert {a["last_name"] for a in body["items"]} == {"MOREAU", "BERNARD", "DARCY"}


async def test_list_agents_requires_authentication(client):
    response = await client.get("/api/agents")
    assert response.status_code == 401
    assert (await response.get_json())["error"]["code"] == "MISSING_TOKEN"


async def test_list_agents_search_filter(client):
    token_value = await token(client)
    response = await client.get("/api/agents?q=darcy", headers=auth_headers(token_value))
    body = await response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["first_name"] == "Eva"


async def test_list_agents_filter_by_site(client):
    token_value = await token(client)
    response = await client.get("/api/agents?site_id=1", headers=auth_headers(token_value))
    body = await response.get_json()
    assert body["total"] == 3
    assert body["items"][0]["site_name"].startswith("SDIS 21")
