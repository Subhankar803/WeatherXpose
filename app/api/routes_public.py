"""
Public dashboard endpoints — READ ONLY.
GET /reports (filter by date/event/location/status)
GET /map/active-incidents
GET /stats/dashboard
All reads should go through app/services/cache_service.py first.
"""
