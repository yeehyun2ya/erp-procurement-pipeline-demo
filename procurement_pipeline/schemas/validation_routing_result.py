from typing import Literal

from pydantic import BaseModel, ConfigDict

from procurement_pipeline.schemas.validation_result import RiskLevel


ValidationRouteAction = Literal[
    "proceed_tco",
    "request_human_review",
    "reparse_ocr",
]
HumanReviewStatus = Literal["awaiting_human_review"]
OcrReparseStatus = Literal["ocr_reparse_requested"]


class ValidationRoutingResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    used_policy_name: str
    risk_level: RiskLevel
    selected_route: ValidationRouteAction
    route_reason: str
    issue_codes: tuple[str, ...]


class OcrReparseResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    risk_level: RiskLevel
    status: OcrReparseStatus
    reparse_reason: str
    issue_codes: tuple[str, ...]


class HumanReviewRequestResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    risk_level: RiskLevel
    status: HumanReviewStatus
    review_reason: str
    issue_codes: tuple[str, ...]
