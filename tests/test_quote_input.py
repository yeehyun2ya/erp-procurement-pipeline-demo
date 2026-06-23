from pathlib import Path

from procurement_pipeline.load_quote import load_quote_comparison


SAMPLE_INPUT_PATH = Path("data/sample_inputs/quote_comparison.json")


def test_load_quote_comparison_reads_sample_json() -> None:
    # Given: a sample quote comparison JSON file.
    sample_path = SAMPLE_INPUT_PATH

    # When: the file is loaded through the input schema.
    quote_input = load_quote_comparison(sample_path)

    # Then: the main request fields are available as typed Python attributes.
    assert quote_input.request_id == "PR-2026-0001"
    assert quote_input.company_id == "COMPANY-DEMO"
    assert quote_input.base_currency == "KRW"
    assert quote_input.quantity == 25


def test_load_quote_comparison_keeps_multiple_supplier_quotes() -> None:
    # Given: a sample quote comparison JSON file with several supplier quotes.
    sample_path = SAMPLE_INPUT_PATH

    # When: the file is loaded through the input schema.
    quote_input = load_quote_comparison(sample_path)

    # Then: every supplier quote is parsed into the typed quote list.
    assert len(quote_input.quotes) == 3
    assert quote_input.item.name == "Hex bolt M12"
    assert quote_input.quotes[0].supplier_id == "SUP-ALPHA"
    assert quote_input.quotes[0].unit_price == 850
    assert quote_input.quotes[1].memo == "Requires minimum order confirmation before shipment."
