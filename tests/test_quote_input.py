from pathlib import Path

from procurement_pipeline.load_quote import load_quote_comparison


SAMPLE_INPUT_PATH = Path("data/sample_inputs/quote_comparison.json")
COMPANY_A_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_a.json")
COMPANY_B_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_b.json")
COMPANY_C_INPUT_PATH = Path("data/sample_inputs/quote_comparison_company_c.json")


def test_load_quote_comparison_reads_sample_json() -> None:
    # Given: a sample quote comparison JSON file.
    sample_path = SAMPLE_INPUT_PATH

    # When: the file is loaded through the input schema.
    quote_input = load_quote_comparison(sample_path)

    # Then: the main request fields are available as typed Python attributes.
    assert quote_input.request_id == "20260605-0001"
    assert quote_input.company_id == "COMPANY-DEMO"
    assert quote_input.base_currency == "KRW"
    assert quote_input.quantity == 500
    assert quote_input.rfq_terms.expected_unit_price == 273
    assert quote_input.rfq_terms.expected_delivery_date.isoformat() == "2026-06-15"


def test_load_quote_comparison_keeps_multiple_supplier_quotes() -> None:
    # Given: a sample quote comparison JSON file with several supplier quotes.
    sample_path = SAMPLE_INPUT_PATH

    # When: the file is loaded through the input schema.
    quote_input = load_quote_comparison(sample_path)

    # Then: every supplier quote is parsed into the typed quote list.
    assert len(quote_input.quotes) == 3
    assert quote_input.item.name == "BOLT M12-40"
    assert quote_input.quotes[0].supplier_id == "SUP-GAON"
    assert quote_input.quotes[0].unit_price == 260
    assert quote_input.quotes[1].memo == "우선 추천 공급업체, 단가와 납기 조건 확인 필요."


def test_company_samples_keep_same_non_company_quote_terms() -> None:
    # 준비: 같은 경제 조건을 회사별 sample로 나눠 둡니다.
    quote_a = load_quote_comparison(COMPANY_A_INPUT_PATH)
    quote_b = load_quote_comparison(COMPANY_B_INPUT_PATH)
    quote_c = load_quote_comparison(COMPANY_C_INPUT_PATH)

    # 실행: company_id를 제외한 비교 대상 값을 모읍니다.
    comparable_a = quote_a.model_dump(exclude={"company_id"})
    comparable_b = quote_b.model_dump(exclude={"company_id"})
    comparable_c = quote_c.model_dump(exclude={"company_id"})

    # 검증: 같은 견적 조건이 회사 config 차이만으로 다른 경로를 타야 합니다.
    assert quote_a.company_id == "COMPANY-A"
    assert quote_b.company_id == "COMPANY-B"
    assert quote_c.company_id == "COMPANY-C"
    assert comparable_a == comparable_b == comparable_c
