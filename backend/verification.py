"""Integration layer for 8x8 Verif8. 8x8 owns OTP generation and validation —
this module only relays requests to it and translates the response."""

import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/verification", tags=["verification"])

VERIF8_BASE_URL = "https://verify.8x8.com"
REQUEST_TIMEOUT = 10.0


class StartVerificationRequest(BaseModel):
    phone: str = Field(..., min_length=1)


class StartVerificationResponse(BaseModel):
    verification_id: str


class VerifyRequest(BaseModel):
    verification_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)


class VerifyResponse(BaseModel):
    verified: bool


def _get_credentials() -> tuple[str, str]:
    api_key = os.environ.get("X8_API_KEY")
    subaccount_id = os.environ.get("X8_SUBACCOUNT_ID")
    if not api_key or not subaccount_id:
        raise HTTPException(
            status_code=500,
            detail="Verification provider is not configured",
        )
    return api_key, subaccount_id


def _map_error(status_code: int) -> HTTPException:
    if status_code == 400:
        return HTTPException(status_code=400, detail="Verification provider rejected the request")
    if status_code in (401, 403):
        return HTTPException(status_code=500, detail="Verification provider authentication failed")
    if status_code == 404:
        return HTTPException(status_code=404, detail="Verification session not found")
    if status_code >= 500:
        return HTTPException(status_code=502, detail="Verification provider error")
    return HTTPException(status_code=502, detail="Unexpected response from verification provider")


@router.post("/start", response_model=StartVerificationResponse)
async def start_verification(payload: StartVerificationRequest) -> StartVerificationResponse:
    phone = payload.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="phone is required")

    api_key, subaccount_id = _get_credentials()
    url = f"{VERIF8_BASE_URL}/api/v2/subaccounts/{subaccount_id}/sessions"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={"destination": phone},
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Verification provider timed out")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to reach verification provider")

    if response.status_code != 200:
        raise _map_error(response.status_code)

    session_id = response.json().get("sessionId")
    if not session_id:
        raise HTTPException(status_code=502, detail="Unexpected response from verification provider")

    return StartVerificationResponse(verification_id=session_id)


@router.post("/verify", response_model=VerifyResponse)
async def verify_code(payload: VerifyRequest) -> VerifyResponse:
    verification_id = payload.verification_id.strip()
    code = payload.code.strip()
    if not verification_id or not code:
        raise HTTPException(status_code=400, detail="verification_id and code are required")

    api_key, subaccount_id = _get_credentials()
    url = f"{VERIF8_BASE_URL}/api/v2/subaccounts/{subaccount_id}/sessions/{verification_id}"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                params={"code": code},
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Verification provider timed out")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to reach verification provider")

    if response.status_code != 200:
        raise _map_error(response.status_code)

    status = response.json().get("status")
    if status not in {"WAITING", "VERIFIED", "FAILED", "EXPIRED"}:
        raise HTTPException(status_code=502, detail="Unexpected response from verification provider")

    return VerifyResponse(verified=status == "VERIFIED")
