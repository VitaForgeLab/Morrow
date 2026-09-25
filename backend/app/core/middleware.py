# 暂时不看
import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger("morrow.request")


def register_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        cost_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d  %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            cost_ms,
        )
        return response