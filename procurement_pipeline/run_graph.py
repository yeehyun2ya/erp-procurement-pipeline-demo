from procurement_pipeline.graph import graph
from procurement_pipeline.state import ProcurementState


def main() -> None:
    initial_state: ProcurementState = {"quote_id": "QUOTE-001"}
    result = graph.invoke(initial_state)
    print(result)


if __name__ == "__main__":
    main()
