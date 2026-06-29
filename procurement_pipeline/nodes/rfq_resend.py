from procurement_pipeline.schemas.rfq_difference_result import (
    RfqDifferenceResult,
    RfqResendResult,
)


def build_rfq_resend_result(
    rfq_difference_result: RfqDifferenceResult,
) -> RfqResendResult:
    return RfqResendResult(
        request_id=rfq_difference_result.request_id,
        company_id=rfq_difference_result.company_id,
        status="rfq_resend_requested",
        resend_reason="RFQ response exceeded company tolerance and requires resend mock.",
        exceeded_supplier_ids=tuple(
            supplier_result.supplier_id
            for supplier_result in rfq_difference_result.supplier_results
            if supplier_result.issue_codes
        ),
        issue_codes=rfq_difference_result.issue_codes,
    )
