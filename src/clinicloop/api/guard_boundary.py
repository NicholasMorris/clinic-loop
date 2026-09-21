"""Guard boundary: FastAPI dependency that enforces guard rules on outbound messages."""

from dataclasses import dataclass
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from clinicloop.compliance.guard.core import check
from clinicloop.compliance.guard.matches import find_matches
from clinicloop.compliance.rulesets import RulesetNotImplemented, load_ruleset

from .schemas.message import MessageCreate

JURISDICTION_SOURCE_HEADER = "X-Jurisdiction-Source"


class GuardRejection(Exception):
    """Exception raised when message is rejected by guard."""

    def __init__(
        self, status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None
    ) -> None:
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


def guard_rejection_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle GuardRejection exceptions.

    Args:
        request: The request.
        exc: The GuardRejection exception.

    Returns:
        JSONResponse with the exception's status code, body, and headers.
    """
    assert isinstance(exc, GuardRejection)
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
    jurisdiction: str, jurisdiction_source: str, verdict: Any, ruleset: Any
) -> dict[str, Any]:
    """Build the response body for a blocked message.

    Args:
        jurisdiction: The jurisdiction code.
        jurisdiction_source: Source of jurisdiction ("request" or "default_au").
        verdict: The GuardVerdict with rule_ids and text_sha256.
        ruleset: The ruleset used for the check.

    Returns:
        Response body dict with rule_ids, jurisdiction, ruleset_version, and matches.
    """
    # Find matches to include in response (empty list for now)
    matches_list: list[dict[str, Any]] = []

    return {
        "code": "GuardBlocked",
        "rule_ids": list(verdict.rule_ids),
        "jurisdiction": jurisdiction,
        "jurisdiction_source": jurisdiction_source,
        "ruleset_version": verdict.ruleset_version,
        "matches": matches_list,
    }


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
    # Record guard trace if tracking is enabled
    if hasattr(request.app.state, "guard_trace") and isinstance(
        request.app.state.guard_trace, list
    ):
        request.app.state.guard_trace.append("guard")

    # Determine jurisdiction and source
    if payload.jurisdiction:
        jurisdiction = payload.jurisdiction.lower()
        jurisdiction_source: Literal["request", "default_au"] = "request"
    else:
        jurisdiction = "au"
        jurisdiction_source = "default_au"

    # Try to load the ruleset
    try:
        ruleset = load_ruleset(jurisdiction)
    except RulesetNotImplemented:
        # UK and NZ return 501
        raise GuardRejection(
            status_code=501,
            body={
                "code": "RulesetNotImplemented",
                "jurisdiction": jurisdiction,
                "jurisdiction_source": jurisdiction_source,
            },
            headers={JURISDICTION_SOURCE_HEADER: jurisdiction_source},
        )
    except ValueError:
        # Unknown jurisdiction returns 400
        raise GuardRejection(
            status_code=400,
            body={
                "code": "UnknownJurisdiction",
                "jurisdiction": jurisdiction,
                "jurisdiction_source": jurisdiction_source,
            },
            headers={JURISDICTION_SOURCE_HEADER: jurisdiction_source},
        )

    # Build the thread for the guard check (single assistant message with the body)
    thread = [{"role": "assistant", "text": payload.body}]

    # Run the guard check
    verdict = check(thread, jurisdiction, ruleset)

    # If blocked, raise GuardRejection with 422
    if not verdict.allowed:
        # Find matches in the normalised text
        matches = find_matches(payload.body, ruleset)
        matches_list = [{"rule_id": m.rule_id, "start": m.start, "end": m.end} for m in matches]

        raise GuardRejection(
            status_code=422,
            body={
                "code": "GuardBlocked",
                "rule_ids": list(verdict.rule_ids),
                "jurisdiction": jurisdiction,
                "jurisdiction_source": jurisdiction_source,
                "ruleset_version": verdict.ruleset_version,
                "matches": matches_list,
            },
            headers={JURISDICTION_SOURCE_HEADER: jurisdiction_source},
        )

    # Allowed - stash the decision in request state and return it
    decision = GuardDecision(
        verdict=verdict,
        jurisdiction=jurisdiction,
        jurisdiction_source=jurisdiction_source,
    )
    request.state.guard_decision = decision

    return decision
