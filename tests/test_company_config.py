from pathlib import Path

import pytest

from procurement_pipeline.load_company_config import (
    CompanyConfigLoadError,
    load_company_config,
)


SAMPLE_CONFIG_PATH = Path("configs/companies/company_demo.json")


def test_load_company_config_reads_sample_json() -> None:
    # Given: a sample company config JSON file.
    sample_path = SAMPLE_CONFIG_PATH

    # When: the file is loaded through the company config schema.
    company_config = load_company_config(sample_path)

    # Then: the main company fields are available as typed Python attributes.
    assert company_config.company_id == "COMPANY-DEMO"
    assert company_config.company_name == "Demo Manufacturing Co."
    assert company_config.base_currency == "KRW"
    assert company_config.validation_policy_name == "demo_procurement_validation"


def test_load_company_config_keeps_policy_thresholds() -> None:
    # Given: a sample company config JSON file with policy threshold values.
    sample_path = SAMPLE_CONFIG_PATH

    # When: the file is loaded through the company config schema.
    company_config = load_company_config(sample_path)

    # Then: each nested policy keeps the configured rule values.
    assert company_config.amount_policy.high_value_purchase_threshold == 1_000_000
    assert company_config.amount_policy.unit_price_difference_warning_ratio == 0.15
    assert company_config.amount_policy.robust_z_score_threshold == 3.5
    assert (
        company_config.amount_policy.historical_unit_price_robust_z_score_threshold
        == 3.5
    )
    assert company_config.amount_policy.historical_quantity_lower_multiplier == 0.5
    assert company_config.amount_policy.historical_quantity_upper_multiplier == 2.0
    assert company_config.delivery_policy.urgent_delivery_days == 7
    assert company_config.delivery_policy.allowed_delay_days == 2
    assert company_config.supplier_policy.minimum_quote_count == 3
    assert company_config.supplier_policy.requires_new_supplier_review is True
    assert company_config.approval_route_policy.route_hints == (
        "standard_review",
        "manager_review",
        "executive_review",
    )
    assert company_config.tco_policy.unit_price_weight == 1.0
    assert company_config.tco_policy.shipping_fee_weight == 1.0
    assert company_config.tco_policy.other_costs_weight == 1.0


def test_load_company_config_rejects_invalid_tco_policy(tmp_path: Path) -> None:
    # 준비: unit_price_weight가 0인 잘못된 TCO 정책 config를 만듭니다.
    invalid_path = tmp_path / "invalid_tco_policy.json"
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
            "historical_quantity_lower_multiplier": 0.5,
            "historical_quantity_upper_multiplier": 2.0
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
            "unit_price_weight": 0,
            "shipping_fee_weight": 1.0,
            "other_costs_weight": 1.0
          }
        }
        """,
        encoding="utf-8",
    )

    # 실행 / 검증: 잘못된 TCO 계수는 schema mismatch로 보고합니다.
    with pytest.raises(CompanyConfigLoadError) as exc_info:
        load_company_config(invalid_path)

    assert exc_info.value.reason == "Company config JSON does not match the schema"


def test_load_company_config_reports_schema_mismatch(tmp_path: Path) -> None:
    # Given: a JSON file that does not match the company config schema.
    invalid_path = tmp_path / "invalid_company_config.json"
    invalid_path.write_text("{}", encoding="utf-8")

    # When / Then: loading it reports a schema mismatch, not a file read error.
    with pytest.raises(CompanyConfigLoadError) as exc_info:
        load_company_config(invalid_path)

    assert exc_info.value.reason == "Company config JSON does not match the schema"
