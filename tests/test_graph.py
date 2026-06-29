from pathlib import Path
from typing import assert_never

from procurement_pipeline.graph import graph
from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.schemas.company_config import CompanyConfig
from procurement_pipeline.schemas.validation_result import (
    IssueSeverity,
    RiskLevel,
    ValidationIssue,
    ValidationResult,
)
from procurement_pipeline.state import ProcurementState


COMPANY_A_CONFIG_PATH = Path("configs/companies/company_a.json")
COMPANY_B_CONFIG_PATH = Path("configs/companies/company_b.json")
COMPANY_C_CONFIG_PATH = Path("configs/companies/company_c.json")
COMPANY_A_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_a.json")
COMPANY_B_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_b.json")
COMPANY_C_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_c.json")


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


def make_validation_result(
    risk_level: RiskLevel,
    company_id: str = "COMPANY-DEMO",
) -> ValidationResult:
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
        request_id="REQ-GRAPH",
        company_id=company_id,
        used_policy_name="demo_procurement_validation",
        risk_level=risk_level,
        issues=issues,
    )


def make_initial_state(
    quote_path: Path,
    company_config: CompanyConfig,
    validation_result: ValidationResult,
) -> ProcurementState:
    return {
        "quote_input": load_quote_comparison(quote_path),
        "company_config": company_config,
        "validation_result": validation_result,
    }


def test_graph_routes_company_a_normal_validation_to_tco_after_rfq_difference() -> None:
    # 준비: A사는 RFQ 차이가 허용 범위 안인 normal 검증 결과를 사용합니다.
    company_config = load_company_config(COMPANY_A_CONFIG_PATH)
    initial_state = make_initial_state(
        COMPANY_A_INPUT_PATH,
        company_config,
        make_validation_result("normal", company_config.company_id),
    )

    # 실행: graph를 실제로 호출합니다.
    result = graph.invoke(initial_state)

    # 검증: 공통 검증 뒤 RFQ 차이 검증을 거쳐 TCO로 갑니다.
    assert result["path_trace"] == (
        "route_validation",
        "rfq_difference",
        "tco_calculation",
    )
    assert result["rfq_difference_result"].selected_route == "proceed_tco"
    assert result["tco_result"].company_id == "COMPANY-A"
    assert "rfq_resend_result" not in result
    assert "human_review_result" not in result
    assert "ocr_reparse_result" not in result


def test_graph_routes_company_b_normal_validation_to_rfq_resend() -> None:
    # 준비: B사는 RFQ 차이가 허용 범위 초과이면 재전송으로 보냅니다.
    company_config = load_company_config(COMPANY_B_CONFIG_PATH)
    initial_state = make_initial_state(
        COMPANY_B_INPUT_PATH,
        company_config,
        make_validation_result("normal", company_config.company_id),
    )

    # 실행: graph를 실제로 호출합니다.
    result = graph.invoke(initial_state)

    # 검증: 회사별 route는 RFQ 차이 단계 이후에 갈라집니다.
    assert result["path_trace"] == (
        "route_validation",
        "rfq_difference",
        "rfq_resend",
    )
    assert result["rfq_difference_result"].selected_route == "resend_rfq"
    assert result["rfq_resend_result"].status == "rfq_resend_requested"
    assert "tco_result" not in result
    assert "human_review_result" not in result


def test_graph_routes_company_c_normal_validation_to_human_review() -> None:
    # 준비: C사는 RFQ 차이가 허용 범위 초과이면 HITL로 보냅니다.
    company_config = load_company_config(COMPANY_C_CONFIG_PATH)
    initial_state = make_initial_state(
        COMPANY_C_INPUT_PATH,
        company_config,
        make_validation_result("normal", company_config.company_id),
    )

    # 실행: graph를 실제로 호출합니다.
    result = graph.invoke(initial_state)

    # 검증: 같은 견적 조건도 C사 config에서는 HITL로 갑니다.
    assert result["path_trace"] == (
        "route_validation",
        "rfq_difference",
        "human_review_request",
    )
    assert result["rfq_difference_result"].selected_route == "request_human_review"
    assert result["human_review_result"].status == "awaiting_human_review"
    assert result["human_review_result"].risk_level == "normal"
    assert result["human_review_result"].review_trigger == "rfq_difference"
    assert "tco_result" not in result
    assert "rfq_resend_result" not in result


def test_graph_routes_warning_validation_to_human_review_request() -> None:
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    initial_state = make_initial_state(
        Path("data/sample_inputs/quote_comparison.json"),
        company_config,
        make_validation_result("warning"),
    )

    result = graph.invoke(initial_state)

    assert result["path_trace"] == (
        "route_validation",
        "human_review_request",
    )
    assert result["routing_result"].selected_route == "request_human_review"
    assert result["human_review_result"].status == "awaiting_human_review"
    assert result["human_review_result"].review_trigger == "validation_risk"
    assert result["human_review_result"].issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)
    assert "rfq_difference_result" not in result
    assert "tco_result" not in result
    assert "ocr_reparse_result" not in result


def test_graph_routes_critical_validation_to_ocr_reparse() -> None:
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    initial_state = make_initial_state(
        Path("data/sample_inputs/quote_comparison.json"),
        company_config,
        make_validation_result("critical"),
    )

    result = graph.invoke(initial_state)

    assert result["path_trace"] == ("route_validation", "ocr_reparse")
    assert result["routing_result"].selected_route == "reparse_ocr"
    assert result["ocr_reparse_result"].status == "ocr_reparse_requested"
    assert result["ocr_reparse_result"].issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)
    assert "rfq_difference_result" not in result
    assert "tco_result" not in result
    assert "human_review_result" not in result
