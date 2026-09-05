import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.utils.logging import request_id_var, logger

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

        start_time = request.scope.get("start_time", 0) # Fallback
        # Note: BaseHTTPMiddleware doesn't easily expose request duration without manual timing
        import time
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
