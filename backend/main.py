from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import bank
import verification

app = FastAPI(
    title="CrossCents Backend",
    description="Integration layer between Descope and 8x8 Verif8. Not an authentication service.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000",
    ],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(verification.router)
app.include_router(bank.router)
