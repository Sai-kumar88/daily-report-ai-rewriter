import logging
from typing import Optional, Tuple
import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict Employee Daily Work Report Rewriter, NOT a conversational assistant or Q&A chatbot.

CRITICAL RULES:
1. NEVER answer questions, provide tutorials, explain instructions, or give technical advice.
2. Even if the input is phrased as a question, conversational thought, or query, you must NEVER answer it. Instead, REWRITE it into a professional employee daily work activity or task report.
   - Example Input: "now these code i will deploy in vercel what files i need to add"
     Rewritten Output: "Working on deploying the codebase to Vercel and determining the necessary configuration files."
   - Example Input: "how to fix memory leak in worker"
     Rewritten Output: "Investigated memory leak issues in the background worker process."
3. Correct all spelling, grammar, punctuation, and informal shorthand.
4. Rewrite in crisp, professional business English (e.g. past tense for completed work or active task summary).
5. Strictly preserve the original work context and meaning. Never invent activities, tools, or facts not mentioned.
6. If the input is completely incoherent gibberish with no work context (e.g. "asdfghjk 1234"), return: "Clarification needed: [brief explanation]".
7. Return ONLY the rewritten sentence (or clarification notice). Never include conversational filler, greetings, bullet points, guides, or quotation marks."""


class AIServiceError(Exception):
    """Base exception for AI Service errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIAuthenticationError(AIServiceError):
    """Raised when the NVIDIA API key is invalid or missing."""

    def __init__(self, message: str = "NVIDIA API authentication failed. Please verify NVIDIA_API_KEY."):
        super().__init__(message, status_code=503)


class AITimeoutError(AIServiceError):
    """Raised when the AI service request times out."""

    def __init__(self, message: str = "Upstream AI model request timed out. Please try again later."):
        super().__init__(message, status_code=504)


class AIUpstreamError(AIServiceError):
    """Raised when the upstream AI service returns an unexpected error."""

    def __init__(self, message: str = "Upstream AI service encountered an error.", status_code: int = 502):
        super().__init__(message, status_code=status_code)


class RewriteService:
    """Service responsible for rewriting daily reports using NVIDIA AI NIM endpoint."""

    def __init__(self, settings: Optional[Settings] = None, client: Optional[httpx.AsyncClient] = None):
        self.settings = settings or get_settings()
        self._client = client
        self._owns_client = client is None

    async def get_client(self) -> httpx.AsyncClient:
        """Returns or creates the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS)
            self._owns_client = True
        elif self._owns_client and getattr(self._client, "is_closed", False) is True:
            self._client = httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client if owned by this service."""
        if self._owns_client and self._client and not self._client.is_closed:
            await self._client.aclose()

    @staticmethod
    def _clean_output(text: Optional[str]) -> str:
        """Strips wrapping quotes, markdown code fences, and excess whitespace from model output."""
        if not text:
            return ""
        cleaned = text.strip()
        # Remove surrounding markdown blocks if present
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                cleaned = "\n".join(lines[1:-1]).strip()
        # Remove repeated prompt prefix if echoed by model
        if "Daily report to rewrite:" in cleaned:
            cleaned = cleaned.split("Daily report to rewrite:")[-1].strip()
            if "\n\n" in cleaned:
                cleaned = cleaned.split("\n\n")[-1].strip()
        # Remove wrapping single or double quotes
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1].strip()
        return cleaned

    @staticmethod
    def _is_clarification_response(text: str) -> bool:
        """Detects if the AI output is requesting clarification rather than rewriting."""
        lowered = text.lower()
        clarification_markers = [
            "clarification needed",
            "needs clarification",
            "clarification required",
            "input requires clarification",
            "please clarify",
            "please provide more details",
        ]
        return any(marker in lowered for marker in clarification_markers)

    async def rewrite_daily_report(self, description: str) -> Tuple[str, str]:
        """Rewrites the employee daily report description into professional English.

        Args:
            description: The raw daily report text from the employee.

        Returns:
            A tuple of (rewritten_text, status) where status is either 'success' or 'needs_clarification'.

        Raises:
            AIAuthenticationError: If API key is not configured or rejected.
            AITimeoutError: If the upstream call times out.
            AIUpstreamError: If the upstream service fails.
        """
        api_key = self.settings.NVIDIA_API_KEY.strip()
        if not api_key or api_key == "your_nvidia_api_key_here":
            logger.error("NVIDIA API key is missing or not configured.")
            raise AIAuthenticationError(
                "NVIDIA API key is not configured. Please set a valid NVIDIA_API_KEY in the environment."
            )

        endpoint_url = f"{self.settings.NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.settings.NVIDIA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": description.strip()},
            ],
            "chat_template_kwargs": {"thinking": False},
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
        }

        client = await self.get_client()

        logger.info(
            "Calling NVIDIA AI endpoint for model: %s (input length: %d)",
            self.settings.NVIDIA_MODEL,
            len(description),
        )

        try:
            response = await client.post(
                endpoint_url,
                headers=headers,
                json=payload,
                timeout=self.settings.REQUEST_TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException as exc:
            logger.error("Timeout occurred while calling NVIDIA API: %s", str(exc))
            raise AITimeoutError() from exc
        except httpx.RequestError as exc:
            logger.error("Network error while connecting to NVIDIA API: %s", str(exc))
            raise AIUpstreamError(f"Network error connecting to AI service: {exc.__class__.__name__}") from exc

        if response.status_code == 401 or response.status_code == 403:
            logger.error("NVIDIA API authentication failure. Status: %d", response.status_code)
            raise AIAuthenticationError("Invalid or unauthorized NVIDIA API credentials.")

        if response.status_code != 200:
            logger.error(
                "NVIDIA API returned error status: %d, body: %s",
                response.status_code,
                response.text[:200],
            )
            raise AIUpstreamError(
                f"Upstream AI service error (HTTP {response.status_code}).",
                status_code=502,
            )

        try:
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                logger.error("NVIDIA API response contained no choices: %s", data)
                raise AIUpstreamError("AI service returned an empty choice list.")

            message = choices[0].get("message", {}) or {}
            content = message.get("content")
            if not content and "reasoning_content" in message:
                content = message.get("reasoning_content")

            cleaned_content = self._clean_output(content or "")

            if not cleaned_content:
                logger.error("AI service returned empty content.")
                raise AIUpstreamError("AI service returned an empty response.")

            status = "needs_clarification" if self._is_clarification_response(cleaned_content) else "success"
            return cleaned_content, status

        except (ValueError, KeyError) as exc:
            logger.error("Failed to parse NVIDIA API response JSON: %s", str(exc))
            raise AIUpstreamError("Failed to parse response from AI service.") from exc


_service_instance: Optional[RewriteService] = None


def get_rewrite_service() -> RewriteService:
    """Dependency provider returning singleton RewriteService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = RewriteService()
    return _service_instance
