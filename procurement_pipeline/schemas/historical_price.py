from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class HistoricalPurchaseItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str


class HistoricalPurchaseRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    purchase_id: str
    supplier_id: str
    unit_price: int = Field(ge=0)
    quantity: int = Field(gt=0)
    purchased_at: date


class HistoricalUnitPriceInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str
    base_currency: str
    item: HistoricalPurchaseItem
    purchase_records: tuple[HistoricalPurchaseRecord, ...] = Field(min_length=1)
