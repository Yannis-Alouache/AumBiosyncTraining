"""Passwords, JWT tokens and the route protection decorator.

This module is a cross-cutting utility: hashing, token issuance and
decoding. Account loading is delegated to the users service.
"""

import time
from functools import wraps

import jwt
from quart import current_app, g, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import ApiError
from app.services.user_service import user_service


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_token(account: dict) -> str:
    now = int(time.time())
    payload = {
        "sub": str(account["id"]),
        "email": account["email"],
        "role": account["role"],
        "iat": now,
        "exp": now + current_app.config["JWT_EXPIRATION_HOURS"] * 3600,
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=current_app.config["JWT_ALGORITHM"])


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRED", "Le jeton a expiré, reconnectez-vous")
    except jwt.InvalidTokenError:
        raise ApiError(401, "INVALID_TOKEN", "Jeton d'authentification invalide")


def require_auth(*required_roles: str):
    """Access restriction: require_auth() for any authenticated user,
    require_auth("ADMIN") for a given role. Loads g.user for the route."""

    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise ApiError(401, "MISSING_TOKEN", "En-tête Authorization: Bearer requis")
            payload = decode_token(header.removeprefix("Bearer ").strip())
            account = await user_service.get_by_id(int(payload["sub"]))
            if account is None:
                raise ApiError(401, "INVALID_TOKEN", "Compte inexistant ou désactivé")
            if required_roles and account["role"] not in required_roles:
                raise ApiError(
                    403,
                    "FORBIDDEN",
                    "Rôle insuffisant pour cette opération",
                    {"required_roles": list(required_roles), "current_role": account["role"]},
                )
            g.user = account
            return await fn(*args, **kwargs)

        return wrapper

    return decorator
