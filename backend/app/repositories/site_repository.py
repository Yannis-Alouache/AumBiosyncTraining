"""Repository for sites."""

from sqlalchemy import func, select

from app.db import get_session
from app.models import Agent, Site


class SiteRepository:
    """ORM access to the sites table, with agent counts."""

    async def list(self) -> list[dict]:
        session = await get_session()
        statement = (
            select(
                Site.id,
                Site.name,
                Site.type,
                Site.city,
                func.count(Agent.id).label("agent_count"),
            )
            .outerjoin(Agent, Agent.site_id == Site.id)
            .group_by(Site.id)
            .order_by(Site.name)
        )
        rows = (await session.execute(statement)).all()
        return [dict(row._mapping) for row in rows]


site_repository = SiteRepository()
