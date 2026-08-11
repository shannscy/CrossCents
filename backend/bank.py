"""MOCK endpoint only. No real bank connection happens here.

Withdrawals moved to transactions.py, since they're a real (mock) ledger
entry now rather than a standalone stub — see that module for the endpoint
that used to live here as `/withdraw`.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import storage
from auth import require_role

router = APIRouter(tags=["mock"])


class LinkBankRequest(BaseModel):
    account_holder: str = Field(..., min_length=1)
    account_number: str = Field(..., min_length=1)


class LinkBankResponse(BaseModel):
    status: str
    message: str


@router.post("/bank/link", response_model=LinkBankResponse)
async def link_bank(payload: LinkBankRequest, user: dict = Depends(require_role("freelancer"))) -> LinkBankResponse:
    """MOCK — does not connect to a real bank."""
    masked = "•••• " + payload.account_number.strip()[-4:]
    storage.upsert_bank_account(user["user_id"], payload.account_holder.strip(), masked)
    storage.write_audit(user["user_id"], "Bank account linked", detail=masked)
    return LinkBankResponse(status="linked", message="Demo bank account linked successfully")
