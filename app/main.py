"""
FastAPI application entrypoint.
Only responsible for creating the app and including routers —
no business logic should ever live in this file.
"""
from fastapi import FastAPI

from app.api import routes_public, routes_admin, routes_auth, routes_citizen_report

app = FastAPI(title="National Weather Big Data Analytics Platform")

app.include_router(routes_auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(routes_public.router, prefix="/api", tags=["Public"])
app.include_router(routes_admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(routes_citizen_report.router, prefix="/api/citizen-report", tags=["Citizen Reports"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
