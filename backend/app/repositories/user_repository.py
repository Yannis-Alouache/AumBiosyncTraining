"""Repository for user accounts (used by authentication)."""

from sqlalchemy import select

from app.db import get_session
from app.models import User


class UserRepository:
    """ORM access to the users table."""

    # Non-sensitive fields safe to expose in responses.
    COLUMNS = ("id", "email", "last_name", "first_name", "role")

    async def get_by_email(self, email: str) -> dict | None:
        """Returns the full account (password hash included), email normalized."""
        session = await get_session()
        user = await session.scalar(
            select(User).where(User.email == email.strip().lower())
        )
        return self._to_dict(user, include_hash=True) if user is not None else None

    async def get_by_id(self, user_id: int) -> dict | None:
        """Returns the account without sensitive data, or None if missing."""
        session = await get_session()
        user = await session.get(User, user_id)
        return self._to_dict(user) if user is not None else None

    def _to_dict(self, user: User, include_hash: bool = False) -> dict:
        account = {field: getattr(user, field) for field in self.COLUMNS}
        if include_hash:
            account["password_hash"] = user.password_hash
        return account


user_repository = UserRepository()
