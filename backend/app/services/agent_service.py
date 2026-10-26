"""Agents registry business logic.

Roadmap (TICKETS.md, tickets T07 and T08): the create and update use
cases extend this service — their uniqueness and field-update rules
belong here, not in the blueprint.
"""

from app.repositories.agent_repository import agent_repository


class AgentService:
    async def list(
        self,
        q: str | None = None,
        site_id: int | None = None,
        status: str | None = None,
    ) -> list[dict]:
        return await agent_repository.list(q=q, site_id=site_id, status=status)


agent_service = AgentService()
