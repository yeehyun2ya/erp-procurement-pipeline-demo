from typing_extensions import NotRequired, TypedDict

from procurement_pipeline.schemas.company_config import CompanyConfig
from procurement_pipeline.schemas.quote_input import QuoteComparisonInput
from procurement_pipeline.schemas.tco_result import TcoCalculationResult
from procurement_pipeline.schemas.validation_result import ValidationResult
from procurement_pipeline.schemas.validation_routing_result import (
    HumanReviewRequestResult,
    OcrReparseResult,
    ValidationRoutingResult,
)


PathTrace = tuple[str, ...]


class ProcurementState(TypedDict):
    quote_input: QuoteComparisonInput
    company_config: CompanyConfig
    validation_result: ValidationResult
    routing_result: NotRequired[ValidationRoutingResult]
    tco_result: NotRequired[TcoCalculationResult]
    ocr_reparse_result: NotRequired[OcrReparseResult]
    human_review_result: NotRequired[HumanReviewRequestResult]
    path_trace: NotRequired[PathTrace]


class ProcurementStateUpdate(TypedDict, total=False):
    routing_result: ValidationRoutingResult
    tco_result: TcoCalculationResult
    ocr_reparse_result: OcrReparseResult
    human_review_result: HumanReviewRequestResult
    path_trace: PathTrace
