from typing import Literal, assert_never

from pydantic import BaseModel, ConfigDict

from procurement_pipeline.run_graph import CompanyDemoSummary


DemoScreenFlow = Literal[
    "tco_analysis",
    "rfq_resend",
    "human_review",
    "ocr_reparse",
]
DemoTone = Literal["success", "warning", "danger", "info"]


class DemoBadgeView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    tone: DemoTone


class DemoDecisionRowView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    value: str
    tone: DemoTone


class DemoPrimaryActionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    toast_title: str
    toast_message: str


class DemoOutcomeHeroView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    eyebrow: str
    title: str
    summary: str
    badge: DemoBadgeView
    decision_rows: tuple[DemoDecisionRowView, ...]
    primary_action: DemoPrimaryActionView


class DemoScreenFlowView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    current_flow: DemoScreenFlow
    srm_steps: tuple[str, ...]
    fourth_step_title: str
    screen_message: str
    next_action_label: str
    outcome_hero: DemoOutcomeHeroView


def build_screen_flow_for_summary(
    summary: CompanyDemoSummary,
) -> DemoScreenFlowView:
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
                outcome_hero=DemoOutcomeHeroView(
                    eyebrow="A사 정상 흐름",
                    title="허용 범위 안, TCO 분석으로 진행",
                    summary=(
                        "RFQ 회신 조건이 회사 기준 안에 있어 최종 총비용 비교가 "
                        "이번 화면의 핵심 업무입니다."
                    ),
                    badge=DemoBadgeView(label="정상 흐름", tone="success"),
                    decision_rows=(
                        DemoDecisionRowView(
                            label="판단",
                            value="RFQ 조건 통과",
                            tone="success",
                        ),
                        DemoDecisionRowView(
                            label="주요 화면",
                            value="TCO 분석",
                            tone="info",
                        ),
                        DemoDecisionRowView(
                            label="다음 업무",
                            value="구매품의 진행",
                            tone="success",
                        ),
                    ),
                    primary_action=DemoPrimaryActionView(
                        label="구매품의로 진행",
                        toast_title="TCO 분석 완료",
                        toast_message=(
                            "추천 공급업체와 총비용 근거를 구매품의 화면으로 넘깁니다."
                        ),
                    ),
                ),
            )
        case "rfq_resend":
            return DemoScreenFlowView(
                current_flow="rfq_resend",
                srm_steps=(*shared_steps, "RFQ 재전송"),
                fourth_step_title="RFQ 재전송",
                screen_message=(
                    "B사 정책 기준에서 가격 조건을 통과한 공급업체가 "
                    "최소 비교 기준보다 부족합니다. RFQ 재요청이 필요합니다."
                ),
                next_action_label="RFQ 재전송 요청",
                outcome_hero=DemoOutcomeHeroView(
                    eyebrow="B사 최소 비교 기준 미달",
                    title="가격 조건 통과 업체 부족",
                    summary=(
                        "B사 정책 기준은 최소 2개 이상의 가격 조건 통과 견적이 "
                        "있어야 TCO 비교를 진행합니다. 현재는 A 가온정밀 1개만 "
                        "통과해 RFQ 재요청 대상으로 봅니다."
                    ),
                    badge=DemoBadgeView(label="가격 조건 초과", tone="warning"),
                    decision_rows=(
                        DemoDecisionRowView(
                            label="가격 통과 업체",
                            value="1개 / 최소 2개",
                            tone="warning",
                        ),
                        DemoDecisionRowView(
                            label="TCO 처리",
                            value="TCO 비교 기준 미달",
                            tone="danger",
                        ),
                        DemoDecisionRowView(
                            label="다음 업무",
                            value="RFQ 재요청",
                            tone="warning",
                        ),
                    ),
                    primary_action=DemoPrimaryActionView(
                        label="RFQ 재전송 요청",
                        toast_title="RFQ 재전송 요청",
                        toast_message=(
                            "가격 조건 초과 사유와 함께 공급업체 재확인 요청을 생성합니다."
                        ),
                    ),
                ),
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
                outcome_hero=DemoOutcomeHeroView(
                    eyebrow="C사 납기 조건 초과",
                    title="납기 조건 초과, 담당자 검토 필요",
                    summary=(
                        "회신 납기가 C사 허용 일수를 넘어 자동 재요청보다 구매 "
                        "담당자 판단이 먼저 필요한 상태입니다."
                    ),
                    badge=DemoBadgeView(label="납기 조건 초과", tone="warning"),
                    decision_rows=(
                        DemoDecisionRowView(
                            label="초과 항목",
                            value="납기 허용 범위 초과",
                            tone="warning",
                        ),
                        DemoDecisionRowView(
                            label="자동 처리",
                            value="담당자 검토로 전환",
                            tone="info",
                        ),
                        DemoDecisionRowView(
                            label="다음 업무",
                            value="구매 담당자 검토",
                            tone="warning",
                        ),
                    ),
                    primary_action=DemoPrimaryActionView(
                        label="담당자 검토 요청",
                        toast_title="담당자 검토 요청",
                        toast_message=(
                            "납기 조건 초과 사유와 판단 근거를 구매 담당자에게 전달합니다."
                        ),
                    ),
                ),
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
                outcome_hero=DemoOutcomeHeroView(
                    eyebrow="입력 신뢰도 확인",
                    title="OCR 재파싱 필요",
                    summary=(
                        "견적 입력값 신뢰도 문제가 먼저 해결되어야 다음 구매 업무로 "
                        "넘어갈 수 있습니다."
                    ),
                    badge=DemoBadgeView(label="입력 확인 필요", tone="danger"),
                    decision_rows=(
                        DemoDecisionRowView(
                            label="검증 결과",
                            value="입력 신뢰도 확인 필요",
                            tone="danger",
                        ),
                        DemoDecisionRowView(
                            label="다음 업무",
                            value="OCR 재파싱",
                            tone="warning",
                        ),
                    ),
                    primary_action=DemoPrimaryActionView(
                        label="OCR 재파싱 요청",
                        toast_title="OCR 재파싱 요청",
                        toast_message="견적서 OCR 재파싱 요청을 생성합니다.",
                    ),
                ),
            )
        case unreachable:
            assert_never(unreachable)
