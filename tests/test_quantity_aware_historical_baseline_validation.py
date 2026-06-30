from pathlib import Path

import pytest

from procurement_pipeline.load_company_config import (
    CompanyConfigLoadError,
    load_company_config,
)
from procurement_pipeline.load_historical_price import (
    HistoricalUnitPriceLoadError,
    load_historical_unit_prices,
)
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.baseline_validation import (
    validate_quote_against_historical_baseline,
)


HISTORICAL_PRICE_SAMPLE_PATH = Path(
    "data/sample_inputs/historical_unit_prices.json"
)
QUOTE_SAMPLE_PATH = Path("data/sample_inputs/quote_comparison.json")
COMPANY_CONFIG_SAMPLE_PATH = Path("configs/companies/company_demo.json")


def test_historical_purchase_record_rejects_non_positive_quantity(
    tmp_path: Path,
) -> None:
    # 준비: quantity가 0인 잘못된 과거 구매 단가 JSON을 만듭니다.
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
              "unit_price": 820,
              "quantity": 0,
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


def test_baseline_validation_uses_only_quantity_similar_history() -> None:
    # 준비: 현재 수량 500과 비슷한 기록 3개, 멀리 떨어진 극단값 2개를 함께 둡니다.
    quote_input = load_quote_comparison(QUOTE_SAMPLE_PATH)
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(COMPANY_CONFIG_SAMPLE_PATH)
    mixed_quantity_history = historical_prices.model_copy(
        update={
            "purchase_records": (
                historical_prices.purchase_records[0].model_copy(
                    update={"unit_price": 100, "quantity": 100}
                ),
                historical_prices.purchase_records[1].model_copy(
                    update={"unit_price": 268, "quantity": 400}
                ),
                historical_prices.purchase_records[2].model_copy(
                    update={"unit_price": 273, "quantity": 500}
                ),
                historical_prices.purchase_records[3].model_copy(
                    update={"unit_price": 278, "quantity": 600}
                ),
                historical_prices.purchase_records[4].model_copy(
                    update={"unit_price": 5_000, "quantity": 2_000}
                ),
            )
        }
    )
    quote_with_high_price = quote_input.model_copy(
        update={
            "quotes": (
                quote_input.quotes[0],
                quote_input.quotes[1],
                quote_input.quotes[2].model_copy(update={"unit_price": 500}),
            )
        }
    )

    # 실행: 수량이 비슷한 기록만 골라 과거 baseline을 계산합니다.
    result = validate_quote_against_historical_baseline(
        quote_with_high_price,
        mixed_quantity_history,
        company_config,
    )

    # 검증: quantity 400/500/600만 median에 들어가므로 극단값 100/5000은 영향을 주지 않습니다.
    assert result.risk_level == "warning"
    assert len(result.issues) == 1
    assert result.issues[0].reference_value == 273.0
    assert result.issues[0].related_supplier_id == "SUP-TAESUNG"


def test_baseline_validation_skips_issue_when_quantity_filtered_history_is_too_small() -> None:
    # 준비: 전체 기록은 3개 이상이지만 현재 수량과 비슷한 기록은 2개뿐입니다.
    quote_input = load_quote_comparison(QUOTE_SAMPLE_PATH)
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(COMPANY_CONFIG_SAMPLE_PATH)
    mostly_different_quantity_history = historical_prices.model_copy(
        update={
            "purchase_records": (
                historical_prices.purchase_records[0].model_copy(
                    update={"unit_price": 100, "quantity": 100}
                ),
                historical_prices.purchase_records[1].model_copy(
                    update={"unit_price": 268, "quantity": 400}
                ),
                historical_prices.purchase_records[2].model_copy(
                    update={"unit_price": 273, "quantity": 500}
                ),
                historical_prices.purchase_records[3].model_copy(
                    update={"unit_price": 5_000, "quantity": 2_000}
                ),
            )
        }
    )
    quote_with_high_price = quote_input.model_copy(
        update={
            "quotes": (
                quote_input.quotes[0].model_copy(update={"unit_price": 500}),
            )
        }
    )

    # 실행: quantity filtering 후 남은 기록만 baseline 후보로 봅니다.
    result = validate_quote_against_historical_baseline(
        quote_with_high_price,
        mostly_different_quantity_history,
        company_config,
    )

    # 검증: 유사 수량 기록이 3개 미만이면 근거 부족으로 issue를 만들지 않습니다.
    assert result.risk_level == "normal"
    assert result.issues == ()


def test_baseline_validation_uses_ratio_fallback_after_quantity_filtering() -> None:
    # 준비: 유사 수량 기록 3개만 같은 단가라서 filtering 후 MAD가 0이 됩니다.
    quote_input = load_quote_comparison(QUOTE_SAMPLE_PATH)
    historical_prices = load_historical_unit_prices(HISTORICAL_PRICE_SAMPLE_PATH)
    company_config = load_company_config(COMPANY_CONFIG_SAMPLE_PATH)
    zero_mad_quantity_history = historical_prices.model_copy(
        update={
            "purchase_records": (
                historical_prices.purchase_records[0].model_copy(
                    update={"unit_price": 100, "quantity": 100}
                ),
                historical_prices.purchase_records[1].model_copy(
                    update={"unit_price": 273, "quantity": 400}
                ),
                historical_prices.purchase_records[2].model_copy(
                    update={"unit_price": 273, "quantity": 500}
                ),
                historical_prices.purchase_records[3].model_copy(
                    update={"unit_price": 273, "quantity": 600}
                ),
                historical_prices.purchase_records[4].model_copy(
                    update={"unit_price": 5_000, "quantity": 2_000}
                ),
            )
        }
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

    # 실행: quantity filtering 후 MAD 0 fallback을 적용합니다.
    result = validate_quote_against_historical_baseline(
        quote_with_high_price,
        zero_mad_quantity_history,
        company_config,
    )

    # 검증: 유사 수량 기록의 median 273 기준으로 ratio fallback issue가 생깁니다.
    assert result.risk_level == "warning"
    assert len(result.issues) == 1
    assert result.issues[0].reference_value == 273.0
    assert result.issues[0].score == pytest.approx(57 / 273)


def test_company_config_reads_historical_quantity_multipliers() -> None:
    # 준비: 회사별 정책 config sample JSON 파일을 지정합니다.
    sample_path = COMPANY_CONFIG_SAMPLE_PATH

    # 실행: loader를 통해 Pydantic schema로 변환합니다.
    company_config = load_company_config(sample_path)

    # 검증: quantity band 기준이 config의 typed field로 읽힙니다.
    assert company_config.amount_policy.historical_quantity_lower_multiplier == 0.5
    assert company_config.amount_policy.historical_quantity_upper_multiplier == 2.0


def test_company_config_rejects_inverted_historical_quantity_multipliers(
    tmp_path: Path,
) -> None:
    # 준비: lower multiplier가 upper multiplier보다 큰 잘못된 config를 만듭니다.
    invalid_path = tmp_path / "invalid_company_config.json"
    invalid_path.write_text(
        """
        {
          "company_id": "COMPANY-DEMO",
          "company_name": "Demo Manufacturing Co.",
          "base_currency": "KRW",
          "validation_policy_name": "demo_procurement_validation",
          "amount_policy": {
            "high_value_purchase_threshold": 1000000,
            "unit_price_difference_warning_ratio": 0.15,
            "robust_z_score_threshold": 3.5,
            "historical_unit_price_robust_z_score_threshold": 3.5,
            "historical_quantity_lower_multiplier": 2.0,
            "historical_quantity_upper_multiplier": 0.5
          },
          "delivery_policy": {
            "urgent_delivery_days": 7,
            "allowed_delay_days": 2
          },
          "supplier_policy": {
            "minimum_quote_count": 3,
            "requires_new_supplier_review": true
          },
          "approval_route_policy": {
            "route_hints": [
              "standard_review",
              "manager_review",
              "executive_review"
            ]
          },
          "tco_policy": {
            "unit_price_weight": 1.0,
            "shipping_fee_weight": 1.0,
            "other_costs_weight": 1.0
          }
        }
        """,
        encoding="utf-8",
    )

    # 실행 / 검증: 잘못된 quantity band는 schema mismatch로 보고합니다.
    with pytest.raises(CompanyConfigLoadError) as exc_info:
        load_company_config(invalid_path)

    assert exc_info.value.reason == "Company config JSON does not match the schema"
