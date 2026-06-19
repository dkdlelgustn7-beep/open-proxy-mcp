---
type: lesson
title: 배당 파서 출처 확정 + 누적차분 + 분류 정밀화 + stateless MCP
context: 2026-06-09 dividend 종합 overhaul (출처맵 → 누적차분 파서 → 감사 → 51사 검증 → MCP 이슈)
date_learned: 2026-06-09
related: [배당공시유형, perf-timing-260524]
---

# 배당 파서 출처 확정 + 누적차분 + 분류 정밀화

## Context

배당 tool을 "공시별로 정확히 어떤 항목이 있는지 먼저 파악·문서화한 뒤 진행"하는 원칙으로 대수술.
출처 확정 → 종합 파서 → 중복/시간/정확도 감사 → 51개사 전수검증 → MCP 실사용 테스트에서 발견한
인프라 이슈 2개 해결까지. 우선순위: **정확도 > 시간 > 내용풍부성.**

## Did

- **데이터 출처 맵 확정** ([[배당공시유형]] §7 + 출처맵): A 사업보고서 alotMatter(다년컬럼=권위) /
  B 분기·반기 alotMatter(누적) / C 현금배당결정 공시(기준일·지급일·구분) / D 주주명부폐쇄(기준일)결정.
  alotMatter 15행 전체 구조를 자의적 절단 없이 덤프 후 문서화.
- **분기별 누적차분** (`_quarterly_full_from_cumulative`): 분기/반기/사업보고서의 **누적 DPS를 차분**
  (Q1=1분기, Q2=반기-Q1, Q3=3분기-반기, 결산=연간-3분기)해 보통+우선 DPS + 배당총액 산출.
  결정공시 fiscal-year 추측(`_bucket_fiscal_year`)을 대체 — 무배당 분기 0·우선주·총액 자동 포착.
- **최신연도 4분류**: 중간배당 확정(B) / 확정 전(D 기준일 매칭) / 미공시(payer인데 증거 없음) /
  무배당(직전도 배당 없음). `pre_dividend` 신호 단독 단정 → 전년 notice 오발동 → **target연도 매칭**으로만 선언.
- **중복 감사**: ① pre_dividend 별도 I001 검색을 메인 검색에 통합(호출 -1) ② 비-target 연도 alotMatter
  개별 호출(pending_annual)을 다년컬럼과 중복이라 제거(-2). → 회사당 DART -3.
- **정확도 억제**: per-decision 시가배당률은 개별공시 자주 0/미기재 → 0을 None 억제(연간값이 권위).
- **날짜**: C 4필드(기준일·지급일·주총일·이사회일) + D §2 기준일(선배당-후결의 '확정 전'의 유일 출처, 자회사 제외·연도매칭).
- **stateless MCP** (`open_proxy_mcp/server.py`): MCP 세션이 머신별 in-memory라 fly nrt×2 라우팅 갈리면 "Session not found".
  OPM tool은 무상태(요청마다 키·파라미터 자급)라 `stateless_http=True` → 2머신 유지하며 세션 문제 제거.

## Improved (검증 51사)

- 정합성(분기합=연간) **100%** — 통신·전력·보험·식품·화학·바이오·게임·물류·반도체 전 섹터.
- 케이스 정확: 무배당 분기(KT&G·고려아연)·무배당 연도(SK이노·삼바)·무배당후재개(한전 0→213→1542)·
  급변(영풍 10000→50→5)·특별배당(삼성 2020 결산 1932 [특별])·우선주(현대 12100·미래에셋 250)·소액(삼천당 50)·첫배당(에이피알).
- DART 회사당 -3 호출(중복제거). production stateless 세션없이 3/3 성공.

## Trade-off

- 누적차분은 보고서 4개 호출 → **최신연도에만** 적용(완료연도는 다년컬럼·결정공시로 충분).
- pending_annual 제거 부작용(무배당 연도가 다년컬럼 skip돼 윈도우에서 빠짐) → **액면가/순이익으로 '회사 존재' 판정**해 0-summary 유지로 보정.
- 미공시 vs 무배당: payer면 '미공시'(조기단정 회피), 직전 배당이력 0이면 '무배당'. 선배당-후결의 artifact 흡수.

## Takeaway

- **출처를 먼저 확정·문서화한다.** 공시 원문 트리를 덤프해 어떤 항목이 있는지 본 뒤 파싱 (특정 필드 가정 금지).
- **누적 차분 > 날짜 추측.** 정기보고서 누적값 차분은 결정공시 버킷팅의 경계 오귀속·중복(예비결산)을 원천 제거. 주행거리계 차분과 같다.
- **신호는 target연도 매칭으로 단정한다.** "윈도우 내 아무 notice" 단독 발동은 전년 notice에 오발동(SK이노).
- **같은 정보 다출처면 권위 1개로 통일** + 검색은 raw 1회 후 다중 필터(중복 호출 제거).
- **무상태 tool의 multi-machine MCP는 stateless_http.** 세션 in-memory가 머신 어피니티 문제의 근원.

## Related commits

- `4326f3b` quarterly_full 누적차분 + collector / `44fd31a` pre_dividend 통합 / `0f20744` pending_annual 제거 + yield 억제
- `1f0474e` 확정전 기준일 추출 / `1666ecc` 미공시 분류 / `2f423f6` stateless / `e52eacf` MD 누적차분 표

## Related

- [[배당공시유형]] (§7 alotMatter 구조 + 출처맵 + 4분류)
- [[perf-timing-260524]] (data tool latency 원칙)
- DART rate limit 교훈: 메모리 `feedback_dart_retry_amplification` (독립 client·ReadError 재시도 금지)
