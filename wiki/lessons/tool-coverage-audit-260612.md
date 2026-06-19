---
type: lesson
title: audit 미커버 툴 전수조사 — proxy_result 0건 회귀·DART 단위 오염·날짜 비일관
context: 2026-06-12 "전수조사가 미흡했던 툴" 매핑 → ① ownership ② 값 정확도 ③ evidence·proxy_result
date_learned: 2026-06-12
related: [ownership-summary-integrity-260610]
---

# audit 미커버 툴 전수조사 (260612)

## Context

17개 툴의 audit 커버리지를 매핑하니 두 층위가 갈렸다: 260517 baseline은 **파싱 성공률**
(exact/no_filing)만 검증했고, **내용 정확도**(값이 맞는가) deep audit은 일부 툴만 있었다.
미흡 순위: ① ownership(재설계 후 33사뿐) ② dilutive·restructuring·deals(값 미검증)
③ evidence·proxy_result(baseline 자체 없음). 순서대로 전수조사했다.

## ① ownership 450사 — [[ownership-summary-integrity-260610]] 후속 섹션 참조
DART 원본 단위 오염 2사(LS ×1,000 / LS에코 ×1,000,000) 자가 교정 + 분모 괴리 경고.

## ② dilutive·restructuring·deals 값 정확도 (exact 회사만 286사)

- **corporate_deals: 행 1,560 · 값필드 채움률 100% · issue 0** — 원문 regex 추출(취득금액·
  자기자본%)이 가장 위험하다고 봤는데 완벽. 금액·비율 전수 깨끗.
- **dilutive·restructuring: 금액·비율 정상, 날짜 676건이 한국어 원본**('2026년 02월 11일') —
  OPM 전체가 ISO 관행인데 두 툴만 DART 구조화 API 원본 형식 그대로. `_normalize_row_dates`
  (수집부 일괄, `*_date` 필드의 한국어/8자리 → ISO)로 통일. 카카오 '2026년 02월 11일'→'2026-02-11' 검증.
- 채움률 dilutive 46.5%/restructuring 64.4%는 DART optional 필드 sparse 반영(정상).

## ③-1 evidence — 결정론 8케이스 매트릭스 (DART 무호출 툴)

DART/KIND 구분·날짜 유도·viewer_url·evidence_id 추출·형식 거부 모두 정상. 엣지 1건:
**불가능 달력 날짜**('2024-13-20')가 exact 통과 → 존재 불가 rcept_no이므로 달력 검증 추가
(strptime, requires_review로 강등).

## ③-2 proxy_result — 🔴 핵심 기능이 통째로 죽어 있었다

30사 baseline에서 **agenda_results 0/30**. 역추적:
- upstream(shareholder_meeting results scope)은 정상 — 안건 행을 `data.results.items`로 노출
  (가결/찬성률 완전체).
- proxy_result는 **구 키 `data.agenda_results`를 읽고 있었다** — 결과 파싱 개편(5/17 DART-first)
  때 upstream 키가 바뀌었는데 소비자가 미수정 → **결과가 조용히 항상 0건** ("no_results"로 위장).
- `results.items` 우선 + 구 키 fallback으로 교정 → **15/15 복구** (삼성 9건 가결, 현대차 16건...).

부수 확인: **과거 연도(2024·2025) 주총 결과는 소스 한계** — 당시 결과공시가 "원안대로 승인"
서술형(가결/찬반율 키워드 0회)이라 파싱 불가. 2026년 공시부터 찬반율 표 형식. 툴 결함 아님.

## 추가 검증 + 단위 파싱 sweep (2026-06-13)

**proxy_result 추가 케이스** — 나머지 KOSPI 10사(10/10) + KOSDAQ 5사(5/5, baseline엔 KOSDAQ
results exact가 없어 직접 선정). outcome 다양성 확보: **가결 124 / 부결 8 / 미결 4** —
부결·미결 전부 고려아연(영풍-MBK 분쟁, 안건 32건)에서 나와 현실 정합.

**단위 파싱 sweep** — 재무/주식 단위(원·백만원·천주) 오염을 교차 불변식으로 탐지:

| 표면 | 불변식 | 검사량 | 결과 |
|---|---|---|---|
| dividend | 내재주식수=총액/DPS 범위 + **qb(원) vs qf(백만) 동분기 교차** | 276+8 | clean |
| treasury | 금액÷수량=단가 ∈ [500, 300만원] | 212 | clean |
| deals | ② 1,560행 채움률 100% (라벨 '(원)' 명시) | — | clean |
| dilutive | 금액 자릿수 (존재분 sparse) | 12 | clean |
| ownership | 지분율 anchor (이번 세션 sanitizer) | 450사 | **유일한 실사고 2사** |
| financial_metrics | 4분기합=연간·듀퐁 등 (260612 412사) | — | 기보유 |

→ **단위 사고는 ownership의 DART 원본 오염 1종뿐.** 필드명에 단위 접미사를 박는 관행
(`total_amount_mil`/`amount_krw`/`dps_common_krw`)이 단위 혼동을 구조적으로 막고 있다.

검사 과정의 메타 교훈 2건: ① dividend 1차 sweep이 **틀린 키(cash_dps)를 봐서 0/20 가짜
clean** — 검사량(checked) 카운트로 적발. 침묵은 성공이 아니다 — sweep은 반드시 양성
검사량을 보고하라. ② 교차검사 1차의 이슈 9건은 단위가 아니라 **join 버그**(quarterly_full은
최신연도 전용인데 전 연도와 매칭 → 비율 0.25-9배 = 배당 증감). 비율이 10^3/10^6이 아니면
단위 사고가 아니다 — flag의 *크기 패턴*으로 원인을 구분하라.

## 2차: seam·render·corp_gov·production 4축 (2026-06-13)

proxy_result 제거(17→16, 핵심을 results tool이 3콜 vs 32콜로 대체·cross-match 미구현·실사용 부재)
후 남은 축 전수:

- **seam audit (proxy_advise 8사)** — composite 출력 vs 직접 호출 교차. ownership/financial
  이음새 정상, **고려아연 crash 발견**: 보수 파서가 headcount를 '7' 문자열로 내려
  `limit // headcount` TypeError → `_comp_amount`에서 일괄 숫자 강제 (근원 fix).
- **render smoke (16툴 × 31케이스)** — FastMCP `call_tool` 경로로 build+render 전체.
  **솔루엠 render crash 발견**: perf matrix `roe.get('avg', 0)`인데 avg가 None '값'으로
  존재해 default 무력 → `None:.1f` TypeError → `or 0` 강제. 교정 후 31/31.
  payload audit이 못 보는 render 레이어 버그를 정확히 잡음 — **두 crash 모두 분쟁사·중형사**.
- **corp_gov 값 정확도 (30사)** — 15지표 × 30사 = 450값 전부 O/X 형식, 기록된 기준값과
  정확 일치 (삼성 13/15=86.7%·X항목 집중투표제/배당예측, KT&G·포스코 15/15).
- **production MCP smoke (fly.io)** — 정식 MCP 클라이언트로 initialize→list→call.
  ownership 재설계(100% 분해·5% 실세) production 반영 확인. (배포 후 1·2번 키 모두 정상
  재확인.) 주의: 1차 smoke에서 1번 키 호출이 "API 조회 실패: 100"으로 보였으나,
  curl 직접 검증 결과 **키는 status 000 정상** — 구버전 production + 일시 응답이었고
  키 무효가 아니었다. **단발 에러로 키 무효를 단정하지 말 것**(아래 메타 참조).

메타: corp_gov 1차 sweep도 **틀린 키(compliance) 가짜 clean**이었다 — 첫 행 출력으로 적발,
'current' 키로 재실행. 이번 세션에서 가짜 clean 3회 — **sweep 작성 시 첫 케이스의 실제
키/행을 반드시 출력하고 양성 검사량을 보고하는 것을 표준으로**.

메타2 (오진 정정): production 1차 smoke의 "키 무효" 결론은 **틀렸다**. 단발 "실패: 100"을
보고 키 무효로 단정했으나, curl로 직접 치니 status 000. 인프라 이상(키/네트워크/권한)은
**단발 증상으로 단정하지 말고 가장 단순한 직접 호출(curl)로 격리 확인**해야 한다 — tool을
통한 실패는 구버전·일시응답·rate limit 등 교란 변수가 많다.

## Takeaway

- **baseline 없는 툴은 죽어도 모른다.** proxy_result는 핵심 기능이 0건을 반환하면서도
  status는 정상 흐름이라 어떤 모니터링에도 안 걸렸다. 모든 툴에 최소 baseline을 깔아라.
- **composite tool은 upstream 키 rename의 조용한 피해자.** upstream 개편 시 소비자(grep으로
  키 사용처)를 같이 갱신하거나, 소비자가 빈 결과일 때 upstream status와 대조해 경고해야 한다.
- **"0건"과 "실패"를 구분하라.** proxy_result는 빈 결과를 no_results로 자연스럽게 위장했다.
  upstream이 exact인데 자기 추출이 0이면 그건 no_data가 아니라 버그 신호다.
- **검사 기준의 오탐도 분류하라.** ②에서 issue 691건 중 실버그는 0, 형식 비일관 676,
  기준 오탐 15(exercise_price_method를 금액으로 오인). 숫자만 보면 과대 평가한다.

## Related

- [[ownership-summary-integrity-260610]] (① 후속 섹션)
- audit raw: `260612_deal_tools_value_audit.json` / 스크립트 `scripts/deal_tools_value_audit.py`
