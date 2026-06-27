from pydantic import BaseModel, ConfigDict


class SupplierTcoResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    supplier_id: str
    supplier_name: str
    base_item_cost: float
    shipping_fee: float
    other_costs: float
    tco_amount: float


class TcoCalculationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    used_policy_name: str
    supplier_results: tuple[SupplierTcoResult, ...]
