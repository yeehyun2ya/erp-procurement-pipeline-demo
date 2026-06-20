from procurement_pipeline.state import ProcurementState, ProcurementStateUpdate


def receive_quote_placeholder(_state: ProcurementState) -> ProcurementStateUpdate:
    # Node: LangGraph에서 실행되는 작업 단계입니다. 지금은 구조 확인용이라 State를 바꾸지 않습니다.
    return {}


def prepare_decision_placeholder(_state: ProcurementState) -> ProcurementStateUpdate:
    # Node: 나중에 사람에게 보여줄 판단 근거를 준비할 자리입니다. 아직 LLM/검증은 호출하지 않습니다.
    return {}
