from pathlib import Path
from typing import Final

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from procurement_pipeline.demo_screen_flow import (
    DemoScreenFlowView,
    build_screen_flow_for_summary,
)
from procurement_pipeline.run_graph import (
    CompanyDemoSummary,
    DemoFinalOutcome,
    run_comparison_demo,
)
from procurement_pipeline.schemas.company_config import RfqDifferenceRouteAction
from procurement_pipeline.schemas.external_delegation import ExternalDelegationResult
from procurement_pipeline.schemas.rfq_difference_result import RfqDifferenceStatus
from procurement_pipeline.schemas.validation_result import RiskLevel
from procurement_pipeline.schemas.validation_routing_result import (
    HumanReviewTrigger,
    ValidationRouteAction,
)


APP_TITLE: Final = "ERP Procurement Pipeline Demo"
STATIC_DIR: Final = Path(__file__).parent / "web" / "static"


class DemoValidationView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    risk_level: RiskLevel
    issue_codes: tuple[str, ...]


class DemoRoutingView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    validation_route: ValidationRouteAction
    rfq_difference_route: RfqDifferenceRouteAction | None
    rfq_difference_status: RfqDifferenceStatus | None
    final_outcome: DemoFinalOutcome
    path_trace: tuple[str, ...]
    human_review_trigger: HumanReviewTrigger | None


class CompanyDemoApiResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    company_id: str
    company_name: str
    request_id: str
    quote_source_path: str
    config_path: str
    source_quote_company_id: str
    executed_quote_company_id: str
    validation: DemoValidationView
    routing: DemoRoutingView
    screen_flow: DemoScreenFlowView
    external_delegation_results: tuple[ExternalDelegationResult, ...]


class DemoComparisonResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    results: tuple[CompanyDemoApiResult, ...]


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)

    @app.get("/api/demo/comparison", response_model=DemoComparisonResponse)
    def get_demo_comparison() -> DemoComparisonResponse:
        return DemoComparisonResponse(
            results=tuple(
                _to_api_result(summary) for summary in run_comparison_demo()
            ),
        )

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _to_api_result(summary: CompanyDemoSummary) -> CompanyDemoApiResult:
    return CompanyDemoApiResult(
        company_id=summary.company_id,
        company_name=summary.company_name,
        request_id=summary.request_id,
        quote_source_path=summary.quote_source_path,
        config_path=summary.config_path,
        source_quote_company_id=summary.source_quote_company_id,
        executed_quote_company_id=summary.executed_quote_company_id,
        validation=DemoValidationView(
            risk_level=summary.validation_risk_level,
            issue_codes=summary.issue_codes,
        ),
        routing=DemoRoutingView(
            validation_route=summary.validation_route,
            rfq_difference_route=summary.rfq_difference_route,
            rfq_difference_status=summary.rfq_difference_status,
            final_outcome=summary.final_outcome,
            path_trace=summary.path_trace,
            human_review_trigger=summary.human_review_trigger,
        ),
        screen_flow=build_screen_flow_for_summary(summary),
        external_delegation_results=summary.external_delegation_results,
    )


app = create_app()
