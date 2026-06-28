from pathlib import Path

from procurement_pipeline.graph import graph
from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.validation import validate_quote_amounts
from procurement_pipeline.state import ProcurementState


def main() -> None:
    quote_input = load_quote_comparison(Path("data/sample_inputs/quote_comparison.json"))
    company_config = load_company_config(Path("configs/companies/company_demo.json"))
    validation_result = validate_quote_amounts(quote_input, company_config)
    initial_state: ProcurementState = {
        "quote_input": quote_input,
        "company_config": company_config,
        "validation_result": validation_result,
    }
    result = graph.invoke(initial_state)
    print(result)


if __name__ == "__main__":
    main()
