---
type: decision
title: 밸류에이션 tool 방법론 스펙 (지표 × 시계열 기준 × 측정방식)
date: 2026-07-01
status: spec-confirmed (v1 배선 대기)
---

# 밸류에이션 방법론 스펙

DART(공시) 재무 + KRX(공식 시세)로 상대가치 배수 + RIM(잔여이익) 앵커를 산출한다.
철학: **공시 기반·근거 투명·예측 남발 X**. "적정가 X원" 블랙박스가 아니라 배수·인풋·가정을
모두 노출하고 사용자가 "밸류 위치"를 판단하게 한다(value_up tool과 결 동일).

## 1. 시계열 기준 3종

| 기준 | 뜻 | 적용 대상 | 데이터 |
|---|---|---|---|
| **FY0** | 최근 **사업연도**(연간 확정) | 모든 지표 | DART 사업보고서(11011) |
| **TTM** | 최근 **4개 분기 합** = 직전FY + 당기누적 − 전년동기누적 | **flow만** (순이익·매출·EBITDA·FCF·영업이익) | DART 분기보고서 |
| **MRQ** | 최근 **분기말 잔액**(합산 X, 최신 스냅샷) | **stock만** (자본·차입·현금) | DART 최근 분기 |

- **flow(합산)** vs **stock(잔액)** 구분이 시계열 기준을 가른다.
  - flow = 기간 누적 → TTM 성립. stock = 시점 잔고 → **TTM 불성립, MRQ(최신 잔액) 사용**.
  - 예: 자본은 stock. FY25(2025-12-31 잔액)와 1Q26(2026-03-31 잔액)은 그 사이
    `순이익 유보 − 배당 ± 기타포괄손익 ± 자본거래`만큼 다름. **최신인 1Q26 = MRQ**.
- **PBR "TTM"은 성립 안 함** → PBR은 FY0(연말자본) 또는 **MRQ(최근분기말 자본)**.
- **FWD(예측)** = 컨센 데이터 없음 → **제외**(원하면 "가정 입력형"으로 별도).

## 2. 지표 정의 (분자/분모 × 기준 × 소스)

| 지표 | 기준 | 분자 | 분모 | 분자 소스 | 분모 소스 |
|---|---|---|---|---|---|
| **PER** | FY0 · TTM | 현재가 | EPS(지배) | KRX 가격 | DART(지배순이익; TTM=4Q합)÷유통주식수 |
| **PBR** | FY0 · MRQ | 현재가 | BPS = 지배자본/유통주식수 | KRX | DART(지배자본)·KRX/DART(주식수) |
| **PSR** | FY0 · TTM | 시총 | 매출 | KRX(MKTCAP) | DART |
| **EV/EBITDA** | FY0 · TTM | EV = 시총 + 순차입(MRQ) | EBITDA = 영업이익+D&A | KRX+DART | DART(CF의 D&A) |
| **EV/EBIT**(옵션) | FY0 · TTM | EV | 영업이익 | KRX+DART | DART |
| **배당수익률** | FY0 | DPS | 현재가 | DART(배당) | KRX |
| **FCF수익률** | FY0 · TTM | FCF | 시총 | DART | KRX |
| **PCR**(옵션) | FY0 · TTM | 시총 | 영업현금흐름(CFO) | KRX | DART |
| **RIM 적정PBR/적정가** | ROE(FY0·TTM), BPS(MRQ) | (ROE−g)/(CoE−g) → ×BPS | — | DART+가정 | — |
| **NAV/시총**(지주 옵션) | MRQ | 순자산(지배자본) | 시총 | DART | KRX |

## 3. 측정 방식 — 공통 규칙 (맞는 아이템·맞는 방식)

- **가격·시가총액·상장주식수 = KRX Open API 공식** (`sto/stk_bydd_trd` MKTCAP·LIST_SHRS).
  우선주 존재 시: 시총/EV는 보통주 기준 + 우선주 별도 합산(경고 부착). PER·PBR·배당수익률은 정상.
- **순이익·EPS = 지배주주 귀속**(account_id `ProfitLossAttributableToOwnersOfParent`; nm substring 금지).
  TTM = FY + 당기누적 − 전년동기누적(4분기 합).
- **자본·BPS = 지배자본 ÷ 유통주식수**(자기주식 제외). 지배자본 = `EquityAttributableToOwnersOfParent`.
  FnGuide 규약 일치 검증됨(삼성전자 424조/6.63억주 = **BPS 63,997**).
- **순차입금 = 총차입(단기+장기) − 현금성자산** (MRQ 잔액).
- **EV = 시총 + 순차입금**.
- **EBITDA = 영업이익 + 감가상각비(D&A)** — D&A는 CF에서 추출. **추출 실패 회사는 N/A**(알려진 한계 →
  EV/EBITDA는 v1.1로, D&A 보강 후).
- **DPS = 현금배당총액 ÷ 유통주식수** (또는 배당 tool 현금DPS).
- **RIM 적정PBR = (ROE − g)/(CoE − g)**, 적정가 = 적정PBR × BPS(MRQ). CoE(요구수익률)·g(영구성장)는
  **투명 가정**(기본 CoE 9%, g 0%; 조정 가능). RIM은 보수적 앵커(고PBR·프랜차이즈 가치 미반영) — 단정 X.

## 4. 밴드(시계열) 측정 방식

"지금 밸류가 역사/동종 대비 어디"를 위한 자기 밴드:
- **각 시점 배수 = 그 시점 KRX 종가 ÷ 그 시점 DART 재무** → min·25%·중앙·75%·max + **현재 백분위**.
- **연간 밴드(v1)**: 최근 5개 **연말(결산일) 종가**(KRX 5콜=전종목) × 연도별 EPS/BPS → PER/PBR 5년 밴드.
- **분기 밴드(v1.1)**: 최근 20개 분기말 × TTM/MRQ 재무(KRX 20콜).
- **rolling 일별(v2)**: 일별 종가 × as-of TTM (가장 정밀, 용량↑).
- **peer 밴드(v1.1)**: 동종업종(WI26/KRX 섹터) 배수 중앙값 대비.

## 5. 데이터 소스·용량·rate limit

- **KRX Open API**(`data-dbg.krx.co.kr/svc/apis`, AUTH_KEY) — 하루 1콜에 전 종목 시세/시총/상장주식수.
  DART 분당한도(1,000)와 무관 → 서비스 IP 차단 리스크 없음. 정제 저장 시 전종목 10년 ~500MB, 코스피200 수십MB.
  ※ Open API엔 PER/PBR/배당수익률 **없음**(우리가 DART로 자체 계산). 투자자별·공매도·지수구성 미포함.
- **DART API** — 재무(사업/분기보고서), 배당. 종목당 다수 콜 → 배치 시 rate limit 준수(`hard-rate-limit` lesson).

## 6. v1 / v1.1 / v2 스코프

| | 포함 | 기준 |
|---|---|---|
| **v1** | PER·PBR·PSR·배당수익률·FCF수익률·**RIM** + 자기 5년 연말 PER/PBR 밴드 | PER/PSR/FCF=FY0+TTM, PBR=FY0+MRQ |
| **v1.1** | EV/EBITDA(D&A 보강), peer 중앙값, 분기 밴드 | TTM/MRQ |
| **v2** | rolling 일별 밴드, 가정입력형 DCF(FWD) | — |

## 7. 검증 (이 스펙 확정 전제)

- 10개사 실측(FY0/TTM/MRQ 배수 산출) + **6개 전문가 관점 검토**(financial analyst·fund manager·
  IR·accountant·DART expert·KRX expert)로 "맞는 아이템을 맞는 방식으로" 계산했는지 교차검토(260701).
- 관련(lessons): `financial-metrics-account-id-260630`(순이익·EPS·BPS 정합성) · `hard-rate-limit`(DART 한도).

## 8. 전문가 패널 검토 반영 (260701, 6인) — 스펙 개정

### CONFIRM (골격 유지)
지배귀속 순이익·자본(account_id) / TTM(flow)·MRQ(stock)·FY0 규율 / BPS=지배자본÷유통합계(자기주식 제외,
FnGuide 일치·DART 실측 검증) / 유통(per-share) vs 상장(시총) 분리(KRX·FnGuide 표준) / CF기반 D&A·추출실패시
EBITDA=None / 금융사 매출 None 정당처리 / KRX ISU_CD 단축코드 조인·Open API엔 PER/PBR 없어 자체계산.

### FIX (확정 수정 — 우선순위)
- **P0 섹터 게이팅**: 금융사(은행·보험)는 EV/EBITDA·PSR·EV·순차입·FCF = **N/A 강제**(category error). 은행=PBR·ROE·PER·배당,
  보험=P/EV·PBR(자본 OCI 변동성 caveat). 지주(삼성물산)=NAV/SOTP flag. 캡티브금융 자동차(현대차·기아)=산업부문 분리 or EV계열 억제.
- **P0 N/M 가드 + 자본잠식·적자 처리**: 분모(EPS·EBITDA·FCF·ROE·**BPS**)≤0이면 부호 숫자 대신 **N/M**
  (적자 PER "싸 보임"·자본잠식 PBR 헛값 오도 방지). **자본잠식**은 `financial_metrics.capital_impairment_status`
  (normal/partial/partial_50plus/full)를 소비 → `full`(완전잠식, 자본≤0)=PER·PBR **N/M + 상장폐지 위험 경고**,
  `partial_50plus`=**관리종목 위험 경고**, `partial`=자본잠식 진행 플래그. 밸류 배수보다 **리스크가 헤드라인**
  ("PBR 0.3배 싸다" ❌ → "자본잠식=상폐/관리종목 위험" ✅). risk_events와 연계 권장.
- **P0 RIM 재프레이밍**: "적정가/적정PBR" 라벨 폐기 → "현 ROE 기준 justified PBR(가정 노출)". ① **역산=시장 내재 ROE 제시**(현PBR×CoE)
  ② CoE 8~11%×g 0~3% **민감도 그리드**(점 아님) ③ **정상화(3~5yr) ROE·섹터별 CoE** ④ ROE≤0·ROE≤g면 suppress.
- **P0 DPS 출처 교체(가장 임팩트)**: CF '배당금의 지급'(dividend_paid_krw) **금지** — 현금주의·비지배 배당 포함·클래스 혼합.
  → **alotMatter 보통주 주당현금배당금**(`dividend`/`div_*`의 cash_dps) 사용. 배당수익률=보통주 DPS÷보통주가.
- **P1 TTM/MRQ 실배선**: 현 서비스는 **FY0 연간만** 계산(TTM/MRQ 미구현). TTM=지배순이익, 반기/3Q는 thstrm_add(누적) 차분으로 **롤링**,
  MRQ=11013 잔액. **013(미공시)→FY 폴백**, CFS→OFS 폴백. TTM EPS 분모=유통 **보통주**(합계 아님).
- **P1 총시총·EV**: 우선주 총시총 = **KRX MKTCAP를 발행사 상장 row별 합산**(추가콜 0). EV = 총시총 + **비지배지분 + 우선주** + 순차입.
  순차입 현금에 **단기금융상품 포함**(cash-rich 순차입 과대 교정). EBITDA D&A 추출 보강(삼성전자 N/A는 데이터결함).
- **P2 인프라**: KRX **전용 throttle**(DART 900/분 공유 금지). docstring 수정(가격 소스 순서·EPS 보통주 기준). 매출 nm 폴백(영업수익) for 지주.

### ADD (v1.1 승격 후보 — 절대배수는 맥락 없이 무의미)
- **peer 상대순위**(섹터 중앙·백분위) — #1 결손. **자기 5년 밴드/백분위** — 최고 ROI, DART+KRX로 가능.
- **품질 블록**(ROE 수준·추세·ROIC·순차입/EBITDA·커버리지). **EV/EBIT·EV/Sales**(적자 스크린). **유동성 게이트**(ADTV·유동주식).
- **cyclical flag + "trailing-only" 각인**(반도체·화학·자동차 trailing 함정). FCF 정의 명시(CFO−capex; FCFF면 분모 EV).

### v1 스코프 개정 — 린(lean) 확정 (260701)
"깨지는 것 드랍, 안 깨지는 코어 + 맥락(밴드)". **v1 = 3배수 + 밴드 + 가드:**
- **PER** — TTM(헤드라인) + FY0(참조). (flow → 둘 다)
- **PBR** — **MRQ만**(미공시 시 FY0 폴백). (stock → 최신 하나. FY0/MRQ 차이 작음)
- **배당수익률** — FY0, **alotMatter 보통주 결의 DPS**(CF 배당지급 금지).
- **자기 5년 PER/PBR 밴드 + 현재 백분위** — 절대배수를 "역사 대비 어디"로 해석가능하게(밴드=연말 기준, 현재=MRQ 별도).
- **가드** — 섹터 N/A(금융사 EV/EBITDA·PSR·EV·FCF·순차입 차단) · **N/M(분모≤0)** · **자본잠식→N/M+상폐/관리종목 위험 경고**.

**v1에서 드랍(→ v1.1)**: RIM(적정가 오해 소지 최대; 남긴다면 "시장 내재 ROE" 주석만)·EV/EBITDA(D&A 갭)·PSR(신호 약·금융 난센스)·FCF수익률(캡티브·capex 노이즈).
**v1.1**: peer 상대순위·품질블록·유동성 게이트·EV/EBIT·분기 밴드 + 위 드랍분(정상화·섹터게이팅 후).
