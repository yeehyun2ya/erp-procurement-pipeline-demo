from pathlib import Path

import pytest

from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.tco_calculation import (
    TcoCompanyConfigMismatchError,
    calculate_supplier_tco,
)


QUOTE_SAMPLE_PATH = Path("data/sample_inputs/quote_comparison.json")
COMPANY_CONFIG_SAMPLE_PATH = Path("configs/companies/company_demo.json")


def test_calculate_supplier_tco_returns_supplier_costs_with_default_weights() -> None:
    # 준비: 배송비와 기타 비용이 포함된 sample 견적과 TCO 정책을 불러옵니다.
    quote_input = load_quote_comparison(QUOTE_SAMPLE_PATH)
    company_config = load_company_config(COMPANY_CONFIG_SAMPLE_PATH)

    # 실행: 공급사별 TCO를 계산합니다.
    result = calculate_supplier_tco(quote_input, company_config)

    # 검증: 입력 식별자와 정책 이름을 유지하고, 견적 수만큼 결과를 만듭니다.
    assert result.request_id == "PR-2026-0001"
    assert result.company_id == "COMPANY-DEMO"
    assert result.used_policy_name == "demo_procurement_validation"
    assert len(result.supplier_results) == len(quote_input.quotes)

    results_by_supplier = {
        supplier_result.supplier_id: supplier_result
        for supplier_result in result.supplier_results
    }
    alpha_result = results_by_supplier["SUP-ALPHA"]
    assert alpha_result.supplier_id == "SUP-ALPHA"
    assert alpha_result.supplier_name == "Alpha Trading"
    assert alpha_result.base_item_cost == 21_250.0
    assert alpha_result.shipping_fee == 30_000.0
    assert alpha_result.other_costs == 10_000.0
    assert alpha_result.tco_amount == 61_250.0

    bravo_result = results_by_supplier["SUP-BRAVO"]
    assert bravo_result.base_item_cost == 19_750.0
    assert bravo_result.shipping_fee == 45_000.0
    assert bravo_result.other_costs == 15_000.0
    assert bravo_result.tco_amount == 79_750.0

    charlie_result = results_by_supplier["SUP-CHARLIE"]
    assert charlie_result.base_item_cost == 23_000.0
    assert charlie_result.shipping_fee == 0.0
    assert charlie_result.other_costs == 20_000.0
    assert charlie_result.tco_amount == 43_000.0


def test_calculate_supplier_tco_applies_config_weights() -> None:
    # 준비: TCO 계수가 1이 아닌 회사 config를 만듭니다.
    quote_input = load_quote_comparison(QUOTE_SAMPLE_PATH)
    company_config = load_company_config(COMPANY_CONFIG_SAMPLE_PATH)
    weighted_config = company_config.model_copy(
        update={
            "tco_policy": company_config.tco_policy.model_copy(
                update={
                    "unit_price_weight": 1.2,
                    "shipping_fee_weight": 0.5,
                    "other_costs_weight": 2.0,
                }
            )
        }
    )

    # 실행: config의 계수를 반영해 공급사별 TCO를 계산합니다.
    result = calculate_supplier_tco(quote_input, weighted_config)

    # 검증: 단가*수량, 배송비, 기타 비용에 각각 다른 계수가 적용됩니다.
    alpha_result = result.supplier_results[0]
    assert alpha_result.base_item_cost == 21_250.0
    assert alpha_result.tco_amount == pytest.approx(60_500.0)


def test_calculate_supplier_tco_rejects_company_id_mismatch() -> None:
    # 준비: 견적의 company_id와 다른 company_id를 가진 config를 만듭니다.
    quote_input = load_quote_comparison(QUOTE_SAMPLE_PATH)
    company_config = load_company_config(COMPANY_CONFIG_SAMPLE_PATH)
    mismatched_config = company_config.model_copy(update={"company_id": "OTHER-COMPANY"})

    # 실행 / 검증: 서로 다른 회사를 가리키면 TCO를 계산하지 않고 명확한 오류를 냅니다.
    with pytest.raises(TcoCompanyConfigMismatchError) as exc_info:
        calculate_supplier_tco(quote_input, mismatched_config)

    assert exc_info.value.quote_company_id == "COMPANY-DEMO"
    assert exc_info.value.config_company_id == "OTHER-COMPANY"
