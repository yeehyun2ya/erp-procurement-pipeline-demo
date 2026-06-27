from dataclasses import dataclass
from statistics import median
from typing import Final

from procurement_pipeline.nodes.risk_scoring import score_issues_risk
from procurement_pipeline.schemas.company_config import CompanyConfig
from procurement_pipeline.schemas.historical_price import (
    HistoricalPurchaseRecord,
    HistoricalUnitPriceInput,
)
from procurement_pipeline.schemas.quote_input import QuoteComparisonInput, SupplierQuote
from procurement_pipeline.schemas.validation_result import ValidationIssue, ValidationResult


HISTORICAL_BASELINE_ISSUE_CODE: Final = "UNIT_PRICE_HISTORICAL_BASELINE_OUTLIER"
MIN_HISTORICAL_RECORD_COUNT: Final = 3
ROBUST_Z_SCORE_SCALE: Final = 0.6745


@dataclass(frozen=True, slots=True)
class HistoricalBaselineMismatchError(RuntimeError):
    quote_company_id: str
    historical_company_id: str
    config_company_id: str

    def __str__(self) -> str:
        return (
            "Quote input, historical baseline, and company config company_id "
            "must match: "
            f"{self.quote_company_id}, {self.historical_company_id}, "
            f"{self.config_company_id}"
        )


@dataclass(frozen=True, slots=True)
class HistoricalBaselineItemMismatchError(RuntimeError):
    quote_item_name: str
    historical_item_name: str
    quote_item_category: str
    historical_item_category: str

    def __str__(self) -> str:
        return (
            "Quote input item does not match historical baseline item: "
            f"{self.quote_item_name}/{self.quote_item_category} != "
            f"{self.historical_item_name}/{self.historical_item_category}"
        )


def validate_quote_against_historical_baseline(
    quote_input: QuoteComparisonInput,
    historical_prices: HistoricalUnitPriceInput,
    company_config: CompanyConfig,
) -> ValidationResult:
    _ensure_company_ids_match(quote_input, historical_prices, company_config)
    _ensure_items_match(quote_input, historical_prices)

    issues = _find_historical_baseline_issues(
        quote_input,
        historical_prices,
        company_config,
    )
    return ValidationResult(
        request_id=quote_input.request_id,
        company_id=quote_input.company_id,
        used_policy_name=company_config.validation_policy_name,
        risk_level=score_issues_risk(issues),
        issues=issues,
    )


def _ensure_company_ids_match(
    quote_input: QuoteComparisonInput,
    historical_prices: HistoricalUnitPriceInput,
    company_config: CompanyConfig,
) -> None:
    if (
        quote_input.company_id
        == historical_prices.company_id
        == company_config.company_id
    ):
        return

    raise HistoricalBaselineMismatchError(
        quote_company_id=quote_input.company_id,
        historical_company_id=historical_prices.company_id,
        config_company_id=company_config.company_id,
    )


def _ensure_items_match(
    quote_input: QuoteComparisonInput,
    historical_prices: HistoricalUnitPriceInput,
) -> None:
    if (
        quote_input.item.name == historical_prices.item.name
        and quote_input.item.category == historical_prices.item.category
    ):
        return

    raise HistoricalBaselineItemMismatchError(
        quote_item_name=quote_input.item.name,
        historical_item_name=historical_prices.item.name,
        quote_item_category=quote_input.item.category,
        historical_item_category=historical_prices.item.category,
    )


def _find_historical_baseline_issues(
    quote_input: QuoteComparisonInput,
    historical_prices: HistoricalUnitPriceInput,
    company_config: CompanyConfig,
) -> tuple[ValidationIssue, ...]:
    records = _filter_records_by_quantity(
        historical_prices,
        quote_input.quantity,
        company_config,
    )
    if len(records) < MIN_HISTORICAL_RECORD_COUNT:
        return ()

    reference_value = float(median(record.unit_price for record in records))
    deviations = tuple(abs(record.unit_price - reference_value) for record in records)
    median_absolute_deviation = float(median(deviations))

    if median_absolute_deviation == 0:
        return _find_ratio_fallback_issues(
            quote_input.quotes,
            reference_value,
            company_config.amount_policy.unit_price_difference_warning_ratio,
        )

    threshold = (
        company_config.amount_policy.historical_unit_price_robust_z_score_threshold
    )
    return tuple(
        _build_issue(quote, reference_value, robust_z_score)
        for quote in quote_input.quotes
        if (robust_z_score := _calculate_robust_z_score(
            quote.unit_price,
            reference_value,
            median_absolute_deviation,
        ))
        >= threshold
    )


def _filter_records_by_quantity(
    historical_prices: HistoricalUnitPriceInput,
    quote_quantity: int,
    company_config: CompanyConfig,
) -> tuple[HistoricalPurchaseRecord, ...]:
    lower_bound = (
        quote_quantity
        * company_config.amount_policy.historical_quantity_lower_multiplier
    )
    upper_bound = (
        quote_quantity
        * company_config.amount_policy.historical_quantity_upper_multiplier
    )
    return tuple(
        record
        for record in historical_prices.purchase_records
        if lower_bound <= record.quantity <= upper_bound
    )


def _calculate_robust_z_score(
    unit_price: int,
    reference_value: float,
    median_absolute_deviation: float,
) -> float:
    return (
        ROBUST_Z_SCORE_SCALE
        * abs(unit_price - reference_value)
        / median_absolute_deviation
    )


def _find_ratio_fallback_issues(
    quotes: tuple[SupplierQuote, ...],
    reference_value: float,
    warning_ratio: float,
) -> tuple[ValidationIssue, ...]:
    if reference_value == 0:
        return ()

    return tuple(
        issue
        for quote in quotes
        if (
            issue := _build_ratio_fallback_issue(
                quote,
                reference_value,
                warning_ratio,
            )
        )
        is not None
    )


def _build_ratio_fallback_issue(
    quote: SupplierQuote,
    reference_value: float,
    warning_ratio: float,
) -> ValidationIssue | None:
    difference_ratio = abs(quote.unit_price - reference_value) / reference_value
    if difference_ratio < warning_ratio:
        return None

    return _build_issue(quote, reference_value, difference_ratio)


def _build_issue(
    quote: SupplierQuote,
    reference_value: float,
    score: float,
) -> ValidationIssue:
    return ValidationIssue(
        issue_code=HISTORICAL_BASELINE_ISSUE_CODE,
        severity="warning",
        message="Supplier unit price is higher than the historical baseline.",
        related_supplier_id=quote.supplier_id,
        related_field="unit_price",
        observed_value=float(quote.unit_price),
        reference_value=reference_value,
        score=score,
    )
