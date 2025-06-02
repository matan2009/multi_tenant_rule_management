from functools import wraps
from http import HTTPStatus

import redis
from fastapi import HTTPException, Request

from dal import cache
from settings import RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD


async def is_allowed(customer_id: str) -> bool:
    key = f"rate_limit:{customer_id}"

    try:
        count = await cache.increment_request_count(key)

        if count == 1:
            await cache.set_expire_time(key, RATE_LIMIT_PERIOD)

    except redis.exceptions.ConnectionError:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Rate limiter unavailable"
        )

    if count > RATE_LIMIT_REQUESTS:
        return False
    return True


def limit_rate(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        customer_id = request.headers.get("x-user-id")
        if not customer_id:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Missing customer_id for rate limiting")

        if not await is_allowed(customer_id):
            raise HTTPException(
                status_code=HTTPStatus.TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded [rate_limit_period={RATE_LIMIT_PERIOD}]"
                       f"[rate_limit_request={RATE_LIMIT_REQUESTS}]"
            )
        return await func(request, *args, **kwargs)
    return wrapper
