---
type: lesson
title: 5% 대량보유보고서 합계표 파서 — 분쟁 유니버스 140사 전수 검증
date: 2026-06-15
tags: [proxy_contest, ownership_structure, parser, audit]
related:
  - lessons/dispute-reverse-lookup-260607
  - 260615_holder_table_census
---

# 5% 합계표 파서 + 전수 검증 (proxy_contest 공동보유 재분류용)

## 배경

proxy_contest의 5% signal `ownership_pct`는 대량보유보고서 헤드라인 보유비율(=보고자 본인+
특별관계자 **합산**)을 그대로 표기한다. 솔루엠 사례에서 얼라인 "23.11%"가 실제로는
얼라인 본인 5.33% + 전성호(최대주주) 15.07% 등 **공동보유 합산**임이 드러났다. 즉:
- 합산값을 단독 지분처럼 오독
- 외부 펀드가 합의로 최대주주와 공동보유가 됐는데 `external_active_block`(외부)으로 오분류

이를 고치려면(본인/합산 분리 + 공동보유 탐지) **보고서 본문 합계표**를 파싱해야 한다.
이 lesson은 그 파서를 만들고 분쟁 유니버스로 성능을 검증한 기록이다.

## 합계표 구조 (Phase 1: 12사 probe로 확정)

```
주수 비율 보고자 [이름] [ID] …숫자… [합계주수] [비율]
특별관계자 [이름] [ID] … [주수] [비율] … ※ 소유에 준하는 보유…
```
- 11/12사 동일 구조. ID = 생년월일 6자리 | 사업자번호(하이픈) | 법인·고유번호(하이픈 없는 5~13자리).
- 검증 케이스: 한미사이언스 보고자 송영숙 3.84% < 특관 신동국 22.88%(공동보유), 고려아연
  보고자 영풍 0.00%(10주) + 특관 합산만 큼, 한진칼 특관에 한국산업은행 10.58%.

## Phase 2: 파서 성능 (분쟁 유니버스 140사 전수)

`scripts/holder_table_census.py`. 불변식 = (보고자 + 특관 비율 합) ≈ 헤드라인 보유비율.

| 항목 | 값 |
|---|---|
| 파싱 ok | 120 |
| no_table(약식·기관 단순투자 — 합계표 없음, 예상) | 7 |
| fail | 2 (스타코링크·네오리진) |
| **불변식 통과** | **111/118 (94.1%)** |

튜닝 과정에서 잡은 것:
- pct를 합계주수(group4, 콤마 포함)로 오추출 → 비율(group5)로 교정.
- **ID 형식 다양성**: 6자리·하이픈 사업자번호 외에 5자리(이탄에쿼티 53541)·하이픈 없는
  10자리(백운조합 6758003138)도 있어 보고자 행이 통째 누락 → `\d{5,13}` 포함으로 확장.

잔존 실패(~6%) 유형:
- **영문명 보고자**(파라택시스코리아 Parataxis Korea, 디와이디 OULANGE TRADE) — 이름/ID
  경계 깨짐. 외국계 펀드 niche.
- 보고자 행 누락(씨씨에스 0.0) / 과다(산돌 +10%p, 정정 중복 의심) / 다수 특관(대호에이엘 101명).

## 판정

- **합계표 데이터는 일관 구조로 존재하고, 표준 한국 보고서는 94% 정합 파싱된다** →
  proxy_contest 공동보유 재분류(B안)는 **기술적으로 feasible**.
- 단 **enrichment + graceful fallback**으로 설계해야 한다: 합계표 없음(약식)·파싱 실패(영문명)
  시 재분류하지 말고 현재 라벨 유지 + "본인/합산 미확정" 표시. 6% 실패가 분류를 막지 않게.
- 약식(기관 단순투자)은 특관 분해 대상이 아니므로 fail이 아니라 정상 경로.

## 통합 완료 (2026-06-15)

파서를 공용 모듈 `open_proxy_mcp/services/holder_table.py`로 추출하고
**ownership_structure + proxy_contest 양쪽에 반영**했다. 5% 블록은 proxy_contest가
ownership_structure의 control_context(control_map)에서 받으므로, ownership_structure 소스
한 곳을 enrich하면 두 tool이 함께 개선된다.

### 변경 지점
- `ownership_structure._latest_block_rows`: 능동(경영참여)+유의미(≥5%) 블록만 본문 합계표
  파싱(보통 1~3건으로 비용 제한). 합계표 없음(약식)·파싱 실패면 `holder_table=None`으로
  두고 기존 라벨 유지(graceful fallback).
- `ownership_structure._build_control_map`: 각 블록에 `self_pct`(보고자 본인 지분),
  `coheld_with_registry`(특관에 명부 최대주주 포함), `coheld_names` 추가(additive — 기존
  버킷 구조 불변). coheld 블록엔 observation 추가("…23.11%는 보고자 합산값이며 특관에
  명부상 최대주주 포함(본인 5.33%) — 외부 세력 단정 불가").
- `proxy_contest._signal_actor_side`: 우선순위 registry_overlap > **coheld_with_registry** >
  external_active_block > passive. `_fight_actor_group`도 coheld 인식.
- `proxy_contest`: `active_external_total_pct`에서 coheld 블록 제외(헤드라인이 명부 최대주주
  합산이라 related_total_pct와 이중계상 + 외부 압력 오독 방지) → signal_level 정확화.

### 검증 (scripts/coheld_integration_test.py, raw: 260615_coheld_integration_test)
- **타깃 솔루엠**: 얼라인 23.11% → self_pct 5.33 / coheld_with_registry=True /
  coheld_names=['전성호'], actor_side가 external_active_block → coheld_with_registry로 교정.
- **회귀 분쟁 60사**: crash 0. coheld 32사 발화 — 대부분 *정당한 교정*(현대차·삼성생명·
  셀트리온홀딩스·농협금융지주 등 이름이 명부 키와 정확히 안 맞아 '외부'로 오분류되던
  지배주주/모회사를 특관 매칭으로 포착).
- **스모크**: 고려아연 — 영풍은 registry_overlap 유지(우선순위), litigation 14·shareholder
  side 4 보존(분쟁 탐지 손실 없음). 삼성전자 — 삼성물산 registry_overlap, 분쟁 신호 미발화
  (과발화 없음).
- **테스트 스위트**: 65 proxy/ownership/control 테스트 통과, 전체 82통과(잔여 3실패는
  dividend/treasury timing — 본 변경과 무관, 사전 존재 확인됨).

### 잔존 한계
- coheld는 정규화 풀네임 정확매칭이라 흔한 이름 우연 충돌 가능(빈도 낮음, 결과는 external→
  coheld 완화로 경미). 명부 자체가 최대주주+특수관계인이라 매칭 시 대체로 유의미.
- 보고자 본인 이름은 명부에 없지만 실세인 케이스(최윤범 등)는 특관 매칭도 안 되면 여전히
  external_active_block — 본 통합 범위 밖(기존 한계 유지, coheld=False).

raw: [[260615_holder_table_census]] / 파서: `open_proxy_mcp/services/holder_table.py` /
검증: `scripts/coheld_integration_test.py` ([[260615_coheld_integration_test]])

## 공동보유자 명세 제품화 (2026-06-16)

웹 실사용에서 "솔루엠 전성호 32.78%의 공동보유자가 누구냐"에 답하지 못했다. 원인은 데이터가
*없어서*가 아니라 ① 파싱은 됐지만 출력에 노출 안 됨(control_map raw 필드에만) ② 이름 품질
버그였다. 이미 파싱된 데이터를 정제+라벨링+노출하는 작업.

### Did
1. **파서 정제** (`holder_table.py`):
   - self 이름 오염 제거 — 앵커 `주수 비율 보고자`를 `start`가 아닌 `.end()`부터 파싱
     (기존 "주수 비율 전성호" → "전성호").
   - **펀드/조합명 숫자 truncation 해결** — 이름 문자클래스에 `0-9` 허용. '제N호'의 단자리
     숫자는 ID 정규식(5~13자리)에 안 걸려 안전. ("호" → "신한 메자닌 신기술투자조합 제3호").
   - `holder_table_total()` 헬퍼 — 본인+특관 합(불변식 검증용).
2. **라벨링·노출** (`ownership_structure.py` + render): 공동보유 분해를 공용 헬퍼
   `_enrich_co_holders`로 **모든 scope(summary/blocks/control_map)** 5% 블록에 부착 →
   `reporter_self_pct`(본인) / `co_holders`[{name, ownership_pct, is_registry_holder}] /
   `co_holders_total_pct` / `co_holders_verified`(합≈헤드라인). render에 "공동보유자 분해" 표
   추가, **불변식 불일치 시 ⚠미검증 표시**(확정 인용 금지 — plausible-wrong 방지). tool desc에
   "본인 vs 공동보유자" 질의·필드 안내 명시(웹 AI 인지).
3. **검증 — 332사 전수**(분쟁 엣지 140 + 일반 top 192, `coheld_quality_census.py`):
   - 이름 품질 의심 **5사 → 1사**(펀드명 truncation 해소).
   - 불변식 정합 **92.7% (255/275) — before/after 불변(회귀 0)**, 파싱 fail 2 불변.
   - 솔루엠 전성호: 본인 15.2% + 소푸스제일차 9.05% + 얼라인계열 5.34% + 신한메자닌 조합 +
     가족(명부 ✓) — 합 34.69 vs 헤드라인 32.78 → `verified=False`로 정직하게 표시.

### 이름 클래스 보강 (2026-06-17) — 영문 길이 + ㈜ 기호
두 가지 이름 매칭 결함을 _NAME 문자클래스/길이로 교정:
1. **긴 영문 펀드명 잘림** — "Align Partners Capital Management Limited"(41자)가 상한 `{1,40}`
   초과로 "A"에서 실패→한 칸 밀린 "lign…"에 매칭. **상한 50**(실측 정상 이름 최장 46자
   'HALO MICROELECTRONICS…CORPORATION', >50은 여러 행 병합 garbage 1건뿐 — 50이 실제 이름은
   다 덮고 runaway는 억제. 80과 결과 동일). 더 긴 이름은 합≠헤드라인→`verified=False`로 포착.
2. **㈜ 등 괄호친 CJK 기호 누락 (under-count 주범)** — "포스코홀딩스㈜"·"넷마블㈜"·"SK㈜"의
   `㈜`(U+321C)가 이름 클래스에 없어 **대형 보고자 행이 통째 매칭 실패** → self가 작은 특관으로
   밀려 합 ≪ 헤드라인. `㈀-㋿`(괄호친 CJK)·전각괄호 추가로 해결.

332사 재검증: 불변식 **92.7% → 94.2%(261/277)**, fail 2→1, **회귀 0**. 포스코퓨처엠
60.62=60.62 / SK이노 52.1≈52.11 / 코웨이 26.47=26.47 완전 복구.

### 단일-library 양식은 금융사 전반 아님 (2026-06-17, 금융 35사 전수)
보수한도 `amount_unparsed`(기업은행·한국금융지주)가 금융사 공통인지 확인 → **아님**. 금융 35사 중
**단일 `<library>`는 이 2사뿐**, 나머지 33사는 library 4~7개로 정상 파싱(ok). 즉 업종 특성이
아니라 **두 회사의 공시 작성 양식(템플릿)** 문제. raw: [[260617_fin_library_census]].

### 외국법인 ID 인식 (2026-06-17) — 누락(합≪헤드라인) 주범 해결
under-count 케이스를 원문 대조하니 **외국 보고자 행이 ID 미인식으로 통째 드롭**이 주범:
- LEI 20자: OULANGE `836800ZVCHME2NPBL852`(디와이디), Parataxis `254900…`(파라택시스).
- 외국 등록번호 `\d3-\d3-\d3`: Den Norske `987-008-954`(현대글로비스).
`_ID`는 한국 숫자 ID(생년월일·사업자·법인번호)만 봐서 이 행들이 매칭 실패→self/대형 특관 드롭.
`_ID`에 **LEI(`[0-9]{4}[0-9A-Z]{14}[0-9]{2}`) + 외국번호(`\d3-\d3-\d3`)** 추가. 332사 재검증:
불변식 **94.2%→95.3%(265/278)**, **fail 1→0**, 회귀 0. 디와이디 31.56·파라택시스 57.68·
현대글로비스 50.35 완전 복구.

### 잔여 ~4.7%(13/278) — 표 레이아웃·측정 이슈 (verified=False로 정직 표기, 별도)
원문 대조 후 파서 단독으론 회귀없이 못 고치는 것으로 판정:
- **합 ≫ 헤드라인 (공동보유 표 병합·측정)**: 미래에셋벤처투자(69 vs 5.1 — 합계표는 그룹 전체,
  헤드라인 regex는 다른 값)·산돌(KCGI 29.58% 공동보유 병합)·레인보우(삼성+오준호 병합). 헤드라인
  추출 vs 합계표 총계의 기준 차이라 파서 문제 아님.
- **all-dash 합계표**: 씨씨에스·시스웍 — 합계표 셀 전부 "-"(실보유는 다른 섹션). 표에서 불가.
- **미세 Δ(±1~4%p)**: 한국항공우주·대호에이엘(101특관)·디앤디파마텍·TS트릴리온 — 소액 특관
  누락·반올림. ROI 낮음.
- 전부 `co_holders_verified=False`로 확정 인용 차단(honesty 유지).

### 교훈
- **"못 준다"의 진짜 원인을 구분** — 파싱 부재 vs *노출 부재*. 데이터는 raw 필드에 있었고
  렌더·라벨이 없어 (웹)모델이 못 읽은 것. 제품화 = 파싱+**노출/라벨**.
- **불변식 플래그로 honesty 유지** — 합 불일치(영문명·정정중복 등 ~7%)는 고치기 어려우니
  `verified=False`로 표기해 "그럴듯하게 틀린 확정값"을 막는다(이 도구 설계 원칙과 일치).
- 정규식 이름 문자클래스는 도메인(펀드 '제N호')을 반영해야 — 숫자 배제가 조합명을 잘랐다.

raw: [[260616_coheld_quality_census]] / 검증: `scripts/coheld_quality_census.py`
