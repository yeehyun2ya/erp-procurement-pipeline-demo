from typing import Literal

from pydantic import BaseModel, ConfigDict


ExternalDelegationType = Literal[
    "erp_approval_request",
    "manager_notification",
]
ExternalDelegationTargetSystem = Literal[
    "erp_approval",
    "procurement_notification",
]
ExternalDelegationStatus = Literal["mock_accepted"]


class ExternalDelegationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    delegation_type: ExternalDelegationType
    issue_codes: tuple[str, ...]


class ExternalDelegationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    company_id: str
    delegation_type: ExternalDelegationType
    target_system: ExternalDelegationTargetSystem
    status: ExternalDelegationStatus
    mock_response_id: str
    issue_codes: tuple[str, ...]
