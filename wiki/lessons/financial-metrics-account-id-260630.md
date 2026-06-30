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

## 엔드포인트 선택 원칙 (260701 후속 — 가장 중요한 일반화)

DART 재무 API는 두 종류이고, **항목마다 "어느 엔드포인트에 사느냐"가 다르다**:

| | 주요계정 `fnlttSinglAcnt` | 전체 `fnlttSinglAcntAll` |
|---|---|---|
| 행 수 | ~14종(요약 총계) | 수백 |
| account_id | **없음**(0/30) | 있음(355/355) |
| 라벨 충돌 | 거의 없음(깔끔) | 잦음(귀속·자본과부채총계 등) |
| 성격 | **안전** | account_id로 잡아야 안전 |

**주요계정에 있는 14개(= 안전한 동네, nm으로 충분):**
- BS(9): 유동자산·비유동자산·자산총계 / 유동부채·비유동부채·부채총계 / 자본금·이익잉여금·자본총계
- IS(5): 매출액·영업이익·법인세차감전순이익·당기순이익(손실, **총계**)·총포괄손익

**주요계정에 없어 전체에서만 오는 것(= 주의 동네):** 지배/비지배 귀속 순이익·지배자본·매출원가·매출총이익·
이자비용·EPS·매출채권/재고/매입채무·차입금·현금흐름표 전부·OCI 세부.

**원칙**: *주요계정에 있는 총계는 주요계정에서 읽고(nm으로 안전), 거기 없는 분리·세부 항목만 전체에서
읽되 모호하면 account_id로 못박는다.* 코드 감사 확인(260701): financial_metrics는 10개 총계를 bs_is
(주요계정)에서, 귀속/세부를 detail(전체)에서 읽어 **원칙 준수**.

**두 실패 모드(이번 세션 실증):**
1. ROE 오류 = **지배순이익이 주요계정에 없어 전체로 갔는데** 거기 nm이 충돌(당기순이익귀속==총포괄손익귀속)
   → account_id로 해결. (위 본문)
2. 하드닝 회귀 = **이미 주요계정에 안전히 있던 부채총계를 굳이 전체로 옮김** → 전체에만 있는
   `자본과부채총계`가 "부채총계"에 부분일치 → 부채비율 +100%p 오염. 20사 before/after가 적발 →
   **철회**. 교훈: "account_id 있으니 전체가 낫다"는 **거짓** — 안전한 동네 항목을 충돌 동네로 끌고 가지 말 것.
   (삼성전자 부채비율 FnGuide 25.36% == 주요계정 산출 25.36%, 회귀값 125.36%는 오답.)
3. **EPS도 같은 클래스(260701 후속 점검에서 발견)** = 주당이익은 주요계정에 없어 전체에서 오는데, nm
   "기본주당이익"이 **"1우선주기본주당이익"에 부분일치 + 우선주 행이 먼저** 와서 보통주 대신 **우선주
   EPS**를 집음(현대차 37851 vs 보통주 36088). → account_id로 교정: `ifrs-full_BasicEarningsLossPerShare`
   (보통주 total) 우선, total 행 없으면(분리공시 회사) `...FromContinuingOperations` fallback. 단, **id-only로
   바꾸자 total 없는 회사(한화에어로·효성중공업)가 None으로 떨어지는 회귀** 발생 → 계속영업 fallback으로 해결.
   30사 검증: 교정 7 / 정상유지 23 / 회귀 0, 부수효과 0(eps 필드만 변경). **첫 수정의 회귀를 before/after가 또 적발.**

## Takeaway

- **정확한 아이템을 잡아라 — 라벨(account_nm)이 아니라 표준코드(account_id)로.** 한국 IFRS 공시는
  같은 한글 라벨이 (순이익 귀속 vs 총포괄 귀속)처럼 다른 항목에 재사용되고, 같은 항목도 회사마다
  표기가 갈린다. substring+첫매칭은 둘 다에 취약.
- **숫자가 나와도 공식을 의심하라.** 아이템을 고쳐도 ROE 분모(지배 vs 전체 자본)가 틀리면 여전히
  어긋난다. ground truth(FnGuide 툴팁 정의)로 분자·분모를 둘 다 확인.
- **검증은 큰 표본 × 이중**: 단건(서진) 교정 후 28사 전수 대조 + 39사 구조분석으로 일반성 확인.
  cf. [[agenda-parser-validation-260621]] 측정 함정·체크리스트.
