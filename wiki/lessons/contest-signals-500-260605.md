---
type: lesson
title: proxy_contest 분쟁 신호 500사 전수조사 — 패턴 + noise 통찰
date: 2026-06-05
related:
  - wiki/tools/proxy_contest.md
related_audits: [architecture/audits/data/260605_contest_signals_audit]
---

# proxy_contest 분쟁 신호 500사 전수조사 회고

## 배경

proxy_contest에 5% 보유 시계열(목적전환/추가매입/보고빈도) + 소송 dedup + 급변 강조를 추가한 뒤, KOSPI 200 + KOSDAQ 300 (중복 제거 500사) 전수조사로 신호 분포와 noise를 측정했다.

## 실행

- universe: kospi200 + kosdaq300 (dedup 500사)
- scope: summary / year 2025
- concurrency 3 + batch 30 sleep 2s
- 회사당 ~8-12 DART 호출 → ~4000 호출. rate limiter(cap 900 rolling 60s)로 차단 0.
- 결과: 383 exact / 116 no_filing(분쟁 공시 없음=정상) / 1 no_match

## 신호 분포

| 신호 | 회사 수 | 비율 |
|---|---:|---:|
| has_contest_signal (진짜 분쟁) | 54 | 14.1% |
| 5% 급변보유 ≥1 | 102 | 27% |
| 소송 원본 ≥1 | 21 | |
| 주주측 위임장 ≥1 | 6 | |
| 목적전환 ≥1 | 2 | |

### 신호 조합
```
신호없음        194 (51%)   ← 절반은 깨끗
외부5% 단독      67          ← 대부분 overlap noise
급변 단독        60          ← 대부분 차익실현 exit
외부5%+급변      36
소송            15
위임            6           ← 가장 드묾 = 강한 신호
위임+소송+급변    1 (고려아연 풀세트)
```

## 핵심 발견 — noise 구조

### 1. active 5% 블록 절대다수가 "대주주 본인 신고"
```
external (외부 세력)  32건  ← 진짜 행동주의
overlap (명부 겹침)   92건  ← 대주주 본인 경영참여 신고 = 분쟁 아님
관찰포인트 "명부 겹침"  256건 (압도적)
```
→ `active_signal_count`가 둘을 합산해 분쟁 과대표현. **external만 진짜 신호.**
→ 조치: md 출력에서 외부세력/대주주 본인 분리 표기 (commit 1bc149e). 구분 로직(registry_overlap)은 _build_control_map에 이미 존재.

### 2. 반복 보고자 = noise 필터 (전수에서만 보임)
```
TheCapitalGroup  4개사   ┐ 한 주체가 여러 회사 급변
국민연금          4개사   │ = 펀드 운용/포트폴리오 조정
미래에셋          3개사   │ = 분쟁 아님
피델리티/Miri     2개사   ┘
```
→ 한 주체가 N개 회사에서 급변 = 펀드 운용. 단일 호출로는 모르고 batch에서만 식별 가능 → tool 미반영, audit 통찰로만 보존.

### 3. 급변(±5%p)은 exit가 매집의 3.6배
```
매집(증가) 31건 / exit(감소) 113건
```
→ exit 대부분 블록딜/창업자 매각/계열 재편/외국기관 차익실현 (SK스퀘어 Macquarie, 하이브 방시혁, 한화오션 한화에어로 등). **급변은 정보로만, 분쟁 판정 X** (사용자 명시).

### 4. 한국 지배구조 특성
- 특관 합계 ≥30%: 240사 (63%) — 구조적으로 분쟁 어려움
- 자사주 ≥5%: 75사 (방어 수단)

## 진짜 분쟁 회사 (위임 OR 소송, 26사)

| 유형 | 회사 |
|---|---|
| 위임장 표대결 | 고려아연(위3 소34), 오스코텍(5), 코웨이(3), 가비아(3), DB하이텍(2) |
| 소송전 | 위메이드(4), 인벤티지랩(4), 하나마이크론(3), 디아이티(3), 차바이오텍(2) |

목적전환 2사 (필옵틱스 / 가비아) — 500 확장으로 처음 포착. 가비아는 위임장+전환 동시 = 행동주의 진입.

## 핵심 교훈

### 1. "여러 신호 나열 + 자동 단일 판정 X"가 옳다 — 500사로 실증
한 신호가 모든 분쟁을 잡지 않는다:
- 적대적 M&A → accumulation (고려아연/한앤코)
- 행동주의 → 소송 + 위임장 (KT&G/DB하이텍)
- 쟁탈전 → 위임장 (SM)
급변을 분쟁으로 자동 판정했으면 87건 exit false positive.

### 2. noise는 "구분"으로 줄인다 (필터 아님)
external/overlap, 매집/exit, 반복/단발 — 갈라서 보여주면 애널리스트/LLM이 noise를 거른다. 자동 제거가 아니라 정보 분리.

### 3. 진짜 분쟁 지표 = has_contest_signal (14.1%)
위임장 주주측 OR 소송 OR 외부5% active. 단독 급변/overlap은 제외.

## tool 반영 (commit)

- 5% 시계열 동학 (c187e90)
- 소송 dedup (a33072b)
- 급변 강조 (be72c98)
- external/overlap 분리 표기 (1bc149e)

## 미반영 (batch 전용 통찰)

- 반복 보고자 필터 — 단일 호출 불가, audit 통찰로만 보존

## archive

- `wiki/architecture/audits/data/260605_contest_signals_audit/audit_kospi200_kosdaq100.json` (300사)
- `wiki/architecture/audits/data/260605_contest_signals_audit/audit_kospi200_kosdaq300.json` (500사)
- `scripts/spot_contest_signals_audit.py`
