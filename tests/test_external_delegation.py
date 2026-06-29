from procurement_pipeline.adapters.external_delegation import (
    MockExternalDelegationAdapter,
)
from procurement_pipeline.schemas.external_delegation import ExternalDelegationRequest


def test_mock_adapter_returns_fixed_erp_approval_response() -> None:
    # 준비: ERP 승인 요청 mock 입력을 만듭니다.
    request = ExternalDelegationRequest(
        request_id="REQ-DELEGATION",
        company_id="COMPANY-B",
        delegation_type="erp_approval_request",
        issue_codes=("RFQ_PRICE_TOLERANCE_EXCEEDED",),
    )

    # 실행: 실제 ERP 대신 mock adapter에 승인 요청을 위임합니다.
    result = MockExternalDelegationAdapter().delegate(request)

    # 검증: 실제 전송 없이 고정된 JSON 응답 모양을 돌려줍니다.
    assert result.request_id == "REQ-DELEGATION"
    assert result.company_id == "COMPANY-B"
    assert result.delegation_type == "erp_approval_request"
    assert result.target_system == "erp_approval"
    assert result.status == "mock_accepted"
    assert result.mock_response_id == "MOCK-ERP-REQ-DELEGATION"
    assert result.issue_codes == ("RFQ_PRICE_TOLERANCE_EXCEEDED",)


def test_mock_adapter_returns_fixed_manager_notification_response() -> None:
    # 준비: 담당자 알림 위임 요청을 만듭니다.
    request = ExternalDelegationRequest(
        request_id="REQ-DELEGATION",
        company_id="COMPANY-C",
        delegation_type="manager_notification",
        issue_codes=("RFQ_DELIVERY_TOLERANCE_EXCEEDED",),
    )

    # 실행: 실제 알림 대신 mock adapter에 담당자 알림을 위임합니다.
    result = MockExternalDelegationAdapter().delegate(request)

    # 검증: 알림 대상 시스템과 mock 응답 id가 고정됩니다.
    assert result.target_system == "procurement_notification"
    assert result.mock_response_id == "MOCK-NOTIFY-REQ-DELEGATION"
