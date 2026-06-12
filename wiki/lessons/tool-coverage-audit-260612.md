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
