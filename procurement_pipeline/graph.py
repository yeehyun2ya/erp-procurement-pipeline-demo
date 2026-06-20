from langgraph.graph import END, START, StateGraph

from procurement_pipeline.nodes.placeholders import (
    prepare_decision_placeholder,
    receive_quote_placeholder,
)
from procurement_pipeline.state import ProcurementState


# StateGraph: 같은 State 모양을 들고 노드와 엣지를 연결하는 LangGraph 그래프 빌더입니다.
builder = StateGraph(ProcurementState)
builder.add_node("receive_quote_placeholder", receive_quote_placeholder)
builder.add_node("prepare_decision_placeholder", prepare_decision_placeholder)

# Edge: 한 단계가 끝난 뒤 다음 노드로 이동하는 연결선입니다.
builder.add_edge(START, "receive_quote_placeholder")
builder.add_edge("receive_quote_placeholder", "prepare_decision_placeholder")
builder.add_edge("prepare_decision_placeholder", END)

graph = builder.compile()
