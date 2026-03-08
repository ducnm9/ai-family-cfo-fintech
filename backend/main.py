from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as finance_router
from routes_v2 import v2_router
from auth.routes import router as auth_router, profile_router
from db.database import init_db

app = FastAPI(
    title="AI Family CFO",
    description="AI-powered household financial planning and simulation engine",
    version="2.0.0",
)

import os

ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(finance_router)  # V1 routes (backward compatible)
app.include_router(v2_router)       # V2 intelligence routes


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "AI Family CFO API running", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
