---
type: lesson
title: financial_metrics 순이익·ROE 오염 — account_nm 충돌/편차를 account_id로 해소
context: 2026-06-30 FnGuide 대조에서 서진시스템 순이익·ROE가 틀림 — tool이 총포괄손익 귀속을 순이익으로 집고 있었음
date_learned: 2026-06-30
related: [financial-metrics-precision-260612, financial-metrics-evidence-fsdiv-260615, agenda-parser-validation-260621]
---

# financial_metrics 순이익·ROE 오염 — account_id로 정확한 아이템 잡기

## Context

사용자가 FnGuide(Company Guide)와 대조: 서진시스템(178320) 순이익·ROE가 tool과 불일치.
3년 6개 값이 전부 어긋났는데 매출·영업이익·부채비율은 정확 → "순이익 계열만" 오염.
감사보고서 포괄손익계산서와 숫자를 맞춰보니 tool이 **당기순이익 귀속(지배)**이 아니라
바로 아래 **총포괄손익 귀속(지배)** 행을 집고 있었다. (서진 2025: -1,012억 대신 -1,273억)

## Did

- **근본원인**: `fnlttSinglAcntAll` CIS에는 `당기순이익 귀속(지배)`과 `총포괄손익 귀속(지배)`이
  **account_nm이 동일**("지배기업 소유주지분")한 두 행으로 들어온다. account_nm substring +
  첫매칭이라, 응답 순서상 먼저 오는 **ComprehensiveIncome 귀속**을 잡아 순이익·ROE를 오염.
- **수정**: 귀속 항목을 **account_id로 매칭** — 순이익=`ifrs-full_ProfitLossAttributableToOwnersOfParent`,
  지배자본=`ifrs-full_EquityAttributableToOwnersOfParent`. account_nm은 fallback로만.
- **공식 교정(동반 발견)**: ROE 분모가 전체자본 평균이었음 → **지배자본 평균**으로
  (FnGuide 정의 = 지배순이익/평균 지배자본). ROA 분자는 **전체순이익**(총자산 대응)으로 분리.
- **검증**: 서진 3년 + 대형·지주(고비지배)·금융·적자 28사를 raw DART(account_id) ground truth와
  전수 대조 → 순이익·ROE 정확 일치. 39사 large-sample로 구조적 근거 확보(아래).

## Improved

- 순이익·ROE가 기타포괄손익(환산·평가)만큼 오염되던 것을 제거. 특히 **흑/적 부호·배수**가 틀리던
  것(서진 2024 +1,420억 → 정정 +843억)을 바로잡음.
- **large-sample 정량근거**: 귀속행 보유 39사 중 **21사(54%)**가 순이익귀속 nm == 총포괄귀속 nm
  (= account_nm 단독이면 절반이 오매칭). 같은 항목 account_nm은 지배순이익 **13종**·지배자본 **14종**
  으로 갈리지만 account_id는 1종으로 통일. 이 표준 귀속항목은 All 엔드포인트에서 account_id가
  **항상 존재**(0/39 결측) → id 매칭이 안전·충분.
- **전수 + 이중 검증(260701)**: KOSPI200(시총상위 200사) 전수 — 평가가능 192사 전부 raw account_id
  ground truth와 일치(불일치 0). 독립 소스(FnGuide계열 리서치터미널 export) 191사 대조 = 흑/적 부호
  100%·크기 99%(TTM≠FY 감안). 라이브 FnGuide 정밀 3종(OCI 갭 극단 삼성생명·부호뒤집힘 삼성SDI·
  비지배 74% HD현대) 전부 일치 — 가장 틀리기 쉬운 종목에서 검증. 삼성생명: 옛 버그값 총포괄지배
  274,348억(12배) 대신 지배순익 23,028억으로 정정 확인.

## Trade-off

- account_id는 **`fnlttSinglAcntAll`에만** 존재(주요계정 `fnlttSinglAcnt`는 0/30 결측).
  따라서 매출·영업이익·자본총계 등 주요계정 출처 항목은 여전히 account_nm 의존 — 다만 라벨이
  단순·저충돌이라 허용. **위험한 귀속 항목만 id로** 잡는 하이브리드가 현실적 최적.
- 외부 교차검증으로 FnGuide 스크래핑을 검토했으나 robots.txt `Disallow: /` + 저작권/DB화 금지 +
  유료 라이선스(DataGuide·fnspace) 충돌 → **상용 제품엔 부적합**. DART OpenAPI 유지가 정답.

## Takeaway

- **정확한 아이템을 잡아라 — 라벨(account_nm)이 아니라 표준코드(account_id)로.** 한국 IFRS 공시는
  같은 한글 라벨이 (순이익 귀속 vs 총포괄 귀속)처럼 다른 항목에 재사용되고, 같은 항목도 회사마다
  표기가 갈린다. substring+첫매칭은 둘 다에 취약.
- **숫자가 나와도 공식을 의심하라.** 아이템을 고쳐도 ROE 분모(지배 vs 전체 자본)가 틀리면 여전히
  어긋난다. ground truth(FnGuide 툴팁 정의)로 분자·분모를 둘 다 확인.
- **검증은 큰 표본 × 이중**: 단건(서진) 교정 후 28사 전수 대조 + 39사 구조분석으로 일반성 확인.
  cf. [[agenda-parser-validation-260621]] 측정 함정·체크리스트.
