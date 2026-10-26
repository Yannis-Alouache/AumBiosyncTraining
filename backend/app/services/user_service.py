"""User accounts business logic: reads delegated to the repository, plus
the public-profile rule (never expose the password hash)."""

from app.repositories.user_repository import user_repository


class UserService:
    async def get_by_email(self, email: str) -> dict | None:
        return await user_repository.get_by_email(email)

    async def get_by_id(self, user_id: int) -> dict | None:
        return await user_repository.get_by_id(user_id)

    def public_profile(self, account: dict) -> dict:
        """Extracts the exposable fields of an account (never the hash)."""
        return {field: account[field] for field in user_repository.COLUMNS}


user_service = UserService()
