# ERP Procurement Pipeline Demo

LangGraph 기반 ERP 조달 검증 파이프라인 데모입니다.

이 프로젝트는 견적 JSON을 검증하고, 신뢰할 수 있는 값만 TCO 계산으로 넘기는 흐름을 단계적으로 구현합니다. 최종 목표는 회사별 정책 차이도 config와 conditional edge로 분리하는 것이지만, 현재 이슈 9에서는 모든 회사가 공통으로 거치는 입력 신뢰도 검증 분기만 다룹니다.

## What This Demo Proves

이 프로젝트의 핵심 아이디어는 다음과 같습니다.

> 견적서 파싱 결과가 TCO 계산에 들어가기 전에, 공통 검증 게이트가 먼저 값의 신뢰도를 판단한다.
> 회사별 허용 한도 차이는 그 다음 단계에서 별도 config 기반 분기로 처리한다.

즉, `robust z-score`로 단가가 너무 튀는지 확인하고, 위험도에 따라 다음 경로를 나눕니다.

```text
normal   -> TCO 계산
warning  -> HITL mock 요청
critical -> OCR 재파싱 mock 요청
```

여기서 `warning`은 시장 상황이나 사회적 맥락 때문에 사람이 봐야 할 수 있는 값이고, `critical`은 OCR/parsing 결과 자체를 다시 확인해야 할 정도로 위험한 값으로 둡니다.

## Final Target Pipeline

최종적으로 만들고 싶은 파이프라인은 다음과 같습니다.

```text
견적 JSON 입력
-> 단가 sanity check
-> robust z-score 기반 공통 검증
-> 필요 시 OCR 재파싱 mock 또는 HITL mock
-> RFQ 원안 대비 공급업체 응답 비교
-> 회사별 tolerance 기반 조건부 라우팅
-> 필요 시 RFQ 재전송 또는 HITL
-> TCO 계산
-> 발표용 결과 정리 또는 API/목업 표시
```

## Current Status

현재 구현은 이슈 9, 공통 검증 라우팅까지 포함합니다.

입력 JSON schema, 회사 config schema, 이상치 검증, 과거 단가 baseline 검증, risk scoring, TCO 계산, 그리고 `risk_level` 기반 공통 graph 분기가 추가되었습니다.

현재 구현된 주요 처리 재료:

```text
견적 입력 schema
회사 config schema
검증 결과 schema
risk_level 산출
공통 validation routing 결과
OCR 재파싱 mock 결과
HITL 요청 mock 결과
TCO 계산 결과
LangGraph conditional edge
```

## Design Principles

- 노드는 회사를 몰라야 합니다.
- 공통 검증 분기와 회사별 정책 분기를 섞지 않습니다.
- `risk_level`은 회사 정책이 아니라 입력 신뢰도 신호로 봅니다.
- 회사별 규칙은 다음 단계에서 config 파일로 분리합니다.
- 실제 분기는 노드 내부가 아니라 LangGraph conditional edge에서 처리합니다.
- LLM/OCR/ERP 같은 외부 연동은 mock과 adapter 경계를 나눠 단계적으로 붙입니다.

## Project Structure

```text
.
├── requirements.txt
├── configs/
│   └── companies/
├── data/
│   ├── sample_inputs/
│   └── sample_outputs/
├── procurement_pipeline/
│   ├── graph.py
│   ├── state.py
│   ├── run_graph.py
│   ├── nodes/
│   │   ├── validation.py
│   │   ├── validation_routing.py
│   │   ├── baseline_validation.py
│   │   ├── risk_scoring.py
│   │   └── tco_calculation.py
│   └── schemas/
│       ├── quote_input.py
│       ├── company_config.py
│       ├── validation_result.py
│       ├── validation_routing_result.py
│       └── tco_result.py
└── tests/
    ├── test_company_config.py
    ├── test_quote_input.py
    ├── test_validation_node.py
    ├── test_validation_routing.py
    ├── test_graph.py
    ├── test_run_graph.py
    ├── test_risk_scoring.py
    └── test_tco_calculation.py
```

## Setup

Python 가상환경을 만듭니다.

```powershell
python -m venv .venv
```

필요한 패키지를 설치합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PowerShell에서 `Activate.ps1` 실행이 막힐 수 있으므로, 이 프로젝트에서는 `.venv` 안의 Python을 직접 실행하는 방식을 기본으로 사용합니다.

## Run

샘플 견적과 회사 config를 읽고 공통 검증 graph를 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m procurement_pipeline.run_graph
```

정상 출력에는 `routing_result`와 `path_trace`가 포함됩니다.

```text
'routing_result': ValidationRoutingResult(...)
'path_trace': ('route_validation', 'tco_calculation')
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

현재 브랜치 기준 정상 결과:

```text
45 passed
```

## Roadmap

- 이슈 1: 프로젝트 셋업
- 이슈 2: 입력 JSON 스키마 정의
- 이슈 3: 회사별 config 정의
- 이슈 4: Robust 수치 이상치 검증 기본 구현
- 이슈 5: 과거 단가 baseline 검증 노드
- 이슈 6: 수량 기반 과거 단가 baseline 검증 고도화
- 이슈 7: 검증 결과 risk scoring
- 이슈 8: TCO 계산
- 이슈 9: robust z-score 기반 OCR 재파싱/HITL 공통 검증 분기
- 이슈 10: RFQ 원안 대비 공급업체 응답 차이 기반 회사별 라우팅
- 이슈 11: 외부 위임 mock
- 이슈 12: FastAPI + HTML 목업 연결
- 이슈 13: TCO 산식 고도화
- 이슈 14: 단가 sanity check 노드

## Not Built Yet

- RFQ 원안 대비 공급업체 응답 비교
- 회사별 `price_tolerance` / 납기 tolerance 기반 conditional edge
- RFQ 재전송 mock 노드
- 동일 입력 A사/B사/C사 분기 시연
- 외부 위임 mock
- FastAPI + HTML 목업 연결
- TCO 산식 고도화
- 단가 sanity check 노드

## Next Issue Candidate

### 이슈 10: RFQ 원안 대비 견적 차이 기반 회사별 라우팅

목표는 RFQ를 보낼 때 기대했던 가격/납기와 공급업체가 실제로 보낸 가격/납기를 비교하고, 회사별 허용 한도에 따라 다음 경로를 다르게 고르는 것입니다.

포함 범위:

- RFQ 원안의 예상 가격/납기와 공급업체 응답 가격/납기를 비교합니다.
- 회사 config에 가격/납기 tolerance와 초과 시 route를 둡니다.
- A사는 허용 범위 안이면 TCO로 진행합니다.
- B사는 허용 범위 초과 시 RFQ 재전송 mock으로 보냅니다.
- C사는 허용 범위 초과 시 HITL mock으로 보냅니다.
- 노드 내부에 `if company_id == ...` 같은 회사별 분기를 넣지 않습니다.

제외 범위:

- 실제 ERP 연동
- 실제 담당자 알림
- FastAPI 또는 화면 연결
- LLM 호출
- 최종 공급사 자동 선정
