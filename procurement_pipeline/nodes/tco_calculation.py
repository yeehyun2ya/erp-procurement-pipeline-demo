from dataclasses import dataclass

from procurement_pipeline.schemas.company_config import CompanyConfig, TcoPolicy
from procurement_pipeline.schemas.quote_input import QuoteComparisonInput, SupplierQuote
from procurement_pipeline.schemas.tco_result import (
    SupplierTcoResult,
    TcoCalculationResult,
)


@dataclass(frozen=True, slots=True)
class TcoCompanyConfigMismatchError(RuntimeError):
    quote_company_id: str
    config_company_id: str

    def __str__(self) -> str:
        return (
            "Quote input company_id does not match company config company_id: "
            f"{self.quote_company_id} != {self.config_company_id}"
        )


def calculate_supplier_tco(
    quote_input: QuoteComparisonInput,
    company_config: CompanyConfig,
) -> TcoCalculationResult:
    if quote_input.company_id != company_config.company_id:
        raise TcoCompanyConfigMismatchError(
            quote_company_id=quote_input.company_id,
            config_company_id=company_config.company_id,
        )

    return TcoCalculationResult(
        request_id=quote_input.request_id,
        company_id=quote_input.company_id,
        used_policy_name=company_config.validation_policy_name,
        supplier_results=tuple(
            _calculate_quote_tco(quote, quote_input.quantity, company_config.tco_policy)
            for quote in quote_input.quotes
        ),
    )


def _calculate_quote_tco(
    quote: SupplierQuote,
    quantity: int,
    tco_policy: TcoPolicy,
) -> SupplierTcoResult:
    base_item_cost = float(quote.unit_price * quantity)
    shipping_fee = float(quote.shipping_fee)
    other_costs = float(quote.other_costs)

    return SupplierTcoResult(
        supplier_id=quote.supplier_id,
        supplier_name=quote.supplier_name,
        base_item_cost=base_item_cost,
        shipping_fee=shipping_fee,
        other_costs=other_costs,
        tco_amount=(
            base_item_cost * tco_policy.unit_price_weight
            + shipping_fee * tco_policy.shipping_fee_weight
            + other_costs * tco_policy.other_costs_weight
        ),
    )
