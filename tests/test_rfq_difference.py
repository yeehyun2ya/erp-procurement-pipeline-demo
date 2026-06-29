from datetime import timedelta
from pathlib import Path

import pytest

from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison


COMPANY_A_CONFIG_PATH = Path("configs/companies/company_a.json")
COMPANY_B_CONFIG_PATH = Path("configs/companies/company_b.json")
COMPANY_C_CONFIG_PATH = Path("configs/companies/company_c.json")
COMPANY_A_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_a.json")
COMPANY_B_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_b.json")
COMPANY_C_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_c.json")


def test_rfq_difference_routes_company_a_within_tolerance_to_tco() -> None:
    from procurement_pipeline.nodes.rfq_difference import build_rfq_difference_result

    # 준비: A사는 sample 견적을 허용 범위 안으로 보는 config를 사용합니다.
    quote_input = load_quote_comparison(COMPANY_A_INPUT_PATH)
    company_config = load_company_config(COMPANY_A_CONFIG_PATH)

    # 실행: RFQ 원안과 공급업체 응답을 비교합니다.
    result = build_rfq_difference_result(quote_input, company_config)

    # 검증: 허용 범위 안이면 TCO로 진행합니다.
    assert result.selected_route == "proceed_tco"
    assert result.status == "within_tolerance"
    assert result.issue_codes == ()


def test_rfq_difference_routes_company_b_exceeded_tolerance_to_resend_rfq() -> None:
    from procurement_pipeline.nodes.rfq_difference import build_rfq_difference_result

    # 준비: B사는 같은 견적을 허용 범위 초과로 보는 config를 사용합니다.
    quote_input = load_quote_comparison(COMPANY_B_INPUT_PATH)
    company_config = load_company_config(COMPANY_B_CONFIG_PATH)

    # 실행: RFQ 원안과 공급업체 응답을 비교합니다.
    result = build_rfq_difference_result(quote_input, company_config)

    # 검증: 허용 범위 초과 시 RFQ 재전송 route를 선택합니다.
    assert result.selected_route == "resend_rfq"
    assert result.status == "tolerance_exceeded"
    assert "RFQ_PRICE_TOLERANCE_EXCEEDED" in result.issue_codes


def test_rfq_difference_routes_company_c_exceeded_tolerance_to_human_review() -> None:
    from procurement_pipeline.nodes.rfq_difference import build_rfq_difference_result

    # 준비: C사는 같은 견적을 허용 범위 초과 시 사람 검토로 보내는 config를 사용합니다.
    quote_input = load_quote_comparison(COMPANY_C_INPUT_PATH)
    company_config = load_company_config(COMPANY_C_CONFIG_PATH)

    # 실행: RFQ 원안과 공급업체 응답을 비교합니다.
    result = build_rfq_difference_result(quote_input, company_config)

    # 검증: 허용 범위 초과 시 HITL route를 선택합니다.
    assert result.selected_route == "request_human_review"
    assert result.status == "tolerance_exceeded"
    assert "RFQ_DELIVERY_TOLERANCE_EXCEEDED" in result.issue_codes


def test_rfq_human_review_result_keeps_rfq_trigger_with_normal_risk() -> None:
    from procurement_pipeline.nodes.rfq_difference import (
        build_rfq_difference_result,
        build_rfq_human_review_request_result,
    )

    # 준비: 공통 검증은 normal이지만 RFQ 납기 차이가 허용 범위를 넘는 C사 결과를 만듭니다.
    quote_input = load_quote_comparison(COMPANY_C_INPUT_PATH)
    company_config = load_company_config(COMPANY_C_CONFIG_PATH)
    rfq_result = build_rfq_difference_result(quote_input, company_config)

    # 실행: RFQ 차이 때문에 사람 검토 요청 결과를 만듭니다.
    review_result = build_rfq_human_review_request_result(rfq_result, "normal")

    # 검증: risk_level은 유지하고, HITL로 간 이유는 RFQ trigger로 따로 남깁니다.
    assert review_result.risk_level == "normal"
    assert review_result.review_trigger == "rfq_difference"
    assert review_result.issue_codes == ("RFQ_DELIVERY_TOLERANCE_EXCEEDED",)


def test_rfq_difference_treats_exact_boundaries_as_within_tolerance() -> None:
    from procurement_pipeline.nodes.rfq_difference import build_rfq_difference_result

    # 준비: A사 config의 가격/납기 허용 경계값에 딱 맞는 견적을 만듭니다.
    quote_input = load_quote_comparison(COMPANY_A_INPUT_PATH)
    company_config = load_company_config(COMPANY_A_CONFIG_PATH)
    policy = company_config.approval_route_policy.rfq_difference_policy
    boundary_unit_price = int(
        quote_input.rfq_terms.expected_unit_price
        * (1 + policy.price_tolerance_ratio),
    )
    boundary_delivery_date = (
        quote_input.rfq_terms.expected_delivery_date
        + timedelta(days=policy.delivery_tolerance_days)
    )
    boundary_quote = quote_input.quotes[0].model_copy(
        update={
            "unit_price": boundary_unit_price,
            "delivery_date": boundary_delivery_date,
        },
    )
    boundary_input = quote_input.model_copy(update={"quotes": (boundary_quote,)})

    # 실행: 경계값 견적을 비교합니다.
    result = build_rfq_difference_result(boundary_input, company_config)

    # 검증: 경계값은 허용 범위 안으로 처리합니다.
    assert result.selected_route == "proceed_tco"
    assert result.issue_codes == ()


def test_rfq_difference_rejects_company_id_mismatch() -> None:
    from procurement_pipeline.nodes.rfq_difference import (
        RfqDifferenceCompanyConfigMismatchError,
        build_rfq_difference_result,
    )

    # 준비: 견적과 다른 회사 config를 함께 사용합니다.
    quote_input = load_quote_comparison(COMPANY_A_INPUT_PATH)
    company_config = load_company_config(COMPANY_B_CONFIG_PATH)

    # 실행 / 검증: 회사가 다르면 RFQ 차이를 계산하지 않습니다.
    with pytest.raises(RfqDifferenceCompanyConfigMismatchError) as exc_info:
        build_rfq_difference_result(quote_input, company_config)

    assert exc_info.value.quote_company_id == "COMPANY-A"
    assert exc_info.value.config_company_id == "COMPANY-B"
