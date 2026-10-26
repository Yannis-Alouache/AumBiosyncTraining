"""Authentication use case: verify credentials."""

from app.errors import ApiError
from app.security import verify_password
from app.services.user_service import user_service


class AuthService:
    async def authenticate(self, email: str, password: str) -> dict:
        """Returns the account when credentials are valid, otherwise raises 401."""
        account = await user_service.get_by_email(email)
        if account is None or not verify_password(password, account["password_hash"]):
            raise ApiError(401, "INVALID_CREDENTIALS", "Email ou mot de passe incorrect")
        return account


auth_service = AuthService()
