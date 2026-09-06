"""
Entry point for scheduled ingestion runs (called by cron or Airflow).
Loops through every collector in app/ingestion/, runs .fetch(),
pushes results through the verification pipeline.
Each collector runs in its own try/except — one failing source
must never stop the others.
"""
