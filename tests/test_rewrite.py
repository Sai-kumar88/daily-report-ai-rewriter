import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.config import Settings
from app.services.rewrite_service import (
    AIServiceError,
    AIAuthenticationError,
    AITimeoutError,
    AIUpstreamError,
    RewriteService,
)


@pytest.fixture
def mock_settings():
    return Settings(
        NVIDIA_API_KEY="nvapi-test-valid-key",
        NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1",
        NVIDIA_MODEL="nvidia/nemotron-3.5-lightning-30b-a3b",
        REQUEST_TIMEOUT_SECONDS=5.0,
    )


@pytest.fixture
def sample_nvidia_success_response():
    return {
        "id": "chat-12345",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Resolved an issue on the login page where users were unable to click the submit button.",
                },
                "finish_reason": "stop",
            }
        ],
    }


@pytest.mark.asyncio
async def test_rewrite_service_success(mock_settings, sample_nvidia_success_response):
    """Test successful rewrite using mock HTTP response."""
    mock_response = httpx.Response(
        status_code=200,
        json=sample_nvidia_success_response,
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    service = RewriteService(settings=mock_settings, client=mock_client)
    rewritten, status_flag = await service.rewrite_daily_report("fixed bug in login page")

    assert status_flag == "success"
    assert rewritten == "Resolved an issue on the login page where users were unable to click the submit button."
    mock_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_rewrite_service_clarification(mock_settings):
    """Test clarification response detection."""
    clarification_payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Clarification needed: The activity description is ambiguous. Please specify which module was updated.",
                }
            }
        ]
    }
    mock_response = httpx.Response(
        status_code=200,
        json=clarification_payload,
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    service = RewriteService(settings=mock_settings, client=mock_client)
    rewritten, status_flag = await service.rewrite_daily_report("did some work on the stuff")

    assert status_flag == "needs_clarification"
    assert "Clarification needed:" in rewritten


@pytest.mark.asyncio
async def test_rewrite_service_question_input(mock_settings):
    """Test that question-phrased input is rewritten as a work report rather than answered."""
    question_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Working on deploying the codebase to Vercel and determining the necessary configuration files.",
                }
            }
        ]
    }
    mock_response = httpx.Response(
        status_code=200,
        json=question_response,
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    service = RewriteService(settings=mock_settings, client=mock_client)
    rewritten, status_flag = await service.rewrite_daily_report(
        "now these code i will deploy in vercel what files i need to add"
    )

    assert status_flag == "success"
    assert "deploying the codebase to Vercel" in rewritten
    assert "package.json" not in rewritten  # Asserts it did not give a tutorial / list files


@pytest.mark.asyncio
async def test_rewrite_service_missing_api_key():
    """Test that missing or empty API key raises AIAuthenticationError."""
    empty_key_settings = Settings(NVIDIA_API_KEY="")
    service = RewriteService(settings=empty_key_settings)

    with pytest.raises(AIAuthenticationError) as exc_info:
        await service.rewrite_daily_report("worked on task")

    assert "NVIDIA API key is not configured" in exc_info.value.message


@pytest.mark.asyncio
async def test_rewrite_service_unauthorized(mock_settings):
    """Test that HTTP 401 raises AIAuthenticationError."""
    mock_response = httpx.Response(
        status_code=401,
        text="Unauthorized",
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    service = RewriteService(settings=mock_settings, client=mock_client)

    with pytest.raises(AIAuthenticationError) as exc_info:
        await service.rewrite_daily_report("some description")

    assert "Invalid or unauthorized" in exc_info.value.message


@pytest.mark.asyncio
async def test_rewrite_service_upstream_500(mock_settings):
    """Test that upstream HTTP 500 error raises AIUpstreamError."""
    mock_response = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    service = RewriteService(settings=mock_settings, client=mock_client)

    with pytest.raises(AIUpstreamError) as exc_info:
        await service.rewrite_daily_report("some description")

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_rewrite_service_timeout(mock_settings):
    """Test that request timeout raises AITimeoutError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))

    service = RewriteService(settings=mock_settings, client=mock_client)

    with pytest.raises(AITimeoutError) as exc_info:
        await service.rewrite_daily_report("some description")

    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_rewrite_service_network_error(mock_settings):
    """Test that network connection errors raise AIUpstreamError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Failed to resolve host"))

    service = RewriteService(settings=mock_settings, client=mock_client)

    with pytest.raises(AIUpstreamError) as exc_info:
        await service.rewrite_daily_report("some description")

    assert "Network error" in exc_info.value.message


@pytest.mark.asyncio
async def test_rewrite_service_empty_choices(mock_settings):
    """Test that empty choices in response raises AIUpstreamError."""
    mock_response = httpx.Response(
        status_code=200,
        json={"choices": []},
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    service = RewriteService(settings=mock_settings, client=mock_client)

    with pytest.raises(AIUpstreamError) as exc_info:
        await service.rewrite_daily_report("some description")

    assert "empty choice list" in exc_info.value.message


def test_clean_output():
    """Test output stripping of quotes and markdown blocks."""
    # Double quotes
    assert RewriteService._clean_output('"Completed code review."') == "Completed code review."
    # Single quotes
    assert RewriteService._clean_output("'Completed code review.'") == "Completed code review."
    # Markdown code blocks
    markdown_wrapped = "```\nImplemented the requested payment gateway webhook handler.\n```"
    assert (
        RewriteService._clean_output(markdown_wrapped)
        == "Implemented the requested payment gateway webhook handler."
    )
    # Surrounding whitespace
    assert RewriteService._clean_output("   Fixed bug.   ") == "Fixed bug."

