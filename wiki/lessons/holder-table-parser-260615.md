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
