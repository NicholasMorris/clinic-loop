"""Guard boundary: FastAPI dependency that enforces guard rules on outbound messages."""

from dataclasses import dataclass
from typing import Any, Literal

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from clinicloop.compliance.guard.core import check
from clinicloop.compliance.rulesets import RulesetNotImplemented, load_ruleset

from .schemas.message import MessageCreate

JURISDICTION_SOURCE_HEADER = "X-Jurisdiction-Source"


class GuardRejection(Exception):
    """Exception raised when message is rejected by guard."""

    def __init__(self, status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        """Initialize GuardRejection.

        Args:
            status_code: HTTP status code.
            body: Response body as dict.
            headers: Optional response headers.
        """
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}
        super().__init__(f"Guard rejected with status {status_code}")


def guard_rejection_handler(request: Request, exc: GuardRejection) -> JSONResponse:
    """Handle GuardRejection exceptions.

    Args:
        request: The request.
        exc: The GuardRejection exception.

    Returns:
        JSONResponse with the exception's status code, body, and headers.
    """
    return JSONResponse(exc.body, status_code=exc.status_code, headers=exc.headers)


def register_guard_handler(app: FastAPI) -> None:
    """Register the guard rejection exception handler on the app.

    Args:
        app: The FastAPI application.
    """
    app.add_exception_handler(GuardRejection, guard_rejection_handler)


@dataclass(frozen=True)
class GuardDecision:
    """Decision from the guard check.

    Attributes:
        verdict: The GuardVerdict from the guard check.
        jurisdiction: The jurisdiction that was used.
        jurisdiction_source: Source of the jurisdiction ("request" or "default_au").
    """

    verdict: Any  # GuardVerdict type, but avoiding circular import
    jurisdiction: str
    jurisdiction_source: Literal["request", "default_au"]


def build_block_response(
    jurisdiction: str, jurisdiction_source: str, verdict: Any
) -> dict[str, Any]:
    """Build the response body for a blocked message.

    Args:
        jurisdiction: The jurisdiction code.
        jurisdiction_source: Source of jurisdiction ("request" or "default_au").
        verdict: The GuardVerdict.

    Returns:
        Response body dict.

    Raises:
        NotImplementedError: Placeholder for red commit.
    """
    raise NotImplementedError()  # pragma: no cover


async def enforce_guard(request: Request, payload: MessageCreate) -> GuardDecision:
    """FastAPI dependency that enforces guard rules on message.

    Reads jurisdiction from the request payload or applies AU default.
    Loads the ruleset and checks the message against it.
    If blocked, raises GuardRejection with 422.
    If jurisdiction is uk or nz, raises GuardRejection with 501.

    Args:
        request: The request object.
        payload: The MessageCreate payload.

    Returns:
        GuardDecision with the verdict and jurisdiction information.

    Raises:
        GuardRejection: If message is blocked or ruleset is not implemented.
    """
    # This is a pass-through stub for the red commit
    return GuardDecision(
        verdict=None,  # Will be set in green commit
        jurisdiction="au",
        jurisdiction_source="default_au",
    )
