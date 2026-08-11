"""Session identity + the mock financial ledger.

Every endpoint here re-derives who the caller is and what they're allowed to
do from the validated Descope session — never from a role the frontend sent.
Transactions are mock only: no real money moves, no real payment provider is
called. See storage.py for the (sqlite) persistence and demo_users.py for the
prototype's role/organisation mapping.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import storage
from auth import get_current_user, require_role
from demo_users import (
    DEMO_COMPANY_STARTING_BUDGET,
    DEMO_FREELANCER_STARTING_BALANCE,
    DEMO_FREELANCERS,
    SUPPORTED_CURRENCIES,
)

router = APIRouter(tags=["session-and-transactions"])


def _freelancer_balance(user_id: str) -> float:
    withdrawn = storage.sum_completed_amount(user_id, "withdrawal")
    return round(DEMO_FREELANCER_STARTING_BALANCE - withdrawn, 2)


def _company_budget_remaining(user_id: str) -> float:
    paid = storage.sum_completed_amount(user_id, "company_payment")
    return round(DEMO_COMPANY_STARTING_BUDGET - paid, 2)


def _me_payload(user: dict) -> dict:
    payload = {
        "user_id": user["user_id"],
        "role": user["role"],
        "organisation": user["organisation"],
    }
    if user["role"] == "freelancer":
        payload["available_balance"] = _freelancer_balance(user["user_id"])
        payload["has_linked_bank"] = storage.get_bank_account(user["user_id"]) is not None
    else:
        payload["budget_remaining"] = _company_budget_remaining(user["user_id"])
    return payload


@router.get("/me")
def me(user: dict = Depends(get_current_user)) -> dict:
    """Cheap, side-effect-free identity check — dashboards call this on load."""
    return _me_payload(user)


@router.post("/session/bootstrap")
def bootstrap(user: dict = Depends(get_current_user)) -> dict:
    """Called once right after a Descope flow completes — logs the login and returns role/org."""
    storage.write_audit(user["user_id"], "User signed in", detail=f"role={user['role']}")
    return _me_payload(user)


class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")


@router.post("/withdrawal")
def withdraw(payload: WithdrawalRequest, user: dict = Depends(require_role("freelancer"))) -> dict:
    if payload.currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {payload.currency}")

    if storage.get_bank_account(user["user_id"]) is None:
        raise HTTPException(status_code=400, detail="Link a bank account before withdrawing")

    balance = _freelancer_balance(user["user_id"])
    if payload.amount > balance:
        raise HTTPException(status_code=400, detail=f"Amount exceeds available balance of {balance:.2f}")

    # This endpoint is only reachable after the existing Descope/Verif8 step-up
    # flow has already succeeded client-side — see freelancer-dashboard.html.
    storage.write_audit(user["user_id"], "Step-up verification completed")

    tx = storage.create_transaction(
        owner_user_id=user["user_id"],
        type_="withdrawal",
        sender=user["user_id"],
        recipient="Linked bank account",
        amount=payload.amount,
        currency=payload.currency,
        status="completed",
    )
    storage.write_audit(
        user["user_id"], "Withdrawal submitted", detail=f"{payload.currency} {payload.amount:.2f}"
    )
    return {"transaction": tx, "available_balance": _freelancer_balance(user["user_id"])}


class CompanyPaymentRequest(BaseModel):
    recipient_name: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    memo: str | None = None


@router.post("/company/payment")
def send_company_payment(
    payload: CompanyPaymentRequest, user: dict = Depends(require_role("company_admin"))
) -> dict:
    if payload.recipient_name not in DEMO_FREELANCERS:
        raise HTTPException(status_code=400, detail="Unknown recipient")

    if payload.currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {payload.currency}")

    budget = _company_budget_remaining(user["user_id"])
    if payload.amount > budget:
        raise HTTPException(status_code=400, detail=f"Amount exceeds remaining budget of {budget:.2f}")

    storage.write_audit(
        user["user_id"],
        "Company Admin initiated payment",
        detail=f"recipient={payload.recipient_name} amount={payload.currency} {payload.amount:.2f}",
    )

    tx = storage.create_transaction(
        owner_user_id=user["user_id"],
        type_="company_payment",
        sender=user["organisation"],
        recipient=payload.recipient_name,
        amount=payload.amount,
        currency=payload.currency,
        status="completed",
        memo=payload.memo,
    )
    storage.write_audit(user["user_id"], "Company payment confirmed")
    return {"transaction": tx, "budget_remaining": _company_budget_remaining(user["user_id"])}


@router.get("/transactions")
def transactions(user: dict = Depends(get_current_user)) -> dict:
    return {"transactions": storage.list_transactions(user["user_id"])}


@router.get("/audit-log")
def audit_log(user: dict = Depends(get_current_user)) -> dict:
    return {"entries": storage.list_audit(user["user_id"])}
