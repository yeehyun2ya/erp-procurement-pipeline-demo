from dataclasses import dataclass
from statistics import median
from typing import Final

from procurement_pipeline.nodes.risk_scoring import score_issues_risk
from procurement_pipeline.schemas.company_config import CompanyConfig
from procurement_pipeline.schemas.quote_input import QuoteComparisonInput, SupplierQuote
from procurement_pipeline.schemas.validation_result import ValidationIssue, ValidationResult


ROBUST_Z_SCORE_SCALE: Final = 0.6745
MIN_ROBUST_QUOTE_COUNT: Final = 3


@dataclass(frozen=True, slots=True)
class CompanyConfigMismatchError(RuntimeError):
    quote_company_id: str
    config_company_id: str

    def __str__(self) -> str:
        return (
            "Quote input company_id does not match company config company_id: "
            f"{self.quote_company_id} != {self.config_company_id}"
        )


def validate_quote_amounts(
    quote_input: QuoteComparisonInput,
    company_config: CompanyConfig,
) -> ValidationResult:
    if quote_input.company_id != company_config.company_id:
        raise CompanyConfigMismatchError(
            quote_company_id=quote_input.company_id,
            config_company_id=company_config.company_id,
        )

    unit_price_median = float(median(quote.unit_price for quote in quote_input.quotes))
    issues = _find_unit_price_issues(
        quotes=quote_input.quotes,
        reference_value=unit_price_median,
        company_config=company_config,
    )
    return ValidationResult(
        request_id=quote_input.request_id,
        company_id=quote_input.company_id,
        used_policy_name=company_config.validation_policy_name,
        risk_level=score_issues_risk(issues),
        issues=issues,
    )


def _find_unit_price_issues(
    quotes: tuple[SupplierQuote, ...],
    reference_value: float,
    company_config: CompanyConfig,
) -> tuple[ValidationIssue, ...]:
    if len(quotes) < MIN_ROBUST_QUOTE_COUNT:
        return ()

    deviations = tuple(abs(quote.unit_price - reference_value) for quote in quotes)
    median_absolute_deviation = float(median(deviations))

    if median_absolute_deviation == 0:
        return _find_ratio_fallback_issues(
            quotes=quotes,
            reference_value=reference_value,
            warning_ratio=company_config.amount_policy.unit_price_difference_warning_ratio,
        )

    threshold = company_config.amount_policy.robust_z_score_threshold
    return tuple(
        ValidationIssue(
            issue_code="UNIT_PRICE_ROBUST_OUTLIER",
            severity="warning",
            message="Supplier unit price is a robust z-score outlier within this RFQ.",
            related_supplier_id=quote.supplier_id,
            related_field="unit_price",
            observed_value=float(quote.unit_price),
            reference_value=reference_value,
            score=robust_z_score,
        )
        for quote in quotes
        if (robust_z_score := _calculate_robust_z_score(
            unit_price=quote.unit_price,
            reference_value=reference_value,
            median_absolute_deviation=median_absolute_deviation,
        )
        )
        >= threshold
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
                quote=quote,
                reference_value=reference_value,
                warning_ratio=warning_ratio,
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

    return ValidationIssue(
        issue_code="UNIT_PRICE_ROBUST_OUTLIER",
        severity="warning",
        message="Supplier unit price differs from the RFQ median while MAD is zero.",
        related_supplier_id=quote.supplier_id,
        related_field="unit_price",
        observed_value=float(quote.unit_price),
        reference_value=reference_value,
        score=difference_ratio,
    )
