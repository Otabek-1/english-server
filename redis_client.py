import os
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    username=os.getenv("REDIS_USERNAME", "default"),
    password=os.getenv("REDIS_PASSWORD", ""),
)