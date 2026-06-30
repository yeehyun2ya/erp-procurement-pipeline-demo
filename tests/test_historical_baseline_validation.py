from pathlib import Path

import pytest

from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_historical_price import (
    HistoricalUnitPriceLoadError,
    load_historical_unit_prices,
)
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.baseline_validation import (
    HistoricalBaselineItemMismatchError,
    HistoricalBaselineMismatchError,
    validate_quote_against_historical_baseline,
)


HISTORICAL_PRICE_SAMPLE_PATH = Path(
    "data/sample_inputs/historical_unit_prices.json"
)


def test_load_historical_unit_prices_reads_sample_json() -> None:
    # 준비: 과거 구매 단가 sample JSON 파일을 지정합니다.
    sample_path = HISTORICAL_PRICE_SAMPLE_PATH

    # 실행: loader를 통해 Pydantic schema로 변환합니다.
    historical_prices = load_historical_unit_prices(sample_path)

    # 검증: 핵심 필드와 구매 기록이 typed object로 읽힙니다.
    assert historical_prices.company_id == "COMPANY-DEMO"
    assert historical_prices.base_currency == "KRW"
    assert historical_prices.item.name == "BOLT M12-40"
    assert len(historical_prices.purchase_records) == 10
    assert historical_prices.purchase_records[0].purchase_id == "PO-2025-0001"
    assert historical_prices.purchase_records[0].unit_price == 282
    assert historical_prices.purchase_records[0].quantity == 260


def test_baseline_validation_returns_normal_when_quotes_match_history() -> None:
    # 준비: 현재 견적 단가가 과거 구매 단가 범위와 크게 다르지 않은 입력을 불러옵니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(Path("configs/companies/company_demo.json"))

    # 실행: 현재 견적 단가를 과거 구매 단가 baseline과 비교합니다.
    result = validate_quote_against_historical_baseline(
        quote_input,
        historical_prices,
        company_config,
    )

    # 검증: baseline 대비 이상치가 없으므로 normal 결과가 나옵니다.
    assert result.request_id == quote_input.request_id
    assert result.company_id == quote_input.company_id
    assert result.used_policy_name == company_config.validation_policy_name
    assert result.risk_level == "normal"
    assert result.issues == ()


def test_baseline_validation_warns_when_quote_exceeds_history() -> None:
    # 준비: 한 공급사의 현재 견적 단가만 과거 구매 단가보다 크게 높입니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    quote_with_outlier = quote_input.model_copy(
        update={
            "quotes": (
                quote_input.quotes[0],
                quote_input.quotes[1],
                quote_input.quotes[2].model_copy(update={"unit_price": 500}),
            )
        }
    )

    # 실행: 과거 baseline 기준으로 현재 견적 단가를 검사합니다.
    result = validate_quote_against_historical_baseline(
        quote_with_outlier,
        historical_prices,
        company_config,
    )

    # 검증: #4 RFQ 내부 issue와 다른 issue_code로 baseline 이상치를 기록합니다.
    assert result.risk_level == "warning"
    assert len(result.issues) == 1

    issue = result.issues[0]
    assert issue.issue_code == "UNIT_PRICE_HISTORICAL_BASELINE_OUTLIER"
    assert issue.issue_code != "UNIT_PRICE_ROBUST_OUTLIER"
    assert issue.severity == "warning"
    assert issue.related_supplier_id == "SUP-TAESUNG"
    assert issue.related_field == "unit_price"
    assert issue.observed_value == 500
    assert issue.reference_value == 270.0
    assert (
        issue.score
        >= company_config.amount_policy.historical_unit_price_robust_z_score_threshold
    )


def test_baseline_validation_skips_issue_when_history_is_too_small() -> None:
    # 준비: 과거 구매 기록이 3개보다 적은 baseline을 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    small_history = historical_prices.model_copy(
        update={"purchase_records": historical_prices.purchase_records[:2]}
    )
    quote_with_high_price = quote_input.model_copy(
        update={
            "quotes": (
                quote_input.quotes[0].model_copy(update={"unit_price": 500}),
            )
        }
    )

    # 실행: 판단 근거가 부족한 과거 baseline으로 검사합니다.
    result = validate_quote_against_historical_baseline(
        quote_with_high_price,
        small_history,
        company_config,
    )

    # 검증: 기록 수가 부족하면 이상치 issue를 만들지 않습니다.
    assert result.risk_level == "normal"
    assert result.issues == ()


def test_baseline_validation_uses_ratio_fallback_when_mad_is_zero() -> None:
    # 준비: 과거 구매 단가가 모두 같아서 MAD가 0인 baseline을 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    same_price_records = tuple(
        record.model_copy(update={"unit_price": 273})
        for record in historical_prices.purchase_records[:8]
    )
    zero_mad_history = historical_prices.model_copy(
        update={"purchase_records": same_price_records}
    )
    quote_with_high_price = quote_input.model_copy(
        update={
            "quotes": (
                quote_input.quotes[0],
                quote_input.quotes[1],
                quote_input.quotes[2].model_copy(update={"unit_price": 330}),
            )
        }
    )

    # 실행: MAD가 0일 때 median 대비 차이 비율로 fallback 검사합니다.
    result = validate_quote_against_historical_baseline(
        quote_with_high_price,
        zero_mad_history,
        company_config,
    )

    # 검증: fallback 기준도 과거 baseline보다 크게 높은 공급사만 warning으로 기록합니다.
    assert result.risk_level == "warning"
    assert len(result.issues) == 1
    assert result.issues[0].related_supplier_id == "SUP-TAESUNG"
    assert result.issues[0].reference_value == 273.0
    assert result.issues[0].score == pytest.approx(57 / 273)


def test_baseline_validation_rejects_company_id_mismatch() -> None:
    # 준비: quote, history, config가 서로 다른 company_id를 가리키게 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    mismatched_history = historical_prices.model_copy(
        update={"company_id": "OTHER-COMPANY"}
    )

    # 실행 / 검증: 회사가 다르면 baseline을 비교하지 않고 명확한 오류를 냅니다.
    with pytest.raises(HistoricalBaselineMismatchError) as exc_info:
        validate_quote_against_historical_baseline(
            quote_input,
            mismatched_history,
            company_config,
        )

    assert exc_info.value.quote_company_id == "COMPANY-DEMO"
    assert exc_info.value.historical_company_id == "OTHER-COMPANY"
    assert exc_info.value.config_company_id == "COMPANY-DEMO"


def test_baseline_validation_rejects_item_mismatch() -> None:
    # 준비: 과거 baseline의 품목이 현재 견적 품목과 다르게 보이도록 만듭니다.
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    mismatched_history = historical_prices.model_copy(
        update={
            "item": historical_prices.item.model_copy(
                update={"name": "Steel nut M12"}
            )
        }
    )

    # 실행 / 검증: 다른 품목이면 잘못된 baseline을 쓰지 않도록 오류를 냅니다.
    with pytest.raises(HistoricalBaselineItemMismatchError) as exc_info:
        validate_quote_against_historical_baseline(
            quote_input,
            mismatched_history,
            company_config,
        )

    assert exc_info.value.quote_item_name == "BOLT M12-40"
    assert exc_info.value.historical_item_name == "Steel nut M12"
    assert exc_info.value.quote_item_category == "볼트류"
    assert exc_info.value.historical_item_category == "볼트류"


def test_historical_purchase_record_rejects_negative_unit_price(tmp_path: Path) -> None:
    # 준비: 음수 단가가 들어간 잘못된 과거 구매 단가 JSON을 만듭니다.
    invalid_path = tmp_path / "invalid_historical_prices.json"
    invalid_path.write_text(
        """
        {
          "company_id": "COMPANY-DEMO",
          "base_currency": "KRW",
          "item": {
            "name": "BOLT M12-40",
            "category": "볼트류"
          },
          "purchase_records": [
            {
              "purchase_id": "PO-2025-0001",
              "supplier_id": "SUP-GAON",
              "unit_price": -1,
              "quantity": 20,
              "purchased_at": "2025-09-10"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    # 실행 / 검증: loader가 schema mismatch로 보고합니다.
    with pytest.raises(HistoricalUnitPriceLoadError) as exc_info:
        load_historical_unit_prices(invalid_path)

    assert "Historical unit price JSON does not match the schema" in str(
        exc_info.value
    )
