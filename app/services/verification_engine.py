"""
The core "detective" logic — orchestrates signal collection (scoring.py)
and produces the final verdict: Verified / Pending Review / Likely False.
This is the single entry point every ingestion collector calls after
an event has been enriched.
"""
