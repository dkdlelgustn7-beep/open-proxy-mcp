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

## 후속 정밀 추적 (2026-06-15, 정관변경 2사·에러 2사)

정관변경 누락 2사를 원문으로 추적하니 **원인이 서로 달랐다** (처음엔 "둘 다 섹션 부재"로
오판 → 원문 확인으로 정정):

- ✅ **기업은행 — 수정 완료.** '목적사항별 기재사항' 섹션 **있음**(1회). 그런데 DART 원문이
  정관변경을 별도 안건 detail로 안 나누고 **'재무제표의 승인' detail 하위 섹션('가.집중투표
  배제…정관의 변경' / '나.그 외의 정관변경에 관한 건')으로 흡수**. `parse_aoi_xml`이 detail의
  title/category에만 '정관'을 보고 판단해 통째로 skip → 안쪽 `변경전 내용/변경후 내용` 표를
  놓침. **fix: detail 필터에 section heading '정관'도 인정**(parser.py). 표 추출은 변경전 AND
  변경후 헤더를 요구하므로 재무제표·보수 표는 자동 배제 = regression-safe by construction.
  검증: 기업은행 0→1, 정상 15사 값 불변, 60사 회귀 에러 0·폭증 0(최대 13건).
- 🟡 **한국금융지주 — 미해결(기업은행과 같은 뿌리, 다른 증상).** (※ 추적 중 2회 정정: 처음
  '소집결의'(24KB, 섹션 부재)를 잘못 봄 → tool은 실제로 올바른 '소집공고'(rcept …000993,
  279KB)를 집고 있었음. 한 회사가 같은 날 `주주총회소집공고`(…000993)와 `주주총회소집결의`
  (…801215)를 동시 제출하니 probe 시 문서 타입 혼동 주의.)
  **진짜 원인**: 기업은행과 동일하게 DART 원문이 모든 안건을 카테고리별로 안 나누고
  **`<library>` 1개**에 첫 안건 제목으로 몰아넣음(한국금융지주 "□ 이사의 선임" / 기업은행
  "□ 재무제표의 승인"). 차이는 library **내부** 안건 분리(`_parse_library_block`):
  기업은행은 전 섹션을 한 detail에 보존(→ section-heading fix가 닿음), 한국금융지주는
  분리 중 **정관·재무제표 섹션이 드롭**돼 detail에 이사선임 15섹션만 남음(→ fix 못 닿음).
  진짜 fix는 `_parse_library_block`의 단일-library 다중안건 분리 로직 보강인데, 전 종목 공용
  파서라 marketwide 회귀 필수 → 별도 작업으로 분리.

### 교훈 추가
- **probe 시 소집공고 vs 소집결의 구분**: 같은 날 둘 다 제출되며 키워드 '소집'이 둘 다 매칭.
  결의(…8xxxxx)는 짧은 결정공시, 공고(…0xxxxx)가 목적사항별 기재사항 본문. tool은 공고를
  올바로 선택하므로 진단도 tool 경로(build_…_payload)로 확인할 것 — raw rcept 직접 집으면 오진.
- **detail title만으로 안건 종류 판단 금지**: DART가 다중 안건을 단일 library에 몰아넣는
  공시(금융지주 다수 추정)에선 detail title이 첫 안건 1개만 대표 → section 레벨까지 봐야 함.

- 320사 중 2사 에러(신영증권·SNT다이내믹스) = **로컬 SSL(KIND 스크래핑) 문제**였고, 진짜
  코드 결함은 "KIND fetch 실패가 전체 페이로드 크래시"(DartClientError만 catch). graceful
  degrade로 수정 완료(별도 커밋). 프로덕션(Fly.io)에선 SSL 미발생이나 KIND는 외부 사이트라
  네트워크 blip 가능 → 견고성 개선.
- 이미지 본문 공고 1건(rcept 20260310003035, 소집통지서 jpg 6장) — 텍스트 파싱 불가 구조,
  IMAGE_NOTICE로 감지됨.

raw: [[260615_agenda_typed_status_audit]] / 스크립트: `scripts/agenda_typed_status_audit.py`
