from pathlib import Path
from typing import Final, Literal, assert_never

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

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
DemoScreenFlow = Literal[
    "tco_analysis",
    "rfq_resend",
    "human_review",
    "ocr_reparse",
]


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


class DemoScreenFlowView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    current_flow: DemoScreenFlow
    srm_steps: tuple[str, ...]
    fourth_step_title: str
    screen_message: str
    next_action_label: str


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
        screen_flow=_screen_flow_for_summary(summary),
        external_delegation_results=summary.external_delegation_results,
    )


def _screen_flow_for_summary(summary: CompanyDemoSummary) -> DemoScreenFlowView:
    shared_steps = (
        "공급업체 리스크 분석",
        "RFQ Agent",
        "OCR 파싱 결과",
    )
    match summary.final_outcome:
        case "tco_calculation":
            return DemoScreenFlowView(
                current_flow="tco_analysis",
                srm_steps=(*shared_steps, "TCO 분석"),
                fourth_step_title="TCO 분석",
                screen_message=(
                    "RFQ 회신 조건이 허용 범위 안입니다. "
                    "TCO 분석으로 이동해 최종 추천 업체를 확인합니다."
                ),
                next_action_label="구매품의로 진행",
            )
        case "rfq_resend":
            return DemoScreenFlowView(
                current_flow="rfq_resend",
                srm_steps=(*shared_steps, "RFQ 재전송"),
                fourth_step_title="RFQ 재전송",
                screen_message=(
                    "회신 견적이 RFQ 허용 범위를 초과했습니다. "
                    "TCO 분석 전 공급업체에 RFQ 재확인이 필요합니다."
                ),
                next_action_label="RFQ 재전송 요청",
            )
        case "human_review_request":
            return DemoScreenFlowView(
                current_flow="human_review",
                srm_steps=(*shared_steps, "담당자 검토 요청"),
                fourth_step_title="담당자 검토 요청",
                screen_message=(
                    "RFQ 차이가 담당자 판단이 필요한 수준입니다. "
                    "구매 담당자에게 검토 요청을 생성합니다."
                ),
                next_action_label="담당자 검토 요청",
            )
        case "ocr_reparse":
            return DemoScreenFlowView(
                current_flow="ocr_reparse",
                srm_steps=(*shared_steps, "OCR 재파싱"),
                fourth_step_title="OCR 재파싱",
                screen_message=(
                    "검증 단계에서 입력 신뢰도 문제가 감지되었습니다. "
                    "OCR 재파싱 요청을 생성합니다."
                ),
                next_action_label="OCR 재파싱 요청",
            )
        case unreachable:
            assert_never(unreachable)


app = create_app()
