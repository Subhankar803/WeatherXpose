"""
National Weather Big Data Analytics Platform - FastAPI Backend Engine.

High performance async ASGI backend powered by FastAPI & Uvicorn:
- Interactive Swagger UI: /docs
- Alternative ReDoc API Docs: /redoc
- Root redirect: / -> /docs
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.api import routes_public, routes_admin, routes_auth, routes_citizen_report
from app.database_setup import engine, Base
from app.models import User, Admin, Source, Reports, Images_Videos, Action_Log
from scripts.seed_data import seed_database
from app.ml.trained_model import load_all_models

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Ensure all database tables exist immediately on import
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed default data & load ML models
    try:
        seed_database()
        load_all_models()
    except Exception as e:
        print(f"[startup] Startup initialization note: {e}")
    yield


app = FastAPI(
    title="National Weather Big Data Analytics Platform - API",
    description="Scalable Big Data Analytics & Truth Verification API for Weather in India (IMD, Windy, GNews, NewsData, Citizen Reports & ML Forensics).",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API Routers
app.include_router(routes_auth.router, prefix="/api/auth", tags=["1. Authentication & Registration (User & Admin with Dual OTP)"])
app.include_router(routes_citizen_report.router, prefix="/api/citizen-report", tags=["2. Citizen Report & Verification"])
app.include_router(routes_public.router, prefix="/api", tags=["3. Public Weather Intelligence & Analytics"])
app.include_router(routes_admin.router, prefix="/api/admin", tags=["4. Admin Review & Audit Queue"])

# Static Mount for Uploaded Media
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirects directly to interactive Swagger UI documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System Health"])
def health_check():
    return {
        "status": "healthy",
        "platform": "National Weather Big Data Analytics Platform (India)",
        "version": "2.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }
