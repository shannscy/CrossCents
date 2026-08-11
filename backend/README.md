# CrossCents Backend

The trusted backend for CrossCents. Two jobs:

1. **Integration layer to 8x8 Verif8** for the existing freelancer step-up
   flows (withdrawal, bank-link). Descope still owns authentication; Verif8
   still owns OTP generation and validation. This backend only relays
   requests to it so `X8_API_KEY` never reaches the frontend or Descope.
2. **Trusted backend for identity, authorization, and the mock ledger.**
   The browser is never trusted for role or identity — every financial
   endpoint independently validates the caller's Descope session JWT
   (official `descope` Python SDK, `validate_session`) and resolves their
   role/organisation from a backend-only demo mapping (`demo_users.py`),
   never from anything the client asserts.

All money movement is **mock** — no real bank, no real payment provider.

## Install

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

```bash
cp .env.example .env
```

```
X8_API_KEY=<your real 8x8 Verif8 bearer token>
X8_SUBACCOUNT_ID=NA_Verif8
DESCOPE_PROJECT_ID=P3HZlcn7sECUmwT4OWWOSR72I2fa
```

`DESCOPE_PROJECT_ID` isn't secret (it's already public in `js/app.js`) — it's
prefilled above. `X8_API_KEY` is secret; `.env` is gitignored, never commit
it. `crosscents.db` (the sqlite ledger, created on first run) is also
gitignored — it's local runtime state, not source.

## Run

```bash
uvicorn main:app --reload --port 8000
```

Docs at `http://localhost:8000/docs`.

## Auth model

Every endpoint below except `/verification/*` requires:

```
Authorization: Bearer <Descope session JWT>
```

The frontend gets this JWT directly from the Descope flow's `success` event
— see `mountDescopeFlow()` in `js/app.js`. The backend validates it via
Descope's SDK and resolves role/org itself (`auth.py` + `demo_users.py`).
There is currently exactly one demo company admin, mapped by Descope user ID
in `demo_users.DEMO_COMPANY_ADMINS`; every other authenticated user is
treated as a freelancer. Replace that mapping with a real
Organisation/Membership table when this stops being a demo.

## Endpoints

### `GET /me`
Returns the caller's resolved identity — `{ user_id, role, organisation,
available_balance | budget_remaining, has_linked_bank }`. Side-effect free;
dashboards call this on every page load to re-verify role, not a cached
value.

### `POST /session/bootstrap`
Same response as `/me`, plus writes a "User signed in" audit row. Call once,
right after a Descope flow's `success` event.

### `POST /verification/start`, `POST /verification/verify`
Unchanged — see the original Verif8 integration notes below.

### `POST /bank/link` (mock, freelancer only)
```json
{ "account_holder": "Jane Doe", "account_number": "0123456789" }
```
→ `{ "status": "linked", "message": "Demo bank account linked successfully" }`

### `POST /withdrawal` (mock, freelancer only)
```json
{ "amount": 200, "currency": "USD" }
```
Only reachable in the frontend after the **existing** Descope/Verif8
step-up flow succeeds. Validates: amount > 0, supported currency, a bank
account is linked, amount ≤ current mock balance. Writes a transaction +
audit rows, returns `{ transaction, available_balance }`.

### `POST /company/payment` (mock, company_admin only)
```json
{ "recipient_name": "Katelin Rivera", "amount": 500, "currency": "USD", "memo": "Invoice #12" }
```
No Verif8 / step-up involved (out of scope for now, per current design).
Validates: recipient is a known demo freelancer, amount > 0, supported
currency, amount ≤ remaining mock budget. Writes a transaction + audit
rows, returns `{ transaction, budget_remaining }`.

### `GET /transactions`
Returns the caller's own transaction history (freelancer: withdrawals +
payments received; company admin: payments sent).

### `GET /audit-log`
Returns the caller's own recent audit events, newest first.

## How Verif8 fits the Descope flow (unchanged)

Descope's Generic HTTP Connector calls this backend directly — no Descope
SDK is used for that side:

```
Descope flow → POST /verification/start → user gets 8x8 SMS
User enters code → Descope flow → POST /verification/verify
verified: true → Descope flow continues (step-up / phone-add complete)
```

## Manual test (real SMS)

Only after `.env` has a real `X8_API_KEY`, and 8x8's account balance/IP
allowlist are sorted (see project notes — currently blocked on 8x8 support):

```bash
curl -X POST http://localhost:8000/verification/start \
  -H "Content-Type: application/json" \
  -d '{"phone": "+6591234567"}'
```

## Manual test (auth + ledger, no Verif8 needed)

```bash
# should 401 — no token
curl -i http://localhost:8000/me

# get a real token: sign in at company-login.html or freelancer-login.html
# in the browser, then read it from sessionStorage (devtools console):
#   sessionStorage.getItem("crosscents_session_token")

curl http://localhost:8000/me -H "Authorization: Bearer <paste token>"
```
