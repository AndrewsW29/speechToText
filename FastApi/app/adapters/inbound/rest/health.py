from collections.abc import Awaitable, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

ReadinessCheck = Callable[[], Awaitable[bool]]


def build_health_router(checks: dict[str, ReadinessCheck] | None = None) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])
    registered = checks or {}

    @router.get("/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/ready")
    async def ready() -> JSONResponse:
        results = {name: await check() for name, check in registered.items()}
        ok = all(results.values())
        return JSONResponse(
            {"status": "ok" if ok else "unavailable", "checks": results},
            status_code=200 if ok else 503,
        )

    return router
