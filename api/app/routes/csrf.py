from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.security.csrf import csrf_binding, issue_token, set_csrf_cookie

router = APIRouter()


class CsrfResponse(BaseModel):
    csrf_token: str


@router.get("/csrf", response_model=CsrfResponse)
def get_csrf_token(
    request: Request, response: Response, settings: Annotated[Settings, Depends(get_settings)]
) -> CsrfResponse:
    """Issue a fresh CSRF token as a cookie and in the body."""
    token = issue_token(settings, csrf_binding(request))
    set_csrf_cookie(response, settings, token)
    response.headers["Cache-Control"] = "no-store"
    return CsrfResponse(csrf_token=token)
