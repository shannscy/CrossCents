# CrossCents Backend

A tiny integration layer between the Descope flow and 8x8 Verif8. It is
**not** an auth service — Descope still owns authentication. 8x8 Verif8
owns OTP generation and validation; this backend only relays requests to
it so the `X8_API_KEY` never has to reach the frontend or Descope.

`/bank/link` and `/withdraw` are **mock** endpoints — no real bank or
money movement is involved.

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

Edit `.env` and fill in your real 8x8 token:

```
X8_API_KEY=<your 8x8 Verif8 bearer token>
X8_SUBACCOUNT_ID=NA_Verif8
```

`.env` is gitignored. Never put the real token in `.env.example`, source
code, or the frontend.

## Run

```bash
uvicorn main:app --reload --port 8000
```

Docs at `http://localhost:8000/docs`.

## Endpoints

### `POST /verification/start`
Request:
```json
{ "phone": "+6591234567" }
```
Response:
```json
{ "verification_id": "..." }
```
Calls 8x8 Verif8's `POST /api/v2/subaccounts/{subAccountId}/sessions` to
generate and send the OTP, and returns its `sessionId` as
`verification_id`.

### `POST /verification/verify`
Request:
```json
{ "verification_id": "...", "code": "123456" }
```
Response:
```json
{ "verified": true }
```
Calls 8x8 Verif8's `GET /api/v2/subaccounts/{subAccountId}/sessions/{sessionId}?code=...`
and returns `verified: true` only if 8x8 reports the session `status` as
`VERIFIED`. This backend does not generate or store OTPs itself.

### `POST /bank/link` (mock)
```json
{ "user_id": "demo-user", "bank_name": "Demo Bank" }
```
→ `{ "status": "linked", "message": "Demo bank account linked successfully" }`

### `POST /withdraw` (mock)
```json
{ "user_id": "demo-user", "amount": 100, "currency": "SGD" }
```
→ `{ "status": "success", "message": "Demo withdrawal approved" }`

## How this fits the Descope flow

Descope's Generic HTTP Connector calls this backend directly — no
Descope SDK is used here:

```
Descope flow → POST /verification/start → user gets 8x8 SMS
User enters code → Descope flow → POST /verification/verify
verified: true → Descope flow continues (step-up / phone-add complete)
```

## Manual test (real SMS)

Only after `.env` has a real `X8_API_KEY`:

```bash
curl -X POST http://localhost:8000/verification/start \
  -H "Content-Type: application/json" \
  -d '{"phone": "+6591234567"}'
```
