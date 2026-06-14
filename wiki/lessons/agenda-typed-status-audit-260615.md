---
type: lesson
title: 안건 유형별 parse_status 확대 검토 — 320사 전수조사 후 "확대 불필요" 결정
date: 2026-06-15
tags: [shareholder_meeting, parser, audit, decision]
related:
  - lessons/tool-coverage-audit-260612
  - 260615_agenda_typed_status_audit
---

# 안건 유형별 parse_status 확대 검토 (결정: 불필요)

## 질문

보수한도(`compensation.summary.parse_status`)는 4종 타입화 상태(ok / no_agenda /
one_side_only / foreign_currency / amount_unparsed)를 payload로 노출한다. **다른 주총
안건(이사선임·정관변경·퇴직금 등)에도 같은 타입화 status를 깔아야 하는가?**

## 핵심 통찰 — "빈손"이 아니라 "그럴듯하게 틀림"이 위험

보수한도에 타입화 status가 필요했던 이유는 *누락(missing)*이 아니라 **단위 오류로 값이
그럴듯하게 틀리는 것**(630원 vs 630억)이었다. 이 "plausible wrong" 실패 모드는 **숫자 +
단위를 다루는 안건에만** 생긴다. 텍스트 안건(이름·조문)은 맞거나, 틀리면 검증 게이트
(`_validate_parse_result`) → LLM 폴백이 잡는다 — 조용히 틀린 채 통과하지 않는다.

숫자+단위 안건은 둘뿐이고 **이미 타입화 status를 보유**:
- 보수한도 → `compensation.summary.parse_status`
- 잠정재무제표 → `prov_financials.metrics.extraction_status`

## 측정 (320사 전수: KOSPI 200 + KOSDAQ 120, scope=full, 분석 318사)

silent-failure = "안건 트리엔 분류돼 있는데 상세 파싱이 빈" 비율:

| 안건 유형 | 보유 | 실패 | 비율 |
|---|---|---|---|
| 이사 선임 | 289 | 0 | **0.0%** |
| 감사위원 선임 | 114 | 0 | **0.0%** |
| 이사 보수한도 | 299 | 6 | 2.0% (parse_status 보유) |
| 감사 보수한도 | 92 | 0 | 0.0% |
| 퇴직금 | 32 | 2 | 6.2% (n 작음 — 현대글로비스·제이에스링크) |
| 정관 변경 | 299 | 2 | 0.7% (기업은행·한국금융지주) |

타입화 status 분포(이미 동작 중):
- 보수한도: ok 290 / no_agenda 18 / amount_unparsed 3 / one_side_only 5 / foreign_currency 2
- 잠정재무: success 307 / no_data 11

## 결정

**신규 타입화 parse_status는 추가하지 않는다.**

- 텍스트 안건(이사선임·감사위원)은 silent-failure 0.0% — 깔아도 실익 없는 ceremony.
- 숫자+단위 위험이 있는 두 안건은 이미 status 보유 + 정상 동작(엣지 케이스를 실제로 분류).
- 비제로 잔여(정관 0.7%, 퇴직금 6.2%)는 "그럴듯하게 틀림"이 아니라 *누락*이라 검증 게이트가
  잡을 수 있는 종류이고, 표본도 작다(금융지주 정관 양식 차이 2사 / 퇴직금 2사).

## 잔여 메모 (당장 조치 X)

- 정관변경 누락 2사 = **기업은행·한국금융지주**(금융지주 정관 비교표 양식 차이). 양식 변형
  추가 후보지만 0.7% 빈도라 우선순위 낮음.
- 320사 중 2사 에러(신영증권·SNT다이내믹스) — 단발, 재현 시 별도 확인.
- 이미지 본문 공고 1건(rcept 20260310003035, 소집통지서 jpg 6장) — 텍스트 파싱 불가 구조,
  IMAGE_NOTICE로 감지됨.

raw: [[260615_agenda_typed_status_audit]] / 스크립트: `scripts/agenda_typed_status_audit.py`
