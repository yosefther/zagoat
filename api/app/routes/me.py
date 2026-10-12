import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.db import DbSession
from app.models import User
from app.security.csrf import ANONYMOUS, issue_token, require_csrf, set_csrf_cookie
from app.security.sessions import RequiredAuth, clear_session_cookie

router = APIRouter()


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    code_opt_in: bool
    created_at: datetime


class MeUpdate(BaseModel):
    code_opt_in: bool


def me_response(user: User) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        code_opt_in=user.code_opt_in,
        created_at=user.created_at,
    )


@router.get("/me", response_model=MeResponse)
def get_me(auth: RequiredAuth) -> MeResponse:
    return me_response(auth.user)


@router.patch("/me", response_model=MeResponse, dependencies=[Depends(require_csrf)])
def update_me(body: MeUpdate, auth: RequiredAuth, db: DbSession) -> MeResponse:
    auth.user.code_opt_in = body.code_opt_in
    db.commit()
    return me_response(auth.user)


@router.delete("/me", status_code=204, dependencies=[Depends(require_csrf)])
def delete_me(
    auth: RequiredAuth,
    response: Response,
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Delete the account and everything tied to it at once (section 11).

    Foreign keys cascade to sessions, OAuth accounts, drafts, submissions, progress and usage.
    """
    db.delete(auth.user)
    db.commit()
    clear_session_cookie(response, settings)
    set_csrf_cookie(response, settings, issue_token(settings, ANONYMOUS))
