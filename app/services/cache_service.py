"""
Cache-aside pattern helpers.
get_or_set(key, compute_fn, ttl) — check Redis first, compute + store on miss.
invalidate(key) — called whenever a report's verdict changes.
"""
