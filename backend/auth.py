"""Server-side authentication and authorisation.

The browser is never trusted for identity or role. Every request that needs
to know "who is this" or "are they allowed to do this" comes through here:
we validate the Descope session JWT ourselves (Descope's official Python SDK,
not a custom scheme) and resolve the role/organisation from our own demo
mapping (see demo_users.py) — never from anything the client sent us.
"""

import os

from descope import AuthException, DescopeClient
from fastapi import Depends, Header, HTTPException

from demo_users import resolve_role

_client: DescopeClient | None = None


def _get_client() -> DescopeClient:
    global _client
    if _client is None:
        project_id = os.environ.get("DESCOPE_PROJECT_ID")
        if not project_id:
            raise HTTPException(status_code=500, detail="Auth is not configured")
        _client = DescopeClient(project_id=project_id)
    return _client


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Validates the Descope session JWT and resolves the caller's identity + role.

    Expects `Authorization: Bearer <session JWT>`, the JWT the frontend got
    directly from the Descope flow's success event — never a role or user ID
    the client asserts on its own.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    session_token = authorization.removeprefix("Bearer ").strip()
    if not session_token:
        raise HTTPException(status_code=401, detail="Missing session token")

    try:
        jwt_response = _get_client().validate_session(session_token=session_token)
    except AuthException:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user_id = jwt_response.get("sub") or jwt_response.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not identify user from session")

    # user_id (Descope's stable internal ID) is what owns ledger/audit rows.
    # email is only used to resolve the demo role — see demo_users.py for why.
    email = jwt_response.get("email")
    resolved = resolve_role(email)
    return {"user_id": user_id, "role": resolved["role"], "organisation": resolved["organisation"]}


def require_role(role: str):
    """FastAPI dependency factory — 403s if the authenticated user's backend-resolved role doesn't match."""

    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] != role:
            raise HTTPException(status_code=403, detail=f"This action requires the '{role}' role")
        return current_user

    return dependency
