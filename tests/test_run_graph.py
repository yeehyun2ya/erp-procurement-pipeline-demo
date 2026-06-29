import pytest

from procurement_pipeline.run_graph import main


def test_run_graph_prints_company_rfq_difference_paths(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 준비 / 실행: demo runner를 실제로 호출합니다.
    main()

    captured = capsys.readouterr()

    # 검증: 같은 견적 조건이 회사 config에 따라 다른 경로를 탑니다.
    assert "path_trace" in captured.out
    assert "route_validation" in captured.out
    assert "rfq_difference" in captured.out
    assert "COMPANY-A" in captured.out
    assert "COMPANY-B" in captured.out
    assert "COMPANY-C" in captured.out
    assert "proceed_tco" in captured.out
    assert "resend_rfq" in captured.out
    assert "request_human_review" in captured.out
    assert "tco_calculation" in captured.out
    assert "rfq_resend" in captured.out
    assert "human_review_request" in captured.out
    assert "rfq_difference_result" in captured.out
    assert "human_review_result" in captured.out
    assert "review_trigger='rfq_difference'" in captured.out
