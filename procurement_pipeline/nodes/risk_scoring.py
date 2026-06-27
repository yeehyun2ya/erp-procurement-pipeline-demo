from typing import Final, assert_never

from procurement_pipeline.schemas.validation_result import (
    RiskLevel,
    ValidationIssue,
    ValidationResult,
)


WARNING_ISSUE_CRITICAL_COUNT: Final = 2


def score_issues_risk(issues: tuple[ValidationIssue, ...]) -> RiskLevel:
    if not issues:
        return "normal"

    warning_issue_count = 0
    for issue in issues:
        match issue.severity:
            case "critical":
                return "critical"
            case "warning":
                warning_issue_count += 1
            case unreachable:
                assert_never(unreachable)

    if warning_issue_count >= WARNING_ISSUE_CRITICAL_COUNT:
        return "critical"

    return "warning"


def score_validation_risk(validation_result: ValidationResult) -> ValidationResult:
    return validation_result.model_copy(
        update={"risk_level": score_issues_risk(validation_result.issues)}
    )
