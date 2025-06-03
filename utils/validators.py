from functools import wraps
from http import HTTPStatus
from fastapi import Request, HTTPException
import ipaddress


def get_customer_id(request: Request) -> str:
    customer_id = request.headers.get("X-User-ID")
    if not customer_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing X-User-ID header")
    return customer_id


def _validate_name(rule_name: str):
    if not isinstance(rule_name, str) or not rule_name.strip():
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Missing or invalid rule name")


def validate_rule_name(param_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            rule_name = kwargs.get(param_name)
            _validate_name(rule_name)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_rule_data():
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            body = await request.json()
            _validate_name(body["name"])
            try:
                ipaddress.ip_address(body["ip"])
            except ValueError:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Field 'ip' must be a valid IP address")

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
