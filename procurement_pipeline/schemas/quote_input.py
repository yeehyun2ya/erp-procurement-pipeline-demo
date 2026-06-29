from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PurchaseItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str
    description: str


class SupplierQuote(BaseModel):
    model_config = ConfigDict(frozen=True)

    supplier_id: str
    supplier_name: str
    unit_price: int = Field(ge=0)
    delivery_date: date
    shipping_fee: int = Field(ge=0)
    other_costs: int = Field(ge=0)
    memo: str


class RfqOriginalTerms(BaseModel):
    model_config = ConfigDict(frozen=True)

    expected_unit_price: int = Field(gt=0)
    expected_delivery_date: date


class QuoteComparisonInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    company_id: str
    base_currency: str
    item: PurchaseItem
    quantity: int = Field(gt=0)
    rfq_terms: RfqOriginalTerms
    quotes: tuple[SupplierQuote, ...] = Field(min_length=1)
