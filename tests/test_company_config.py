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
    assert company_config.delivery_policy.urgent_delivery_days == 7
    assert company_config.delivery_policy.allowed_delay_days == 2
    assert company_config.supplier_policy.minimum_quote_count == 3
    assert company_config.supplier_policy.requires_new_supplier_review is True
    assert company_config.approval_route_policy.route_hints == (
        "standard_review",
        "manager_review",
        "executive_review",
    )


def test_load_company_config_reports_schema_mismatch(tmp_path: Path) -> None:
    # Given: a JSON file that does not match the company config schema.
    invalid_path = tmp_path / "invalid_company_config.json"
    invalid_path.write_text("{}", encoding="utf-8")

    # When / Then: loading it reports a schema mismatch, not a file read error.
    with pytest.raises(CompanyConfigLoadError) as exc_info:
        load_company_config(invalid_path)

    assert exc_info.value.reason == "Company config JSON does not match the schema"
