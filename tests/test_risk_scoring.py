from procurement_pipeline.nodes.risk_scoring import (
    score_issues_risk,
    score_validation_risk,
)
from procurement_pipeline.schemas.validation_result import (
    IssueSeverity,
    ValidationIssue,
    ValidationResult,
)


def make_issue(
    severity: IssueSeverity,
    issue_code: str = "TEST_VALIDATION_ISSUE",
) -> ValidationIssue:
    return ValidationIssue(
        issue_code=issue_code,
        severity=severity,
        message="Test validation issue.",
        related_supplier_id="SUP-TEST",
        related_field="unit_price",
        observed_value=1_200.0,
        reference_value=900.0,
        score=3.5,
    )


def test_score_issues_risk_returns_normal_without_issues() -> None:
    # 준비: 검증 issue가 하나도 없는 결과를 준비합니다.
    issues: tuple[ValidationIssue, ...] = ()

    # 실행: issue 목록을 하나의 risk level로 요약합니다.
    risk_level = score_issues_risk(issues)

    # 검증: issue가 없으면 routing에 넘길 위험 신호도 normal입니다.
    assert risk_level == "normal"


def test_score_issues_risk_returns_warning_for_one_warning_issue() -> None:
    # 준비: 담당자 확인이 필요할 수 있는 warning issue 하나를 준비합니다.
    issues = (make_issue("warning"),)

    # 실행: issue severity를 risk level로 요약합니다.
    risk_level = score_issues_risk(issues)

    # 검증: warning issue 하나는 전체 위험도를 warning으로 만듭니다.
    assert risk_level == "warning"


def test_score_issues_risk_returns_critical_for_critical_issue() -> None:
    # 준비: 심각한 검토가 필요한 critical issue 하나를 준비합니다.
    issues = (make_issue("critical"),)

    # 실행: issue severity를 risk level로 요약합니다.
    risk_level = score_issues_risk(issues)

    # 검증: critical issue가 하나라도 있으면 전체 위험도도 critical입니다.
    assert risk_level == "critical"


def test_score_issues_risk_returns_critical_when_warning_and_critical_are_mixed() -> None:
    # 준비: warning issue와 critical issue가 섞인 목록을 준비합니다.
    issues = (
        make_issue("warning", "WARNING_ISSUE"),
        make_issue("critical", "CRITICAL_ISSUE"),
    )

    # 실행: 여러 issue를 하나의 risk level로 요약합니다.
    risk_level = score_issues_risk(issues)

    # 검증: 더 심각한 critical 신호가 전체 위험도를 결정합니다.
    assert risk_level == "critical"


def test_score_issues_risk_escalates_multiple_warnings_to_critical() -> None:
    # 준비: 각각은 warning이지만 여러 개 누적된 issue 목록을 준비합니다.
    issues = (
        make_issue("warning", "FIRST_WARNING"),
        make_issue("warning", "SECOND_WARNING"),
    )

    # 실행: issue 개수와 severity를 함께 반영합니다.
    risk_level = score_issues_risk(issues)

    # 검증: warning이 두 개 이상이면 공통 기준상 critical로 올립니다.
    assert risk_level == "critical"


def test_score_validation_risk_updates_validation_result_risk_level() -> None:
    # 준비: risk_level이 아직 normal인 ValidationResult에 warning issue를 담습니다.
    issue = make_issue("warning")
    validation_result = ValidationResult(
        request_id="REQ-TEST",
        company_id="COMPANY-DEMO",
        used_policy_name="demo_policy",
        risk_level="normal",
        issues=(issue,),
    )

    # 실행: ValidationResult의 issue 목록을 기준으로 risk_level을 다시 계산합니다.
    scored_result = score_validation_risk(validation_result)

    # 검증: 기존 issue와 식별자는 유지하고 risk_level만 일관되게 채웁니다.
    assert scored_result.request_id == "REQ-TEST"
    assert scored_result.company_id == "COMPANY-DEMO"
    assert scored_result.used_policy_name == "demo_policy"
    assert scored_result.issues == (issue,)
    assert scored_result.risk_level == "warning"
