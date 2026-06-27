from typing import Literal

from pydantic import BaseModel, ConfigDict


IssueSeverity = Literal["warning", "critical"]
RiskLevel = Literal["normal", "warning", "critical"]


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    issue_code: str
    severity: IssueSeverity
    message: str
    related_supplier_id: str
    related_field: str
    observed_value: float
    reference_value: float
    score: float


class ValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    company_id: str
    used_policy_name: str
    risk_level: RiskLevel
    issues: tuple[ValidationIssue, ...]
