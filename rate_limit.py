from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from redis_client import redis_client

MAX_REQUESTS = 40
WINDOW_SECONDS = 60

async def global_rate_limiter(request: Request, call_next):
    ip = request.client.host
    key = f"rate:{ip}"

    current = redis_client.get(key)

    if current is None:
        redis_client.set(key, 1, ex=WINDOW_SECONDS)
    else:
        current = int(current)
        if current >= MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Try after {WINDOW_SECONDS} seconds"}
            )
        redis_client.incr(key)

    return await call_next(request)