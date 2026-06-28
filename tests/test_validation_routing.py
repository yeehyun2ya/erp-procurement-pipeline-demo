from pathlib import Path
from typing import assert_never

import pytest

from procurement_pipeline.nodes.validation_routing import (
    MissingHumanReviewEvidenceError,
    build_human_review_request_result,
    build_ocr_reparse_result,
    build_validation_routing_result,
)
from procurement_pipeline.schemas.validation_result import (
    IssueSeverity,
    RiskLevel,
    ValidationIssue,
    ValidationResult,
)
from procurement_pipeline.schemas.validation_routing_result import ValidationRouteAction


def make_issue(severity: IssueSeverity) -> ValidationIssue:
    return ValidationIssue(
        issue_code="UNIT_PRICE_ROBUST_OUTLIER",
        severity=severity,
        message="Supplier unit price may need common validation routing.",
        related_supplier_id="SUP-TEST",
        related_field="unit_price",
        observed_value=5_000.0,
        reference_value=885.0,
        score=4.2,
    )


def make_validation_result(risk_level: RiskLevel) -> ValidationResult:
    match risk_level:
        case "normal":
            issues: tuple[ValidationIssue, ...] = ()
        case "warning":
            issues = (make_issue("warning"),)
        case "critical":
            issues = (make_issue("critical"),)
        case unreachable:
            assert_never(unreachable)

    return ValidationResult(
        request_id="REQ-VALIDATION-ROUTE",
        company_id="COMPANY-DEMO",
        used_policy_name="demo_procurement_validation",
        risk_level=risk_level,
        issues=issues,
    )


def test_validation_routing_source_does_not_use_company_specific_policy() -> None:
    # 준비: 공통 검증 라우팅 source를 읽습니다.
    source_path = Path("procurement_pipeline/nodes/validation_routing.py")
    source_text = source_path.read_text(encoding="utf-8")

    # 실행: 회사별 tolerance/RFQ 라우팅 흔적을 찾습니다.
    forbidden_literals = (
        "A사",
        "B사",
        "C사",
        "COMPANY-A",
        "COMPANY-B",
        "COMPANY-C",
        "price_tolerance",
        "resend_rfq",
        "human_decision_routes",
    )
    matches = tuple(
        literal for literal in forbidden_literals if literal in source_text
    )

    # 검증: 이번 이슈는 회사별 분기가 아니라 공통 검증 분기만 다룹니다.
    assert matches == ()


def assert_common_risk_route(
    risk_level: RiskLevel,
    expected_route: ValidationRouteAction,
) -> None:
    validation_result = make_validation_result(risk_level)

    routing_result = build_validation_routing_result(validation_result)

    assert routing_result.request_id == "REQ-VALIDATION-ROUTE"
    assert routing_result.company_id == "COMPANY-DEMO"
    assert routing_result.risk_level == risk_level
    assert routing_result.selected_route == expected_route
    assert routing_result.issue_codes == tuple(
        issue.issue_code for issue in validation_result.issues
    )


def test_build_validation_routing_result_routes_normal_to_tco() -> None:
    assert_common_risk_route("normal", "proceed_tco")


def test_build_validation_routing_result_routes_warning_to_human_review() -> None:
    assert_common_risk_route("warning", "request_human_review")


def test_build_validation_routing_result_routes_critical_to_ocr_reparse() -> None:
    assert_common_risk_route("critical", "reparse_ocr")


def test_build_ocr_reparse_result_keeps_critical_evidence() -> None:
    # 준비: OCR 재파싱으로 보내야 할 critical validation 결과를 만듭니다.
    validation_result = make_validation_result("critical")

    # 실행: OCR 재파싱 mock 결과를 만듭니다.
    reparse_result = build_ocr_reparse_result(validation_result)

    # 검증: 실제 OCR 호출 없이 재파싱 판단 근거만 남깁니다.
    assert reparse_result.request_id == "REQ-VALIDATION-ROUTE"
    assert reparse_result.company_id == "COMPANY-DEMO"
    assert reparse_result.risk_level == "critical"
    assert reparse_result.issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)


def test_build_human_review_request_result_keeps_warning_evidence() -> None:
    # 준비: 사람이 사회적 맥락을 봐야 할 warning validation 결과를 만듭니다.
    validation_result = make_validation_result("warning")

    # 실행: HITL 요청 mock 결과를 만듭니다.
    review_result = build_human_review_request_result(validation_result)

    # 검증: approve/reject 결정 없이 사람 검토 요청 근거만 남깁니다.
    assert review_result.request_id == "REQ-VALIDATION-ROUTE"
    assert review_result.company_id == "COMPANY-DEMO"
    assert review_result.risk_level == "warning"
    assert review_result.issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)
    assert review_result.status == "awaiting_human_review"


def test_build_human_review_request_result_requires_evidence() -> None:
    # 준비: 근거 없이 사람이 볼 필요가 없는 normal validation 결과를 만듭니다.
    validation_result = make_validation_result("normal")

    # 실행 / 검증: HITL 요청은 검증 근거가 있을 때만 만들 수 있습니다.
    with pytest.raises(MissingHumanReviewEvidenceError) as exc_info:
        build_human_review_request_result(validation_result)

    assert exc_info.value.request_id == "REQ-VALIDATION-ROUTE"
