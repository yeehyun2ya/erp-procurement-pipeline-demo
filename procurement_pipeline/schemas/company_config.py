from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError


class AmountPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    high_value_purchase_threshold: int = Field(gt=0)
    unit_price_difference_warning_ratio: float = Field(ge=0, le=1)
    robust_z_score_threshold: float = Field(gt=0)
    historical_unit_price_robust_z_score_threshold: float = Field(gt=0)
    historical_quantity_lower_multiplier: float = Field(gt=0)
    historical_quantity_upper_multiplier: float = Field(gt=0)

    @model_validator(mode="after")
    def ensure_quantity_multiplier_order(self) -> Self:
        if (
            self.historical_quantity_lower_multiplier
            <= self.historical_quantity_upper_multiplier
        ):
            return self

        raise PydanticCustomError(
            "historical_quantity_multiplier_order",
            "historical_quantity_lower_multiplier must be less than or equal "
            "to historical_quantity_upper_multiplier",
        )


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


class TcoPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    unit_price_weight: float = Field(gt=0)
    shipping_fee_weight: float = Field(ge=0)
    other_costs_weight: float = Field(ge=0)


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
    tco_policy: TcoPolicy
