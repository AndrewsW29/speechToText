from app.adapters.inbound.rest.health import build_health_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client(ok: bool) -> TestClient:
    async def check() -> bool:
        return ok

    app = FastAPI()
    app.include_router(build_health_router({"db": check}))
    return TestClient(app)


def test_ready_reports_unavailable_dependency() -> None:
    r = _client(False).get("/health/ready")
    assert r.status_code == 503 and r.json()["checks"] == {"db": False}


def test_ready_ok_when_dependencies_healthy() -> None:
    assert _client(True).get("/health/ready").status_code == 200
