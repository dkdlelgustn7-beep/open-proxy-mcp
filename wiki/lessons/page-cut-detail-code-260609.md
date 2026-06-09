---
type: lesson
title: 공시 검색 페이지컷 truncation → detail-code 좁히기 (6 tool)
context: 2026-06-09 사용자 지적 "페이지수로 끊는 게 부정확" → 카탈로그 기반 detail-code 좁히기
date_learned: 2026-06-09
related: [공시유형코드체계, 배당공시유형]
---

# 공시 검색 페이지컷 truncation → detail-code 좁히기

## Context

`search_filings_by_report_name`는 넓은 공시유형(pblntf_ty="I" 등)을 페이지 단위로 받아
(`max_pages=10`) 제목 필터한다. 사용자 지적: "API 데이터를 페이지수로 끊는 게 비정확하다."
이미 만든 [[공시유형코드체계]] 카탈로그로 각 tool을 정확한 detail 코드로 좁혀 검증했다.

## Did

- **6 tool detail-code 좁히기** (카탈로그 매핑 + '넓은type vs detail 차집합 0' 검증):
  - corp_gov_report I→I001 / value_up I→I001 / shareholder_meeting E→E006·I→I001
  - treasury_share B,I,E→[B001,E001,E002,I001] / related_party B,I→[B001,I001]·I→I001
  - proxy_contest 소송 I,B→[I001,B001] / 위임장·5%·공개매수 D→[D001,D003,D004]
- **filing_search 멀티 detail-code 지원** — `pblntf_detail_ty`가 리스트면 코드별 스캔(union).
- **013 버그 fix** — 멀티코드 스캔 중 한 코드가 013(데이터없음)을 던지면 루프가 통째
  early-return해 다른 코드 결과까지 날리던 문제 → 013은 continue. 단일코드도 013을 빈결과로.

## Improved

- **page-cut truncation 실사례 발견·교정** ★ — proxy_contest D 검색이 삼성전자에서 실제 잘림:
  삼성은 **D002(임원·주요주주 소유상황, 수천 건)**가 D 전체 페이지를 채워 max_pages=10에서
  D001/D003/D004(위임장·5%·공개매수) 일부가 누락. **D broad=6 vs detail=14 = +8 복구.**
  detail로 좁혀 D002 제외하니 페이지컷 없이 전부 수집.
- 나머지 tool은 차집합 0(누락 없음) + 속도·정밀도 개선. treasury 삼성 27=27·KB 31·고려아연 28.

## Trade-off

- 멀티유형(B,I,E) tool은 detail 코드 수만큼 sub-search (treasury 3→4) — 각 search가 좁아져
  페이지·총시간은 오히려 감소. detail 코드 가정이 틀리면 누락 → **차집합 검증 필수**.
- treasury 초기 가정(B001+E001+I001)이 삼성에서 0 반환 → 013 abort 버그가 원인이었음
  (E002 no-data). 검증이 버그를 잡음.

## Takeaway

- **넓은 공시유형 페이지 순회는 prolific 회사에서 truncation을 일으킨다.** (삼성 D002 flood)
  detail-code(카탈로그)로 좁히면 무관 공시(D002)를 애초에 안 받아 누락이 사라진다.
- **detail 코드 매핑은 반드시 '넓은type vs detail 차집합 0'으로 검증.** 가정이 틀리면 조용히 누락.
- **013(no-data)은 에러가 아니라 빈결과.** 멀티 스캔에서 abort하면 안 됨.
- **이미 만든 카탈로그를 재사용하라** — 추측 없이 정확한 코드 매핑.

## Related commits

- `bd81fde` 단일코드 3 tool / `d38b4f3` filing_search 멀티코드+013 fix + treasury / `6d4ccca` related_party+proxy_contest

## Related

- [[공시유형코드체계]] (detail 코드 → 실제 공시 매핑 — 좁히기의 근거)
- [[배당공시유형]] (dividend I001 좁히기 — 같은 패턴 첫 적용)
