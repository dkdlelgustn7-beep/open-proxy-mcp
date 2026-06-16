---
type: lesson
title: render 출력 점검 — 데이터는 멀쩡한데 화면에서 이상하게 뜨는 것
context: 2026-06-15~16 "실제 툴 사용과 같은 방식으로 점검해서 이상하게 뜨는거 잡아줘"
date_learned: 2026-06-16
related: [shareholder-meeting-agenda-parse-260615, proxy-advise-perf-fact-260614]
---

# render 출력 점검 — 사용자가 보는 화면 기준으로 이상 잡기

## Context

서비스 데이터 구조(payload) 점검만으론 안 보이고 **tool render(사용자가 보는 markdown)에서만
드러나는 이상**을 잡자는 요청. 큰 샘플(255→410사)로 11개 tool render를 실제 호출 경로
(build_*_payload → render_*(payload))로 스캔.

## 발견한 이상 3종 (전부 데이터는 멀쩡, 화면만 이상)

1. **proxy_advise — Python dict 통째 노출** (commit 655577e)
   facts가 `candidate_review_profile`(dict)를 `str()`로 통째 출력 → 화면에 `{'candidate_name':
   '허은녕', ..., None, ...}` 객체가 박힘. None 노출 29·큰숫자 237이 전부 이 dict가 근본 원인.
   → dict/list 값은 raw 대신 `(상세 N항목 — 후보 평가 섹션 참조)`로 요약.
2. **order_contracts — 'None%' 노출** (commit 73b400f)
   `s.get('max_revenue_ratio_pct', '-')`의 함정 — **키가 있고 값이 None이면 default('-')가 안
   먹고 None 반환**(default는 키 부재 시만). 매출대비 없는 회사에서 '단일 최대 None%'.
   → `_pct()` 헬퍼로 요약·계약별·해지 3곳 None→'-'.
3. **proxy_advise — '외부 수주 0건 0억원' 군더더기** (commit df3b0ca)
   order_signal fact 조건이 `order_count`(외부+계열)라 계열 일감만 있는 회사(external 0)에서
   '외부 수주 0건 0억원' 노출. → `external_count` 기준 + parts 비면 line 생략.

## evidence 화면 노출 — "노이즈"라는 내 단정이 틀렸다 (commit 6688dd6)

선임 후보 독립성 evidence(2년 직원 경력 raw)를 payload에만 두고 화면엔 판정 결과만 노출했다.
처음엔 "전체 노출은 노이즈"라고 단정했으나 — **애널리스트가 의결권 판단 시 독립성 근거를
직접 검토하는 건 정당한 니즈**다. LLM은 payload를 읽으니 충분하지만, 사람이 메모를 검토할 땐
근거가 화면에 있어야 한다. 내 판단을 사용자에게 강요한 오류.

→ 후보별 detail에 독립성 4 sub_factor(최대주주관계·3년거래·2년직원·5년룰) 결과 + 근거를
**구조화 노출**(`_indep_evidence_lines`). 사외이사/감사위원 한정. 예:
`최근 2년 직원 이력: 외부인 — 근거: 2013~현재 GIC Managing Director`.
관건은 "노출 여부"가 아니라 "어떻게 구조화하느냐"였다.

## 아이콘 정책 — 경고는 ⚠️, 등급은 색상

독립성 우려·본업 적자·해지 등 **경고/주의** 표시는 ⚠️로 통일(commit 다음). 단 성과 분류
`cls_emoji`(🟢🟡🟠🔴 = 우수/양호/부진/저조)는 **4색 그라데이션 등급 체계**라 🔴 유지
(주의 아이콘이 아니라 색상 등급). 경고와 등급은 다른 의미.

## 진단 도구 (재사용)

- `scripts/render_anomaly_scan.py` — 11개 tool render md 이상 패턴 스캔(None/0억/dict노출/빈셀/
  깨진텍스트/카테고리None/비정상숫자). `_SKIP_LINE`으로 정상(rcept_no·소수점) 오탐 제외.
  UNIVERSE_FILE/LIMIT/PA_LIMIT/JOBS_LIMIT 파라미터화. XL 410사·11 tool·11582콜·52분 실증.

## raw 금액 환산 — 값만 있고 단위 환산이 없는 것 (commit 다음)

"레이블 없는 값" 점검(bullet 패턴)은 **0건**(render bullet에 레이블 다 붙어 있음). 단 부수로
**환산 안 된 raw 금액**을 발견 — treasury 금액(원) `7,174,299,854,900`(7조를 쉼표 숫자로),
dividend 배당총액 `11,107,906백만원`(11조). 헤더 레이블(`금액(원)`)은 있으나 조/억 환산이 없어
"이게 몇 조야?"가 한눈에 안 보였다.

→ 공용 `_won` 정책을 4개 tool(treasury·dividend·order_contracts·proxy_advise)에 통일.
**환산은 절삭(`7.1742…조`→`7.17조`)이라 정밀이 깎이므로 raw를 괄호로 병기**:
`7,174,299,854,900` → `7.17조원 (7,174,299,854,900원)`. 환산=가독, raw=정밀 둘 다 화면에.
1억 미만은 절삭이 없어 raw만. treasury 헤더 `금액(원)`→`금액`.
**단 주식수(`1,174,366,888`)·단가(`162,400원`)는 환산/병기 X** — 주식수는 지분%가 핵심이라
raw가 맞고, 단가는 작아 환산 무의미. 금액 컬럼만 정확히 골라 처리(주식수까지 건드리면 오히려 틀림).
(처음엔 환산으로 raw를 '대체'했으나 사용자 지적 — 환산 절삭으로 정밀 손실 → 병기로 정정.)

## Takeaway

- **데이터 점검 ≠ 화면 점검.** payload는 정상인데 render에서 dict 노출·None%·군더더기가 뜬다.
  실제 사용자 출력(render md)을 봐야 잡힌다.
- **`.get(key, default)`는 None 값에서 default를 안 쓴다.** 키가 있고 값이 None이면 None 반환.
  화면 None 노출의 단골 원인 — `_pct()`/`or '-'`/`is not None` 명시 필요.
- **"노이즈"라는 단정으로 사용자 니즈를 막지 말 것.** evidence 화면 노출은 애널리스트의
  정당한 검토 니즈였다. 관건은 노출 여부가 아니라 구조화.
- **scanner 오탐은 정상 케이스 제외로 정제.** rcept_no(14자리)·소수점(.0억)을 단위미환산으로
  오탐하던 것을 `_SKIP_LINE`/패턴으로 걸러 진짜 이상만 남긴다.

## Related

- [[shareholder-meeting-agenda-parse-260615]] (보수한도·선임 파싱 점검 — 같은 시기, 데이터 레벨)
- [[proxy-advise-perf-fact-260614]] (proxy_advise 성과 fact 구조)
