from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from procurement_pipeline.graph import graph
from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.validation import validate_quote_amounts
from procurement_pipeline.schemas.company_config import RfqDifferenceRouteAction
from procurement_pipeline.schemas.rfq_difference_result import RfqDifferenceStatus
from procurement_pipeline.schemas.validation_routing_result import (
    HumanReviewTrigger,
    ValidationRouteAction,
)
from procurement_pipeline.state import ProcurementState


SHARED_QUOTE_PATH = Path("data/sample_inputs/quote_comparison_shared.json")
DemoFinalOutcome = Literal[
    "tco_calculation",
    "rfq_resend",
    "human_review_request",
    "ocr_reparse",
]


@dataclass(frozen=True, slots=True)
class CompanyDemoCase:
    config_path: Path


@dataclass(frozen=True, slots=True)
class DemoOutcomeSelectionError(RuntimeError):
    path_trace: tuple[str, ...]

    def __str__(self) -> str:
        return f"Could not select final demo outcome from path: {self.path_trace}"


class CompanyDemoSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    company_id: str
    company_name: str
    request_id: str
    quote_source_path: str
    config_path: str
    source_quote_company_id: str
    executed_quote_company_id: str
    validation_route: ValidationRouteAction
    rfq_difference_route: RfqDifferenceRouteAction | None
    rfq_difference_status: RfqDifferenceStatus | None
    final_outcome: DemoFinalOutcome
    path_trace: tuple[str, ...]
    issue_codes: tuple[str, ...]
    human_review_trigger: HumanReviewTrigger | None


COMPANY_DEMO_CASES = (
    CompanyDemoCase(config_path=Path("configs/companies/company_a.json")),
    CompanyDemoCase(config_path=Path("configs/companies/company_b.json")),
    CompanyDemoCase(config_path=Path("configs/companies/company_c.json")),
)


def run_company_demo(quote_path: Path, config_path: Path) -> CompanyDemoSummary:
    source_quote_input = load_quote_comparison(quote_path)
    company_config = load_company_config(config_path)
    quote_input = source_quote_input.model_copy(
        update={"company_id": company_config.company_id},
    )
    validation_result = validate_quote_amounts(quote_input, company_config)
    initial_state: ProcurementState = {
        "quote_input": quote_input,
        "company_config": company_config,
        "validation_result": validation_result,
    }
    result: ProcurementState = graph.invoke(initial_state)
    human_review_trigger: HumanReviewTrigger | None = None
    rfq_difference_route: RfqDifferenceRouteAction | None = None
    rfq_difference_status: RfqDifferenceStatus | None = None
    issue_codes: tuple[str, ...] = ()
    if "rfq_difference_result" in result:
        rfq_difference_route = result["rfq_difference_result"].selected_route
        rfq_difference_status = result["rfq_difference_result"].status
        issue_codes = result["rfq_difference_result"].issue_codes
    if "human_review_result" in result:
        human_review_trigger = result["human_review_result"].review_trigger
        issue_codes = result["human_review_result"].issue_codes
    if "ocr_reparse_result" in result:
        issue_codes = result["ocr_reparse_result"].issue_codes

    return CompanyDemoSummary(
        company_id=result["company_config"].company_id,
        company_name=result["company_config"].company_name,
        request_id=result["quote_input"].request_id,
        quote_source_path=quote_path.as_posix(),
        config_path=config_path.as_posix(),
        source_quote_company_id=source_quote_input.company_id,
        executed_quote_company_id=result["quote_input"].company_id,
        validation_route=result["routing_result"].selected_route,
        rfq_difference_route=rfq_difference_route,
        rfq_difference_status=rfq_difference_status,
        final_outcome=_final_outcome(result),
        path_trace=result["path_trace"],
        issue_codes=issue_codes,
        human_review_trigger=human_review_trigger,
    )


def run_comparison_demo() -> tuple[CompanyDemoSummary, ...]:
    return tuple(
        run_company_demo(SHARED_QUOTE_PATH, demo_case.config_path)
        for demo_case in COMPANY_DEMO_CASES
    )


def main() -> None:
    for summary in run_comparison_demo():
        print(summary.model_dump_json())


def _final_outcome(state: ProcurementState) -> DemoFinalOutcome:
    if "tco_result" in state:
        return "tco_calculation"
    if "rfq_resend_result" in state:
        return "rfq_resend"
    if "human_review_result" in state:
        return "human_review_request"
    if "ocr_reparse_result" in state:
        return "ocr_reparse"

    raise DemoOutcomeSelectionError(path_trace=state.get("path_trace", ()))


if __name__ == "__main__":
    main()
