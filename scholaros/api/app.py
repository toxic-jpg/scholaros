"""FastAPI app factory.

Local-only: this API has no auth, rate limiting, or CORS. Run it bound to
127.0.0.1 only (uvicorn scholaros.api.app:create_app --factory --host 127.0.0.1)
and never expose it to an untrusted network.
"""
from __future__ import annotations

from fastapi import FastAPI

from scholaros.storage.migrations import migrate
from scholaros.utils.logging import setup_logging

logger = setup_logging()


def create_app() -> FastAPI:
    migrate()
    app = FastAPI(title="ScholarOS API", version="0.1.0")

    from scholaros.api.routes import router
    app.include_router(router)

    return app