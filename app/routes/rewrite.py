import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.services.rewrite_service import (
    AIServiceError,
    AIAuthenticationError,
    AITimeoutError,
    AIUpstreamError,
    RewriteService,
    get_rewrite_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Daily Report Rewrite"])


class RewriteRequest(BaseModel):
    """Request payload for rewriting a daily report description."""

    description: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The employee's original daily report description to rewrite.",
        examples=["fixed bug in login page where user cant click submit button"],
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Daily report description cannot be empty or solely whitespace.")
        if len(stripped) < 3:
            raise ValueError("Daily report description must contain at least 3 characters.")
        return stripped


class RewriteResponse(BaseModel):
    """Response payload containing the rewritten daily report."""

    original: str = Field(
        ...,
        description="The original daily report description submitted.",
    )
    rewritten: str = Field(
        ...,
        description="The professionally rewritten report sentence or clarification request.",
    )
    status: str = Field(
        default="success",
        description="Result status: 'success' or 'needs_clarification'.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "original": "fixed bug in login page where user cant click submit button",
                "rewritten": "Resolved an issue on the login page that prevented users from clicking the submit button.",
                "status": "success",
            }
        }
    }


@router.post(
    "/rewrite-daily-report",
    response_model=RewriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Rewrite daily report into professional English",
    description=(
        "Accepts an employee's daily report description, corrects grammar and spelling, "
        "and rewrites it into clear, professional English without inventing any activities. "
        "Returns a clarification request if the input cannot be understood without guessing."
    ),
    responses={
        200: {"description": "Daily report successfully rewritten or clarification requested."},
        422: {"description": "Validation error (e.g. empty description, invalid input length)."},
        502: {"description": "Upstream NVIDIA AI service error."},
        503: {"description": "AI service authentication failure or configuration missing."},
        504: {"description": "Upstream AI service timeout."},
    },
)
async def rewrite_daily_report(
    request: RewriteRequest,
    service: RewriteService = Depends(get_rewrite_service),
) -> RewriteResponse:
    """Handles daily report rewrite requests."""
    logger.info("Received rewrite request. Length: %d chars.", len(request.description))

    try:
        rewritten_text, rewrite_status = await service.rewrite_daily_report(request.description)
        return RewriteResponse(
            original=request.description,
            rewritten=rewritten_text,
            status=rewrite_status,
        )
    except AIAuthenticationError as exc:
        logger.error("Authentication error: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except AITimeoutError as exc:
        logger.error("Timeout error: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=exc.message,
        ) from exc
    except AIUpstreamError as exc:
        logger.error("Upstream error: %s", exc.message)
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc
    except AIServiceError as exc:
        logger.error("General AI service error: %s", exc.message)
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

