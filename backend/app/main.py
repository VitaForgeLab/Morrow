import logging

from fastapi import FastAPI

from app.api import api_router
from app.core.errors import register_exception_handlers
from app.core.middleware import register_request_logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)

app = FastAPI(title="Morrow")

register_exception_handlers(app)
register_request_logging(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}