from dataclasses import dataclass
from typing import Final

from procurement_pipeline.schemas.company_config import CompanyConfig, RfqDifferencePolicy
from procurement_pipeline.schemas.quote_input import (
    QuoteComparisonInput,
    RfqOriginalTerms,
    SupplierQuote,
)
from procurement_pipeline.schemas.rfq_difference_result import (
    RfqDifferenceResult,
    SupplierRfqDifferenceResult,
)
from procurement_pipeline.schemas.validation_result import RiskLevel
from procurement_pipeline.schemas.validation_routing_result import (
    HumanReviewRequestResult,
)


RFQ_PRICE_TOLERANCE_EXCEEDED: Final = "RFQ_PRICE_TOLERANCE_EXCEEDED"
RFQ_DELIVERY_TOLERANCE_EXCEEDED: Final = "RFQ_DELIVERY_TOLERANCE_EXCEEDED"


@dataclass(frozen=True, slots=True)
class RfqDifferenceCompanyConfigMismatchError(RuntimeError):
    quote_company_id: str
    config_company_id: str

    def __str__(self) -> str:
        return (
            "Quote input company_id does not match company config company_id: "
            f"{self.quote_company_id} != {self.config_company_id}"
        )


def build_rfq_difference_result(
    quote_input: QuoteComparisonInput,
    company_config: CompanyConfig,
) -> RfqDifferenceResult:
    _ensure_company_ids_match(quote_input, company_config)

    supplier_results = tuple(
        _build_supplier_result(
            quote,
            quote_input.rfq_terms,
            company_config.approval_route_policy.rfq_difference_policy,
        )
        for quote in quote_input.quotes
    )
    issue_codes = _collect_issue_codes(supplier_results)
    is_within_tolerance = not issue_codes
    policy = company_config.approval_route_policy.rfq_difference_policy

    return RfqDifferenceResult(
        request_id=quote_input.request_id,
        company_id=quote_input.company_id,
        selected_route=(
            policy.within_tolerance_route
            if is_within_tolerance
            else policy.exceeds_tolerance_route
        ),
        status="within_tolerance" if is_within_tolerance else "tolerance_exceeded",
        route_reason=_route_reason(is_within_tolerance),
        issue_codes=issue_codes,
        supplier_results=supplier_results,
    )


def build_rfq_human_review_request_result(
    rfq_difference_result: RfqDifferenceResult,
    risk_level: RiskLevel,
) -> HumanReviewRequestResult:
    return HumanReviewRequestResult(
        request_id=rfq_difference_result.request_id,
        company_id=rfq_difference_result.company_id,
        risk_level=risk_level,
        status="awaiting_human_review",
        review_trigger="rfq_difference",
        review_reason="RFQ response exceeded company tolerance and requires HITL mock review.",
        issue_codes=rfq_difference_result.issue_codes,
    )


def _ensure_company_ids_match(
    quote_input: QuoteComparisonInput,
    company_config: CompanyConfig,
) -> None:
    if quote_input.company_id == company_config.company_id:
        return

    raise RfqDifferenceCompanyConfigMismatchError(
        quote_company_id=quote_input.company_id,
        config_company_id=company_config.company_id,
    )


def _build_supplier_result(
    quote: SupplierQuote,
    rfq_terms: RfqOriginalTerms,
    policy: RfqDifferencePolicy,
) -> SupplierRfqDifferenceResult:
    price_difference_ratio = (
        quote.unit_price - rfq_terms.expected_unit_price
    ) / rfq_terms.expected_unit_price
    delivery_delay_days = (
        quote.delivery_date - rfq_terms.expected_delivery_date
    ).days
    issue_codes = _supplier_issue_codes(
        price_difference_ratio,
        delivery_delay_days,
        policy,
    )

    return SupplierRfqDifferenceResult(
        supplier_id=quote.supplier_id,
        supplier_name=quote.supplier_name,
        unit_price=quote.unit_price,
        expected_unit_price=rfq_terms.expected_unit_price,
        price_difference_ratio=price_difference_ratio,
        delivery_date=quote.delivery_date,
        expected_delivery_date=rfq_terms.expected_delivery_date,
        delivery_delay_days=delivery_delay_days,
        issue_codes=issue_codes,
    )


def _supplier_issue_codes(
    price_difference_ratio: float,
    delivery_delay_days: int,
    policy: RfqDifferencePolicy,
) -> tuple[str, ...]:
    issue_codes: list[str] = []
    if price_difference_ratio > policy.price_tolerance_ratio:
        issue_codes.append(RFQ_PRICE_TOLERANCE_EXCEEDED)
    if delivery_delay_days > policy.delivery_tolerance_days:
        issue_codes.append(RFQ_DELIVERY_TOLERANCE_EXCEEDED)
    return tuple(issue_codes)


def _collect_issue_codes(
    supplier_results: tuple[SupplierRfqDifferenceResult, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            issue_code
            for supplier_result in supplier_results
            for issue_code in supplier_result.issue_codes
        ),
    )


def _route_reason(is_within_tolerance: bool) -> str:
    if is_within_tolerance:
        return "Every supplier response is within the configured RFQ tolerance."
    return "At least one supplier response exceeds the configured RFQ tolerance."
