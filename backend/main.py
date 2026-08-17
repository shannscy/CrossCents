from dotenv import load_dotenv

load_dotenv()

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import bank
import storage
import transactions
import verification

logger = logging.getLogger("crosscents")

app = FastAPI(
    title="CrossCents Backend",
    description="Trusted backend for CrossCents: validates Descope sessions, "
    "resolves roles/organisations server-side, and owns the mock transaction ledger. "
    "Also the integration layer to 8x8 Verif8 for freelancer step-up verification.",
)

storage.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000",
        "https://shannscy.github.io",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.exception_handler(RequestValidationError)
async def log_validation_errors(request: Request, exc: RequestValidationError):
    """A 422 from a Descope connector call is otherwise invisible — the flow just
    shows a generic error and the payload never gets recorded anywhere. Log the
    body we actually received so a malformed connector template is diagnosable
    from the service logs instead of by guesswork."""
    body = (await request.body()).decode("utf-8", errors="replace")
    logger.warning("422 on %s — received body: %s", request.url.path, body)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.include_router(verification.router)
app.include_router(bank.router)
app.include_router(transactions.router)
