"""Repository for the agents registry."""

from sqlalchemy import or_, select

from app.db import get_session
from app.models import Agent, Site


class AgentRepository:
    """ORM access to the agents table, joined with sites."""

    async def list(
        self,
        q: str | None = None,
        site_id: int | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """All agents, filtered by free-text search, site and status."""
        session = await get_session()
        statement = select(Agent, Site).join(Site, Agent.site_id == Site.id)
        if site_id is not None:
            statement = statement.where(Agent.site_id == site_id)
        if status:
            statement = statement.where(Agent.status == status)
        if q:
            fragment = f"%{q.lower()}%"
            statement = statement.where(
                or_(
                    Agent.last_name.ilike(fragment),
                    Agent.first_name.ilike(fragment),
                    Agent.email.ilike(fragment),
                )
            )
        statement = statement.order_by(Agent.last_name, Agent.first_name)

        rows = (await session.execute(statement)).all()
        return [self._to_dict(agent, site) for agent, site in rows]

    def _to_dict(self, agent: Agent, site: Site) -> dict:
        return {
            "id": agent.id,
            "site_id": agent.site_id,
            "last_name": agent.last_name,
            "first_name": agent.first_name,
            "email": agent.email,
            "profession": agent.profession,
            "grade": agent.grade,
            "status": agent.status,
            "fatigue_index": agent.fatigue_index,
            "last_sleep_hours": agent.last_sleep_hours,
            "hired_on": agent.hired_on,
            "site_name": site.name,
            "site_type": site.type,
            "site_city": site.city,
        }


agent_repository = AgentRepository()
