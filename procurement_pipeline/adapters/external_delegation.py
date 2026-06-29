from typing import Protocol, assert_never

from procurement_pipeline.schemas.external_delegation import (
    ExternalDelegationRequest,
    ExternalDelegationResult,
)
from procurement_pipeline.schemas.rfq_difference_result import RfqResendResult
from procurement_pipeline.schemas.validation_routing_result import (
    HumanReviewRequestResult,
)


class ExternalDelegationAdapter(Protocol):
    def delegate(
        self,
        request: ExternalDelegationRequest,
    ) -> ExternalDelegationResult: ...


class MockExternalDelegationAdapter:
    def delegate(
        self,
        request: ExternalDelegationRequest,
    ) -> ExternalDelegationResult:
        match request.delegation_type:
            case "erp_approval_request":
                target_system = "erp_approval"
                mock_response_id = f"MOCK-ERP-{request.request_id}"
            case "manager_notification":
                target_system = "procurement_notification"
                mock_response_id = f"MOCK-NOTIFY-{request.request_id}"
            case unreachable:
                assert_never(unreachable)

        return ExternalDelegationResult(
            request_id=request.request_id,
            company_id=request.company_id,
            delegation_type=request.delegation_type,
            target_system=target_system,
            status="mock_accepted",
            mock_response_id=mock_response_id,
            issue_codes=request.issue_codes,
        )


def build_erp_approval_request(
    rfq_resend_result: RfqResendResult,
) -> ExternalDelegationRequest:
    return ExternalDelegationRequest(
        request_id=rfq_resend_result.request_id,
        company_id=rfq_resend_result.company_id,
        delegation_type="erp_approval_request",
        issue_codes=rfq_resend_result.issue_codes,
    )


def build_manager_notification_request(
    human_review_result: HumanReviewRequestResult,
) -> ExternalDelegationRequest:
    return ExternalDelegationRequest(
        request_id=human_review_result.request_id,
        company_id=human_review_result.company_id,
        delegation_type="manager_notification",
        issue_codes=human_review_result.issue_codes,
    )
