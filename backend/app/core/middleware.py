import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log execution time and details for all incoming HTTP requests.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"HTTP {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.2f}ms"
            )
            return response
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"HTTP {request.method} {request.url.path} - Failed - Duration: {duration:.2f}ms - Error: {str(e)}"
            )
            raise e
