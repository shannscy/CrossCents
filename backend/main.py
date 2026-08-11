from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import bank
import storage
import transactions
import verification

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
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(verification.router)
app.include_router(bank.router)
app.include_router(transactions.router)
