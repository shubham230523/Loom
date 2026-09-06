import uuid
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.utils.logging import request_id_var, logger
from backend.app.services.redis import redis_service
from backend.app.config import settings

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        logger.info(f"Incoming request: {method} {path}")
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                f"Completed request: {method} {path} with status {response.status_code}",
                extra={"extra_info": {"duration": round(process_time, 4), "status": response.status_code}}
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Failed request: {method} {path} - {str(e)}",
                exc_info=True,
                extra={"extra_info": {"duration": round(process_time, 4)}}
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware using Redis.
    Limits requests per IP address.
    """
    def __init__(self, app, limit: int = 100, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        if settings.DEBUG and settings.ENVIRONMENT == "development":
            return await call_next(request)

        client_ip = request.client.host
        key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            current = await redis_service.get(key)

            if current and int(current) >= self.limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip} on {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later."
                        }
                    }
                )

            if not current:
                await redis_service.set(key, "1", expire=self.window)
            else:
                await redis_service.client.incr(key)

        except Exception as e:
            logger.error(f"Rate limit check failed (Redis error): {str(e)}")
            return await call_next(request)

        return await call_next(request)
