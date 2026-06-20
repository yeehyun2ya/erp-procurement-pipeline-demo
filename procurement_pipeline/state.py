from typing_extensions import TypedDict


class ProcurementState(TypedDict):
    # State: 그래프 전체를 지나가며 노드들이 공유하는 데이터 상자입니다.
    quote_id: str


class ProcurementStateUpdate(TypedDict, total=False):
    # Node는 State 전체가 아니라 바뀐 값만 부분적으로 반환할 수 있습니다.
    quote_id: str
