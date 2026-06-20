from procurement_pipeline.graph import graph
from procurement_pipeline.state import ProcurementState


def test_graph_returns_initial_state_when_placeholders_do_nothing() -> None:
    initial_state: ProcurementState = {"quote_id": "QUOTE-001"}

    result = graph.invoke(initial_state)

    assert result == initial_state
