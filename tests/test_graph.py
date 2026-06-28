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
        request_id="REQ-GRAPH",
        company_id="COMPANY-DEMO",
        used_policy_name="demo_procurement_validation",
        risk_level=risk_level,
        issues=issues,
    )


def make_company_config() -> CompanyConfig:
    return load_company_config(Path("configs/companies/company_demo.json"))


def make_initial_state(
    company_config: CompanyConfig,
    validation_result: ValidationResult,
) -> ProcurementState:
    return {
        "quote_input": load_quote_comparison(
            Path("data/sample_inputs/quote_comparison.json"),
        ),
        "company_config": company_config,
        "validation_result": validation_result,
    }


def test_graph_routes_normal_validation_to_tco() -> None:
    initial_state = make_initial_state(
        make_company_config(),
        make_validation_result("normal"),
    )

    result = graph.invoke(initial_state)

    assert result["path_trace"] == ("route_validation", "tco_calculation")
    assert result["routing_result"].selected_route == "proceed_tco"
    assert result["tco_result"].company_id == "COMPANY-DEMO"
    assert "human_review_result" not in result
    assert "ocr_reparse_result" not in result


def test_graph_routes_warning_validation_to_human_review_request() -> None:
    initial_state = make_initial_state(
        make_company_config(),
        make_validation_result("warning"),
    )

    result = graph.invoke(initial_state)

    assert result["path_trace"] == (
        "route_validation",
        "human_review_request",
    )
    assert result["routing_result"].selected_route == "request_human_review"
    assert result["human_review_result"].status == "awaiting_human_review"
    assert result["human_review_result"].issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)
    assert "tco_result" not in result
    assert "ocr_reparse_result" not in result


def test_graph_routes_critical_validation_to_ocr_reparse() -> None:
    initial_state = make_initial_state(
        make_company_config(),
        make_validation_result("critical"),
    )

    result = graph.invoke(initial_state)

    assert result["path_trace"] == ("route_validation", "ocr_reparse")
    assert result["routing_result"].selected_route == "reparse_ocr"
    assert result["ocr_reparse_result"].status == "ocr_reparse_requested"
    assert result["ocr_reparse_result"].issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)
    assert "tco_result" not in result
    assert "human_review_result" not in result
