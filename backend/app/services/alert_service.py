"""Fatigue alerts business logic: filtered consultation.

Roadmap (TICKETS.md, ticket T11): acknowledgment extends this service —
its state-transition rule (409 when already handled, recorder identity)
belongs here, not in the blueprint.
"""

from app.repositories.alert_repository import alert_repository

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


class AlertService:
    async def list(
        self,
        status: str | None = None,
        severity: str | None = None,
        agent_id: int | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:
        """Business rule owned here: the result window is capped."""
        return await alert_repository.list(
            status=status,
            severity=severity,
            agent_id=agent_id,
            limit=min(MAX_LIMIT, max(1, limit)),
        )


alert_service = AlertService()
