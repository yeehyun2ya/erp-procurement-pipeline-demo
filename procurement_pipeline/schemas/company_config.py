from pydantic import BaseModel, ConfigDict, Field


class AmountPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    high_value_purchase_threshold: int = Field(gt=0)
    unit_price_difference_warning_ratio: float = Field(ge=0, le=1)


class DeliveryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    urgent_delivery_days: int = Field(gt=0)
    allowed_delay_days: int = Field(ge=0)


class SupplierPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    minimum_quote_count: int = Field(gt=0)
    requires_new_supplier_review: bool


class ApprovalRoutePolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    route_hints: tuple[str, ...] = Field(min_length=1)


class CompanyConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    company_id: str
    company_name: str
    base_currency: str
    validation_policy_name: str
    amount_policy: AmountPolicy
    delivery_policy: DeliveryPolicy
    supplier_policy: SupplierPolicy
    approval_route_policy: ApprovalRoutePolicy
