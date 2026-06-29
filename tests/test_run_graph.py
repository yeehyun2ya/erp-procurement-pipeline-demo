import pytest

from procurement_pipeline.load_quote import load_quote_comparison
from procurement_pipeline.run_graph import (
    COMPANY_DEMO_CASES,
    CompanyDemoSummary,
    SHARED_QUOTE_PATH,
    main,
    run_company_demo,
    run_comparison_demo,
)


def test_run_company_demo_uses_one_quote_and_one_company_config() -> None:
    # 준비: 동일 견적 JSON과 B사 config 경로를 준비합니다.
    config_path = COMPANY_DEMO_CASES[1].config_path

    # 실행: 회사 하나에 대해서만 데모를 실행합니다.
    summary = run_company_demo(SHARED_QUOTE_PATH, config_path)

    # 검증: 견적 내용은 공통 파일에서 오고, 실행 회사만 B사 config에 맞춰집니다.
    assert summary.quote_source_path == "data/sample_inputs/quote_comparison_shared.json"
    assert summary.config_path == "configs/companies/company_b.json"
    assert summary.source_quote_company_id == "COMPANY-SHARED"
    assert summary.executed_quote_company_id == "COMPANY-B"
    assert summary.company_id == "COMPANY-B"
    assert summary.final_outcome == "rfq_resend"
    assert tuple(
        delegation.delegation_type
        for delegation in summary.external_delegation_results
    ) == ("erp_approval_request",)
    assert summary.path_trace == (
        "route_validation",
        "rfq_difference",
        "rfq_resend",
    )


def test_run_comparison_demo_reuses_same_quote_for_all_companies() -> None:
    # 준비 / 실행: A/B/C 비교 데모를 실행합니다.
    summaries = run_comparison_demo()

    # 검증: 세 회사 모두 같은 견적 파일에서 출발하지만 config에 따라 다른 끝점으로 갑니다.
    assert tuple(summary.company_id for summary in summaries) == (
        "COMPANY-A",
        "COMPANY-B",
        "COMPANY-C",
    )
    assert {summary.quote_source_path for summary in summaries} == {
        "data/sample_inputs/quote_comparison_shared.json",
    }
    assert tuple(summary.final_outcome for summary in summaries) == (
        "tco_calculation",
        "rfq_resend",
        "human_review_request",
    )
    assert summaries[0].external_delegation_results == ()
    assert tuple(
        delegation.delegation_type
        for delegation in summaries[1].external_delegation_results
    ) == ("erp_approval_request",)
    assert tuple(
        delegation.delegation_type
        for delegation in summaries[2].external_delegation_results
    ) == ("manager_notification",)


def test_run_company_demo_summarizes_validation_human_review_route(
    tmp_path,
) -> None:
    # 준비: RFQ 비교 전에 공통 validation에서 warning이 나는 견적을 만듭니다.
    source_quote = load_quote_comparison(SHARED_QUOTE_PATH)
    warning_quote_path = tmp_path / "quote_warning_before_rfq.json"
    warning_quote = source_quote.model_copy(
        update={
            "quotes": (
                source_quote.quotes[0].model_copy(update={"unit_price": 900}),
                source_quote.quotes[1].model_copy(update={"unit_price": 900}),
                source_quote.quotes[2].model_copy(update={"unit_price": 900}),
                source_quote.quotes[2].model_copy(
                    update={
                        "supplier_id": "SUP-DELTA",
                        "supplier_name": "Delta Supply",
                        "unit_price": 5000,
                    },
                ),
            ),
        },
    )
    warning_quote_path.write_text(warning_quote.model_dump_json(), encoding="utf-8")

    # 실행: 회사 하나에 대해 데모를 실행합니다.
    summary = run_company_demo(
        warning_quote_path,
        COMPANY_DEMO_CASES[0].config_path,
    )

    # 검증: RFQ 비교 결과가 없어도 validation 단계의 사람 검토 요청을 요약합니다.
    assert summary.final_outcome == "human_review_request"
    assert summary.path_trace == ("route_validation", "human_review_request")
    assert summary.rfq_difference_route is None
    assert summary.rfq_difference_status is None
    assert summary.issue_codes == ("UNIT_PRICE_ROBUST_OUTLIER",)
    assert summary.human_review_trigger == "validation_risk"
    assert tuple(
        delegation.delegation_type
        for delegation in summary.external_delegation_results
    ) == ("manager_notification",)


def test_run_graph_prints_company_rfq_difference_paths(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 준비 / 실행: demo runner를 실제로 호출합니다.
    main()

    captured = capsys.readouterr()

    # 검증: 출력은 회사별 비교가 가능한 고정 JSONL 형태입니다.
    output_summaries = tuple(
        CompanyDemoSummary.model_validate_json(line)
        for line in captured.out.splitlines()
    )
    assert tuple(summary.company_id for summary in output_summaries) == (
        "COMPANY-A",
        "COMPANY-B",
        "COMPANY-C",
    )
    assert tuple(summary.final_outcome for summary in output_summaries) == (
        "tco_calculation",
        "rfq_resend",
        "human_review_request",
    )
    assert output_summaries[0].path_trace == (
        "route_validation",
        "rfq_difference",
        "tco_calculation",
    )
    assert output_summaries[1].rfq_difference_route == "resend_rfq"
    assert (
        output_summaries[1].external_delegation_results[0].target_system
        == "erp_approval"
    )
    assert output_summaries[2].human_review_trigger == "rfq_difference"
    assert (
        output_summaries[2].external_delegation_results[0].target_system
        == "procurement_notification"
    )
