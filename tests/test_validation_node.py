from datetime import date
from pathlib import Path

import pytest

from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.validation import (
    CompanyConfigMismatchError,
    validate_quote_amounts,
)
from procurement_pipeline.schemas.quote_input import SupplierQuote


def test_validate_quote_amounts_returns_normal_result_without_outliers() -> None:
    # 준비: 단가가 서로 크게 튀지 않는 샘플 견적과 회사 config를 불러옵니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    company_config = load_company_config(Path("configs/companies/company_demo.json"))

    # 실행: 현재 RFQ 안의 공급사 단가를 비교합니다.
    result = validate_quote_amounts(quote_input, company_config)

    # 검증: 결과는 입력과 config의 핵심 식별자를 그대로 담고, 이슈는 비어 있습니다.
    assert result.request_id == quote_input.request_id
    assert result.company_id == quote_input.company_id
    assert result.used_policy_name == company_config.validation_policy_name
    assert result.risk_level == "normal"
    assert result.issues == ()


def test_validate_quote_amounts_warns_when_unit_price_is_robust_outlier() -> None:
    # 준비: 같은 RFQ 안에서 한 공급사의 단가만 크게 높은 견적을 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    outlier_quote = SupplierQuote(
        supplier_id="SUP-DELTA",
        supplier_name="Delta Industrial",
        unit_price=5_000,
        delivery_date=date(2026, 7, 18),
        shipping_fee=20_000,
        other_costs=5_000,
        memo="Outlier quote for validation test.",
    )
    quote_with_outlier = quote_input.model_copy(
        update={"quotes": (*quote_input.quotes, outlier_quote)}
    )

    # 실행: robust z-score 기준으로 단가 이상치를 검사합니다.
    result = validate_quote_amounts(quote_with_outlier, company_config)

    # 검증: 이상치 공급사에 대한 이슈와 warning 위험 수준이 기록됩니다.
    assert result.risk_level == "warning"
    assert len(result.issues) == 1

    issue = result.issues[0]
    assert issue.issue_code == "UNIT_PRICE_ROBUST_OUTLIER"
    assert issue.severity == "warning"
    assert issue.related_supplier_id == "SUP-DELTA"
    assert issue.related_field == "unit_price"
    assert issue.observed_value == 5_000
    assert issue.reference_value == 280.0
    assert issue.score >= company_config.amount_policy.robust_z_score_threshold


def test_validate_quote_amounts_stays_normal_when_quote_count_is_too_small() -> None:
    # 준비: robust z-score 비교에 필요한 최소 견적 수보다 적은 입력을 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    small_quote_input = quote_input.model_copy(update={"quotes": quote_input.quotes[:2]})

    # 실행: 견적 수가 부족한 RFQ의 단가를 검사합니다.
    result = validate_quote_amounts(small_quote_input, company_config)

    # 검증: 비교 근거가 부족하므로 이상치 이슈를 만들지 않습니다.
    assert result.risk_level == "normal"
    assert result.issues == ()


def test_validate_quote_amounts_uses_ratio_fallback_when_mad_is_zero() -> None:
    # 준비: 대부분 단가가 같아서 MAD가 0이 되는 RFQ를 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    same_price_quotes = (
        quote_input.quotes[0].model_copy(
            update={"supplier_id": "SUP-SAME-1", "unit_price": 273}
        ),
        quote_input.quotes[1].model_copy(
            update={"supplier_id": "SUP-SAME-2", "unit_price": 273}
        ),
        quote_input.quotes[2].model_copy(
            update={"supplier_id": "SUP-SAME-3", "unit_price": 273}
        ),
        quote_input.quotes[2].model_copy(
            update={"supplier_id": "SUP-HIGH", "unit_price": 330}
        ),
    )
    quote_with_zero_mad = quote_input.model_copy(update={"quotes": same_price_quotes})

    # 실행: MAD가 0일 때 단순 비율 기준 fallback을 사용합니다.
    result = validate_quote_amounts(quote_with_zero_mad, company_config)

    # 검증: fallback도 현재 RFQ 안에서 크게 튄 단가만 warning으로 기록합니다.
    assert result.risk_level == "warning"
    assert len(result.issues) == 1
    assert result.issues[0].related_supplier_id == "SUP-HIGH"
    assert result.issues[0].score == pytest.approx(57 / 273)


def test_validate_quote_amounts_rejects_company_id_mismatch() -> None:
    # 준비: 견적의 company_id와 다른 company_id를 가진 config를 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    mismatched_config = company_config.model_copy(update={"company_id": "OTHER-COMPANY"})

    # 실행 / 검증: 서로 다른 회사를 가리키면 명확한 오류가 발생합니다.
    with pytest.raises(CompanyConfigMismatchError) as exc_info:
        validate_quote_amounts(quote_input, mismatched_config)

    assert exc_info.value.quote_company_id == "COMPANY-DEMO"
    assert exc_info.value.config_company_id == "OTHER-COMPANY"
