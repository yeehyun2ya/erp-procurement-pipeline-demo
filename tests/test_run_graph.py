import pytest

from procurement_pipeline.run_graph import main


def test_run_graph_prints_common_validation_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main()

    captured = capsys.readouterr()

    assert "path_trace" in captured.out
    assert "route_validation" in captured.out
    assert "tco_calculation" in captured.out
    assert "routing_result" in captured.out
