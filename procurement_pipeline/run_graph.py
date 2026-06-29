from pathlib import Path

from procurement_pipeline.graph import graph
from procurement_pipeline.load_company_config import load_company_config
from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.nodes.validation import validate_quote_amounts
from procurement_pipeline.state import ProcurementState


DEMO_CASES = (
    (
        Path("data/sample_inputs/quote_comparison_company_a.json"),
        Path("configs/companies/company_a.json"),
    ),
    (
        Path("data/sample_inputs/quote_comparison_company_b.json"),
        Path("configs/companies/company_b.json"),
    ),
    (
        Path("data/sample_inputs/quote_comparison_company_c.json"),
        Path("configs/companies/company_c.json"),
    ),
)


def main() -> None:
    for quote_path, config_path in DEMO_CASES:
        quote_input = load_quote_comparison(quote_path)
        company_config = load_company_config(config_path)
        validation_result = validate_quote_amounts(quote_input, company_config)
        initial_state: ProcurementState = {
            "quote_input": quote_input,
            "company_config": company_config,
            "validation_result": validation_result,
        }
        result = graph.invoke(initial_state)
        print(
            {
                "company_id": result["company_config"].company_id,
                "path_trace": result["path_trace"],
                "rfq_difference_result": result.get("rfq_difference_result"),
                "human_review_result": result.get("human_review_result"),
            },
        )


if __name__ == "__main__":
    main()
