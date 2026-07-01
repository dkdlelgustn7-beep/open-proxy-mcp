---
type: lesson
title: 밸류에이션 tool lean v1 — 스펙 6인 검토 + 전수조사·2R 패널로 배포 전 함정 제거
context: 2026-07-01~02 밸류에이션 tool 신설. financial_metrics가 최다 사용(84명)이라 배수 수요 확인 → 공시(DART)+시세(KRX) 기반
date_learned: 2026-07-02
related: [financial-metrics-account-id-260630, hard-rate-limit, agenda-parser-validation-260621]
category: tool
---

# 밸류에이션 tool lean v1 — 검토 주도 개발

## Context

financial_metrics가 실사용 1위 tool → 밸류에이션 배수 수요 확인. DART(공시)+KRX(공식 시세)로 상대가치 배수를
만들되, OPM 철학(공시 기반·근거 투명·예측 남발 X)에 맞춰 설계. 밸류에이션은 본질이 **의견**이라, 코드보다
**"맞는 아이템을 맞는 방식으로"**가 핵심 — 그래서 구현 전 스펙을 전문가로 교차검토하고, 구현 후 전수조사+패널로 검증.

## Did

- **스펙 먼저**(`decisions/valuation-methodology`): 지표 × **시계열 기준(FY0/TTM/MRQ)** × 측정방식.
  flow(순이익·매출)=TTM(4분기 합), stock(자본·차입)=MRQ(최신 분기말 잔액), FWD(예측)=제외.
  6인 전문가(analyst·PM·IR·accountant·DART·KRX) 검토 + 자본잠식·**PIT(공시 접수일 기준)** 반영.
- **KRX Open API 실측**: `stk_bydd_trd`로 전 종목 시세·시총·상장주식수 하루 1콜. PER/PBR은 Open API에 없어
  DART(EPS/BPS)로 자체 계산. 시계열은 basDd 반복(2016+).
- **lean v1 구현**: PER(FY0+TTM)·PBR(MRQ)·배당수익률(alotMatter DPS) + 섹터게이팅·N/M·자본잠식 가드.
  RIM·EV/EBITDA·PSR·FCF는 "고치느니 드랍" → v1.1.
- **전수조사 + 4인 패널 2R loop**(Workflow): KOSPI200 200종목 + analyst·PM·CPA·IR 각 2라운드 적대검토.

## Improved

- **배포 전 함정 6건 제거**(단일 개발자면 놓쳤을 것): ① eps_ttm 분모를 유통 '합계'(보통+우선) 대신 **보통주**로
  (우선주 발행사 PER_TTM 과대·per_fy0와 불일치 교정) ② 결측 EPS(None)를 '적자'로 오표기 금지 ③ KRX 상장주식수로
  DART 유통주식수 파싱오류 sanity(LS에코 ×1e6 차단) ④ 우선주 총시총 접두매칭 오합산 → 보통주만 ⑤ price=None 크래시
  가드 ⑥ 극단배수 plausibility 경고(두산밥캣 단위 오독 방어).
- **전수 정합 확인**: 200종목 크래시 0, PER/PBR/BPS/배당 공식정합 100%(반올림 오탐 1건은 도구 보정으로 소거),
  적자 가드 **bijection**(per 산출수 = 흑자기업수). 섹터게이팅 22 금융사 오분류 0.
- **데이터 품질 버그 2건 발견**: 두산밥캣(acntAll 금액 ~1000× 과소·단위 오독)·LS에코(주식수 ×1e6) — 전수 없인
  안 드러났을 롱테일. 가드로 방어 + v1.1 근본원인 조사 등록.

## Trade-off

- **RIM 드랍**: 6인이 "ROE/CoE 장난감을 적정가로 포장"이라 강력 경고(삼성전자 적정가 −74%). 제대로 하려면
  역산(시장 내재 ROE)+민감도그리드+정상화ROE+섹터CoE = v2급 → v1에서 제외. **"깨지는 것 드랍, 안 깨지는 코어+맥락(밴드)"**.
- EV/EBITDA·PSR·FCF도 v1.1(금융사 무의미·D&A갭·캡티브 왜곡).
- v1.1 잔여: 지배자본 미파싱 5사·은행 sector 오분류·TTM 반기/3Q 롤링·OFS 폴백·MCP 등록·5년 밴드·PIT 시계열.

## Takeaway

- **의견성 tool은 코드 전에 스펙을, 스펙은 다관점으로.** "맞는 아이템(account_id)·맞는 시계열(flow=TTM/stock=MRQ)·
  맞는 분모(EPS=보통주·BPS=합계)"를 전문가 렌즈로 못 박아야 배수가 desk-credible.
- **전수조사가 롱테일을 잡는다.** 스팟체크로는 안 나오는 단위오독·주식수 파싱오류가 200종목에서 드러남.
  cf. `agenda-parser-validation-260621`(측정 함정·전수 프로토콜).
- **가드가 신뢰를 만든다.** 금융사→N/A, 적자·자본잠식→N/M+리스크경고, 극단배수→plausibility 경고. "버그처럼 보임"에서
  "데스크 신뢰"로 가는 두 레버 = 섹터 게이팅 + 비양수 분모 N/M.
- **KRX는 DART와 별도 채널** — 하루 1콜 전종목·rate-limit 무관. 다만 시총/EV의 우선주 합산·주식수 정합은 조심(교차 sanity).
- 스펙·구현·검증 상세: `decisions/valuation-methodology`.
