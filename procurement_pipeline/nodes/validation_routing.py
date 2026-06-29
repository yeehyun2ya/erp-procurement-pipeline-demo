from dataclasses import dataclass
from typing import assert_never

from procurement_pipeline.schemas.validation_result import (
    RiskLevel,
    ValidationResult,
)
from procurement_pipeline.schemas.validation_routing_result import (
    HumanReviewRequestResult,
    OcrReparseResult,
    ValidationRouteAction,
    ValidationRoutingResult,
)


@dataclass(frozen=True, slots=True)
class MissingHumanReviewEvidenceError(RuntimeError):
    request_id: str

    def __str__(self) -> str:
        return f"Human review evidence is required: {self.request_id}"


def build_validation_routing_result(
    validation_result: ValidationResult,
) -> ValidationRoutingResult:
    selected_route = _select_common_route(validation_result.risk_level)
    return ValidationRoutingResult(
        request_id=validation_result.request_id,
        company_id=validation_result.company_id,
        used_policy_name=validation_result.used_policy_name,
        risk_level=validation_result.risk_level,
        selected_route=selected_route,
        route_reason=(
            f"{validation_result.risk_level} risk uses common "
            f"{selected_route} validation route."
        ),
        issue_codes=_issue_codes(validation_result),
    )


def build_ocr_reparse_result(
    validation_result: ValidationResult,
) -> OcrReparseResult:
    issue_codes = _issue_codes(validation_result)
    return OcrReparseResult(
        request_id=validation_result.request_id,
        company_id=validation_result.company_id,
        risk_level=validation_result.risk_level,
        status="ocr_reparse_requested",
        reparse_reason=(
            f"{validation_result.risk_level} risk requires OCR reparse mock."
        ),
        issue_codes=issue_codes,
    )


def build_human_review_request_result(
    validation_result: ValidationResult,
) -> HumanReviewRequestResult:
    issue_codes = _issue_codes(validation_result)
    if issue_codes:
        return HumanReviewRequestResult(
            request_id=validation_result.request_id,
            company_id=validation_result.company_id,
            risk_level=validation_result.risk_level,
            status="awaiting_human_review",
            review_trigger="validation_risk",
            review_reason=(
                f"{validation_result.risk_level} risk requires HITL mock review."
            ),
            issue_codes=issue_codes,
        )

    raise MissingHumanReviewEvidenceError(request_id=validation_result.request_id)


def _select_common_route(risk_level: RiskLevel) -> ValidationRouteAction:
    match risk_level:
        case "normal":
            return "proceed_tco"
        case "warning":
            return "request_human_review"
        case "critical":
            return "reparse_ocr"
        case unreachable:
            assert_never(unreachable)


def _issue_codes(validation_result: ValidationResult) -> tuple[str, ...]:
    return tuple(issue.issue_code for issue in validation_result.issues)
