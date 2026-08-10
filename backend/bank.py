"""MOCK endpoints only. No real bank connection or financial transaction happens here."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["mock"])


class LinkBankRequest(BaseModel):
    user_id: str
    bank_name: str


class LinkBankResponse(BaseModel):
    status: str
    message: str


class WithdrawRequest(BaseModel):
    user_id: str
    amount: float
    currency: str


class WithdrawResponse(BaseModel):
    status: str
    message: str


@router.post("/bank/link", response_model=LinkBankResponse)
async def link_bank(payload: LinkBankRequest) -> LinkBankResponse:
    """MOCK — does not connect to a real bank."""
    return LinkBankResponse(status="linked", message="Demo bank account linked successfully")


@router.post("/withdraw", response_model=WithdrawResponse)
async def withdraw(payload: WithdrawRequest) -> WithdrawResponse:
    """MOCK — does not perform a real financial transaction."""
    return WithdrawResponse(status="success", message="Demo withdrawal approved")
