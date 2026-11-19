import pytest
from unittest.mock import AsyncMock, patch
import httpx
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.rewrite_service import (
    AIAuthenticationError,
    AITimeoutError,
    AIUpstreamError,
    RewriteService,
    get_rewrite_service,
)


@pytest.fixture
def mock_service():
    """Returns a mock RewriteService instance."""
    service = AsyncMock(spec=RewriteService)
    return service


@pytest.mark.asyncio
async def test_health_check():
    """Test the /health endpoint returns 200 and healthy status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


@pytest.mark.asyncio
async def test_rewrite_success(mock_service):
    """Test successful rewrite request with mocked service."""
    mock_service.rewrite_daily_report.return_value = (
        "Refactored the authentication middleware to enhance session security.",
        "success",
    )
    app.dependency_overrides[get_rewrite_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"description": "refactored auth middleware for session security"}
        response = await client.post("/api/rewrite-daily-report", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "refactored auth middleware for session security"
        assert data["rewritten"] == "Refactored the authentication middleware to enhance session security."
        assert data["status"] == "success"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rewrite_clarification(mock_service):
    """Test response when input requires clarification."""
    mock_service.rewrite_daily_report.return_value = (
        "Clarification needed: Please provide more details regarding what components were tested.",
        "needs_clarification",
    )
    app.dependency_overrides[get_rewrite_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"description": "did testing on stuff"}
        response = await client.post("/api/rewrite-daily-report", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_clarification"
        assert "Clarification needed:" in data["rewritten"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rewrite_empty_description():
    """Test validation error when description is empty string."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/rewrite-daily-report", json={"description": ""})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"


@pytest.mark.asyncio
async def test_rewrite_whitespace_only():
    """Test validation error when description contains only whitespace."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/rewrite-daily-report", json={"description": "     "})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"


@pytest.mark.asyncio
async def test_rewrite_too_short():
    """Test validation error when description is less than 3 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/rewrite-daily-report", json={"description": "ab"})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"


@pytest.mark.asyncio
async def test_rewrite_too_long():
    """Test validation error when description exceeds 2000 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        long_text = "x" * 2001
        response = await client.post("/api/rewrite-daily-report", json={"description": long_text})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"


@pytest.mark.asyncio
async def test_rewrite_missing_field():
    """Test validation error when payload misses description field."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/rewrite-daily-report", json={})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"


@pytest.mark.asyncio
async def test_rewrite_ai_upstream_failure(mock_service):
    """Test handling of 502 Bad Gateway when upstream AI fails."""
    mock_service.rewrite_daily_report.side_effect = AIUpstreamError("Upstream service failed", status_code=502)
    app.dependency_overrides[get_rewrite_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"description": "fixed server crash issue"}
        response = await client.post("/api/rewrite-daily-report", json=payload)
        assert response.status_code == 502
        assert "Upstream service failed" in response.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rewrite_ai_timeout(mock_service):
    """Test handling of 504 Gateway Timeout when upstream AI times out."""
    mock_service.rewrite_daily_report.side_effect = AITimeoutError()
    app.dependency_overrides[get_rewrite_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"description": "fixed server crash issue"}
        response = await client.post("/api/rewrite-daily-report", json=payload)
        assert response.status_code == 504
        assert "timed out" in response.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rewrite_ai_auth_error(mock_service):
    """Test handling of 503 when API key is missing or unauthorized."""
    mock_service.rewrite_daily_report.side_effect = AIAuthenticationError()
    app.dependency_overrides[get_rewrite_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"description": "fixed server crash issue"}
        response = await client.post("/api/rewrite-daily-report", json=payload)
        assert response.status_code == 503
        assert "authentication" in response.json()["detail"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_openapi_and_docs_available():
    """Test that OpenAPI schema and Swagger documentation are reachable."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        docs_response = await client.get("/docs")
        assert docs_response.status_code == 200

        schema_response = await client.get("/openapi.json")
        assert schema_response.status_code == 200
        schema = schema_response.json()
        assert schema["info"]["title"] == "Daily Report AI"
        assert "/api/rewrite-daily-report" in schema["paths"]
        assert "/health" in schema["paths"]


@pytest.mark.asyncio
async def test_root_serves_frontend():
    """Test that GET / serves the interactive HTML frontend."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "Daily Report AI" in response.text


@pytest.mark.asyncio
async def test_static_assets_available():
    """Test that static CSS and JS assets are served properly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        css_res = await client.get("/static/style.css")
        assert css_res.status_code == 200
        assert "var(--bg-page)" in css_res.text

        js_res = await client.get("/static/app.js")
        assert js_res.status_code == 200
        assert "reportInput" in js_res.text


