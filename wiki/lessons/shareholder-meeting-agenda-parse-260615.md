---
type: lesson
title: 주총 안건 파싱 점검 — 보수한도 단위 버그 + 카테고리 분류 부재 (진행중)
context: 2026-06-15 "KOSPI 시총 상위 50 보수한도 상향/하향" → "모든 주총 안건 점검" 확장
date_learned: 2026-06-15
related: [proxy-advise-perf-fact-260614, order-contracts-260613, agenda-typed-status-audit-260615, financial-metrics-evidence-fsdiv-260615, holder-table-parser-260615]
---

# 주총 안건 파싱 전수 점검 (진행중 — 다른 컴퓨터에서 이어갈 것)

## Context

"KOSPI 시총 상위 50 이사 보수한도 상향/하향" 질문에서 출발 → 보수한도 단위 미환산 버그 발견 →
사용자 지시로 **모든 주총 안건 파싱**을 코스피+코스닥 큰 샘플에서 정확도·속도 regression 없이
점검 + 필요 시 warning/raw 폴백. 방법론: **큰 샘플 진단 → 실패 유형 분류 → 폴백 → regression 측정**.

## 발견된 문제 + 수정 (완료)

### 1. 보수한도 단위 미환산 (commit f68c274)

DART 보수한도 공시가 단위를 표 헤더(`(단위 : 명, 억원)`)나 표 직전 텍스트(`(단위: 백만원)`)에
두고 **금액 셀엔 숫자만**(`630`) 적는데, `_parse_krw_amount`가 단위 없는 숫자를 원 단위로 오인.
→ 두산 `630`을 630원으로(실제 630억), LG엔솔 `6,000`을 6천원으로(실제 60억).

**수정** (`open_proxy_mcp/tools/parser.py`):
- `_parse_krw_amount(text, fallback_unit)` — 단위 없는 숫자에 표 헤더 단위 적용
- `parse_compensation_xml`이 표 블록에서 단위 추적 (`comp_unit`)
- 블록화에서 누락되는 경우(LG엔솔 '(당기) (단위: 백만원)'이 text 블록에서 빠짐) →
  `_extract_comp_unit_from_html` raw html fallback
- 검증: KOSPI 상위 120사 미환산 7건→1건(두산로보틱스는 공시에 단위 표기 자체가 없음 = 파서 한계)

### 2. 보수한도 파싱 실패 6유형 → 폴백 4종 (commit 0217f69)

255사 진단으로 실패 8%(21사)를 6유형 분류 → 폴백:
- **셀 오염 선행 숫자 추출** (SK스퀘어 `100※장기인센티브…`→100억, ok 복구)
- **한쪽 누락 유효값 살리기** (한미약품 당기 50억 + `parse_status=one_side_only` + warning)
- **외화/단위미상 플래그+raw** (코오롱티슈진 `USD`→`foreign_currency`, 두산로보틱스 단위없음)
- **parse_status 명시** (`no_agenda`/`one_side_only`/`foreign_currency`/`amount_unparsed`)
- summary에 `parse_status`·`direction_available`·`warnings` 추가 → shareholder_meeting payload로 노출
- regression(255사): ok 234→235, 회귀 0, 속도 6.8→6.5분

### 3. agenda 카테고리 100% None → 분류 추가 (commit 686b148)

255사 안건 1501개 진단: **제목/번호/검출은 99.9% 견고**(빈제목 1·검출실패 1=ETF)하나
**카테고리 100% None**. proxy_advise의 300사 검증 분류기 `_classify_agenda`를 agenda
scope(`_agenda_nodes`)에 적용(순환 import 회피 지역 import) + 영문 `category` + 한글 `category_label`.
- regression(255사): category None 1501→0, 제목/검출/번호/안건수 전부 회귀 0, 속도 6.3→6.2분

## 진단 도구 (재사용 템플릿)

- `scripts/compensation_parse_diagnosis.py` — 보수한도 실패 유형 분류 + raw 수집
- `scripts/agenda_parse_diagnosis.py` — 안건 검출/제목/카테고리/종류 분포
- `scripts/top50_compensation_audit.py` — 보수한도 상향/하향 + 단위 미환산 검출 (UNIVERSE_FILE 파라미터화)
- universe: 네이버 시총순 curl (`/tmp/kospi_kosdaq_300.json` 재생성 — page1-4 KOSPI + page1-2 KOSDAQ, ETF·우선주 제외)
- audit 결과: `wiki/architecture/audits/data/260615_*.json` (before/after 쌍으로 regression 측정)

## 안건 종류 분포 (255사 1501안건)

선임 516(34%) · 보수한도 315(21%) · 재무제표 250(17%) · 정관변경 246(16%) · 자기주식 63 ·
퇴직금 26 · 자본감액 4 · 배당 2

## 남은 작업 / 진행 상황 (2026-06-15 갱신 — 병렬 세션 반영)

안건 **검출/제목/카테고리(공통)** + **보수한도 세부**는 완료. 종류별 세부 파싱은 **병렬 세션에서
상당 부분 진행됨**(pull 후 확인). 현 상황:

1. **선임 (516건, 34%)** — board scope / director_evaluation (후보 경력·결격·독립성).
   ✅ **255사 후보 1171명 전수 완료** (`director_eval_diagnosis.py`, commit 680cceb). 이름/결격
   (clean 1170·red_flag 1)/독립성 3축(최대주주·3년거래·5년룰 100% success)/선임유형 견고.
   recent_2y_employee만 98% soft-fail(경력이 '재직/근무' 키워드 없는 직책 형식) → soft-fail 시
   경력 raw를 evidence로 노출(학력 제외·최근순). regression: 판정 분포 전부 동일(회귀 0),
   evidence 채움 0→1147/1147. **교훈: 진단 스크립트가 필드명 틀리면 멀쩡한 축을 "100% 실패"로
   오진한다(결격 unknown 100% → 실제 clean). 원본 구조 먼저 확인할 것.**
2. **재무제표 (250건, 17%)** — ✅ evidence 원문 rcept 부착 + CFS→OFS 폴백 경고 + 순이익 QoQ
   alert 진행됨 → [[financial-metrics-evidence-fsdiv-260615]]
3. **정관변경 (246건, 16%)** — ✅ **KOSPI 485사 정관 전수 완료**(실패 1사·0.2%, audit
   `260615_aoi_kospi_census`). 기업은행(정관변경이 타 안건 detail에 흡수, commit e781989)·
   한국금융지주(소집공고 vs 소집결의 추적 정정, commit 1ff47a3) 개별 수정.
4. **안건 유형별 parse_status 확대** — ✅ **320사 전수 후 "불필요" 결정** →
   [[agenda-typed-status-audit-260615]]. 보수한도식 타입화 status를 선임·정관 등에 일괄 확대하지
   않음("빈손"이 아니라 "그럴듯하게 틀림"이 위험 — 종류별 맞춤 검증이 맞다).
5. **5% 합계표(지분 분쟁)** — ✅ 본인/공동보유 분리 파서 + 140사 전수 →
   [[holder-table-parser-260615]] (이번 주총 안건과 별개 축이나 같은 시기 진행).

→ **주요 안건 종류(보수한도·선임·재무제표·정관) 세부 파싱 점검 완료.** 남은 건 소수 종류
(자기주식·퇴직금·자본감액 등) — 빈도 낮고 의결권 영향 작아 우선순위 낮음. 필요 시 동일 방법론:
① 큰 샘플(코스피+코스닥 255사) 실패 유형 분류 → ② 폴백(셀오염 추출/유효값 살리기/플래그+raw/
parse_status/warning/경력 raw evidence) → ③ before/after regression(정확도·속도 회귀 0). 단,
parse_status 일괄 확대는 위 4번 결정대로 지양하고 종류 맞춤 지표로.

## Takeaway

- **파싱 점검은 "큰 샘플 진단 → 실패 유형 분류 → 폴백 → regression 측정" 사이클로.**
  ground truth 없이도 실패 유형(단위미환산/한쪽누락/외화/안건미검출)을 프록시 지표로 빈도화.
- **조용한 실패(None) 대신 명시적 플래그 + raw + warning.** "왜 없는지"를 parse_status로,
  유효한 한쪽은 살리고, 환산 불가(외화/단위없음)는 raw로 넘긴다.
- **검증된 로직은 공유.** agenda 카테고리는 proxy_advise의 300사 검증 분류기를 scope에 연결만 하면 됐다.
- **regression은 before/after 같은 샘플로 수치 비교.** 정확도(실패율) + 속도 둘 다 회귀 0 확인 후 진행.

## Related

- [[proxy-advise-perf-fact-260614]] (직전 — 성과 fact + treasury 동적 + regression 방법론)
- [[order-contracts-260613]] (수주 tool 전수조사 방법론)
