from fastapi.testclient import TestClient

from procurement_pipeline.api import create_app


def test_demo_comparison_api_returns_validation_and_routing_results() -> None:
    # 준비: FastAPI 앱을 테스트 클라이언트로 실행합니다.
    client = TestClient(create_app())

    # 실행: 발표 화면이 사용할 회사별 비교 API를 호출합니다.
    response = client.get("/api/demo/comparison")

    # 검증: validation route, risk level, 실제 graph 경로가 고정 JSON으로 내려옵니다.
    assert response.status_code == 200
    payload = response.json()
    results = payload["results"]
    assert [result["company_id"] for result in results] == [
        "COMPANY-A",
        "COMPANY-B",
        "COMPANY-C",
    ]
    assert [result["validation"]["risk_level"] for result in results] == [
        "normal",
        "normal",
        "normal",
    ]
    assert [result["routing"]["validation_route"] for result in results] == [
        "proceed_tco",
        "proceed_tco",
        "proceed_tco",
    ]
    assert [result["routing"]["final_outcome"] for result in results] == [
        "tco_calculation",
        "rfq_resend",
        "human_review_request",
    ]
    assert results[0]["routing"]["path_trace"] == [
        "route_validation",
        "rfq_difference",
        "tco_calculation",
    ]
    assert results[1]["routing"]["rfq_difference_route"] == "resend_rfq"
    assert results[2]["routing"]["human_review_trigger"] == "rfq_difference"


def test_demo_comparison_api_returns_screen_flow_for_each_company() -> None:
    # 준비: FastAPI 앱을 테스트 클라이언트로 실행합니다.
    client = TestClient(create_app())

    # 실행: 발표 화면이 사용할 회사별 흐름 제어 API를 호출합니다.
    response = client.get("/api/demo/comparison")

    # 검증: 회사별 최종 결과가 목업의 4단계 화면과 다음 버튼 문구로 변환됩니다.
    assert response.status_code == 200
    results = response.json()["results"]
    flows = {result["company_id"]: result["screen_flow"] for result in results}
    assert flows["COMPANY-A"]["current_flow"] == "tco_analysis"
    assert flows["COMPANY-A"]["fourth_step_title"] == "TCO 분석"
    assert flows["COMPANY-A"]["next_action_label"] == "구매품의로 진행"
    assert flows["COMPANY-A"]["outcome_hero"]["eyebrow"] == "A사 정상 흐름"
    assert flows["COMPANY-A"]["outcome_hero"]["badge"]["label"] == "정상 흐름"
    assert flows["COMPANY-A"]["outcome_hero"]["badge"]["tone"] == "success"
    assert flows["COMPANY-A"]["outcome_hero"]["title"] == (
        "허용 범위 안, TCO 분석으로 진행"
    )
    assert flows["COMPANY-B"]["current_flow"] == "rfq_resend"
    assert flows["COMPANY-B"]["fourth_step_title"] == "RFQ 재전송"
    assert flows["COMPANY-B"]["next_action_label"] == "RFQ 재전송 요청"
    assert flows["COMPANY-B"]["outcome_hero"]["eyebrow"] == "B사 최소 비교 기준 미달"
    assert flows["COMPANY-B"]["outcome_hero"]["badge"]["label"] == "가격 조건 초과"
    assert flows["COMPANY-B"]["outcome_hero"]["title"] == (
        "가격 조건 통과 업체 부족"
    )
    assert flows["COMPANY-B"]["outcome_hero"]["decision_rows"][0]["value"] == (
        "1개 / 최소 2개"
    )
    assert flows["COMPANY-B"]["outcome_hero"]["decision_rows"][1]["value"] == (
        "TCO 비교 기준 미달"
    )
    assert "B사 정책 기준" in flows["COMPANY-B"]["outcome_hero"]["summary"]
    assert "최소 2개" in flows["COMPANY-B"]["outcome_hero"]["summary"]
    assert "A 가온정밀 1개" in flows["COMPANY-B"]["outcome_hero"]["summary"]
    assert flows["COMPANY-C"]["current_flow"] == "human_review"
    assert flows["COMPANY-C"]["fourth_step_title"] == "담당자 검토 요청"
    assert flows["COMPANY-C"]["next_action_label"] == "담당자 검토 요청"
    assert flows["COMPANY-C"]["outcome_hero"]["eyebrow"] == "C사 납기 조건 초과"
    assert flows["COMPANY-C"]["outcome_hero"]["badge"]["label"] == "납기 조건 초과"
    assert flows["COMPANY-C"]["outcome_hero"]["decision_rows"][0]["value"] == (
        "납기 허용 범위 초과"
    )


def test_root_serves_cleaned_systemever_mockup_html() -> None:
    # 준비: FastAPI 앱을 테스트 클라이언트로 실행합니다.
    client = TestClient(create_app())

    # 실행: 브라우저 첫 화면으로 사용할 정적 HTML을 요청합니다.
    response = client.get("/")

    # 검증: 앱 관리용 HTML 복사본이 로그인 컨텍스트만 노출하고 내부 routing debug 패널은 숨깁니다.
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "SystemEver Proactive SRM 시현" in response.text
    assert "loginScreenDisabled" in response.text
    assert "tenant-context-dock" in response.text
    assert 'data-login-company="COMPANY-A"' in response.text
    assert 'data-login-company="COMPANY-B"' in response.text
    assert 'data-login-company="COMPANY-C"' in response.text
    assert "current-tenant-badge" in response.text
    assert "company-switch-btn" in response.text
    assert "company-flow-panel" not in response.text
    assert "flowCompanySelect" not in response.text
    assert "pipeline-result-panel" not in response.text
    assert "처리 이력" not in response.text
    assert "traceToggle" not in response.text
    assert "agentTrace" not in response.text
    assert "Audit Trail" not in response.text
    assert "auditToggleBtn" not in response.text
    assert "회사별 config route" not in response.text
    assert "회사 config 기준" not in response.text
    assert 'if (!flow) return tcoBody();' not in response.text
    assert 'flow?.fourth_step_title || "TCO 분석"' not in response.text
    assert "회사별 처리 결과를 불러오는 중입니다." in response.text
    assert "renderOutcomeHero" in response.text
    assert "renderQuoteRouteReason" in response.text
    assert "다음 업무 판정" in response.text
    assert "조건 확인 후 결정" in response.text
    assert "판정 결과 보기" in response.text
    assert 'id="toOutcome">${escapeHtml(activeScreenFlow()?.fourth_step_title' not in response.text
    assert "왜 ${escapeHtml(flow.fourth_step_title)}인가" not in response.text
    assert "회사 기준 판정" in response.text
    assert "판정 결과" in response.text
    assert "isPriceComparisonShortfall" in response.text
    assert "B사 기준 단가 초과" in response.text
    assert "가격 조건 통과" in response.text
    assert "outcome_hero" in response.text
    assert "decision_rows" in response.text
