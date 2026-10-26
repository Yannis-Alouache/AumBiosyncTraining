"""Sites business logic."""

from app.repositories.site_repository import site_repository


class SiteService:
    async def list(self) -> list[dict]:
        return await site_repository.list()


site_service = SiteService()
