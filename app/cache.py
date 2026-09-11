"""
Redis client setup with fast connection timeouts for instantaneous in-memory fallback.
"""
import redis
from app.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True,
    socket_timeout=0.5,
    socket_connect_timeout=0.5,
)
