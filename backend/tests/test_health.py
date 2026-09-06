from tributaria_api.api.routes.health import HealthResponse, health
from tributaria_api.main import app


def test_health_endpoint() -> None:
    schema = app.openapi()

    assert "/api/v1/health" in schema["paths"]
    assert health() == HealthResponse(status="ok", service="tributaria-api")
