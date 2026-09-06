"""
Citizen-report submission endpoint.
POST /citizen-report — accepts text + optional photo/video + GPS.
Writes directly to DB (bypasses cache), then hands off to
services/verification_engine.py for scoring.
"""
