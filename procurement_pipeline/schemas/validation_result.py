from pydantic import BaseModel, ConfigDict


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    issue_code: str
    severity: str
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
    risk_level: str
    issues: tuple[ValidationIssue, ...]
