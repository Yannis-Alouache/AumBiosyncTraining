"""Authentication controller: token issuance and current profile."""

from pydantic import BaseModel, ConfigDict
from quart import Blueprint, g

from app.security import create_token, require_auth
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.validation import json_body

bp = Blueprint("auth", __name__)


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


@bp.post("/login")
async def login():
    body = Credentials(**await json_body())
    account = await auth_service.authenticate(body.email, body.password)
    return {
        "access_token": create_token(account),
        "user": user_service.public_profile(account),
    }


@bp.get("/me")
@require_auth()
async def me():
    return {"user": g.user}
