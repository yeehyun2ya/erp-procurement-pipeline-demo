from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from procurement_pipeline.schemas.company_config import RfqDifferenceRouteAction


RfqDifferenceStatus = Literal["within_tolerance", "tolerance_exceeded"]
RfqResendStatus = Literal["rfq_resend_requested"]


class SupplierRfqDifferenceResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    supplier_id: str
    supplier_name: str
    unit_price: int
    expected_unit_price: int
    price_difference_ratio: float
    delivery_date: date
    expected_delivery_date: date
    delivery_delay_days: int
    issue_codes: tuple[str, ...]


class RfqDifferenceResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    selected_route: RfqDifferenceRouteAction
    status: RfqDifferenceStatus
    route_reason: str
    issue_codes: tuple[str, ...]
    supplier_results: tuple[SupplierRfqDifferenceResult, ...]


class RfqResendResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    status: RfqResendStatus
    resend_reason: str
    exceeded_supplier_ids: tuple[str, ...]
    issue_codes: tuple[str, ...]
