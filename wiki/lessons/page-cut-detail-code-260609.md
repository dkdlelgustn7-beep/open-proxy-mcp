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

## 직접 search_filings 호출 전수 확인 (helper 미경유 4곳)

`search_filings_by_report_name` helper를 안 거치고 `client.search_filings`를 직접 부르는
4곳도 전수 점검했다. 단일 호출/소량 page는 helper의 max_pages보다 **더 심한** 컷 가능.

- **ownership_structure `_fetch_change_filings`** 🔴 최악 사례 — `pblntf_ty="I" page_count=20`
  단일 호출로 받아 '최대주주등소유주식변동신고서'(=I004) 필터. I 전체 20건이 배당·실적·
  주총에 밀려 변동신고서가 거의 다 잘림: **삼성 8 vs 90(82 누락), 고려아연 0 vs 40,
  SK이노 0 vs 20, 현대차 1 vs 16.** → `pblntf_detail_ty="I004" page_count=100`으로 교정.
- **director_evaluation** — `pblntf_ty=None` 6페이지 순회로 '주주총회소집공고'(=E006) 필터.
  → `pblntf_detail_ty="E006"`로 좁힘. 차집합 0(삼성·고려아연·SK·현대차), 6콜→1콜.
- **company `_recent_filings`** — '최근 공시 인덱스' 전체 type 의도적 광역(회사 활동 개요).
  특정 공시 타깃이 아니므로 **좁히지 않음(정상)**.
- **shareholder_meeting fallback** — E type 부족 시 `pblntf_ty=None` 안전망. **의도적 광역**.

## detail-code 좁히기는 정확하지만 'scope 정의'가 좁으면 다른 형태 변동을 놓친다

ownership_structure `changes` scope를 I004로 정확히 좁힌 뒤 사용자가 물었다: "고려아연이
변동이 없는 게 맞아?" — 영풍-MBK 분쟁사인데 직관에 안 맞았다. 확인하니:

- I004(최대주주등소유주식변동신고서) 마지막이 2025-03-24 → 최근 12개월엔 0건. **기술적으론 맞다.**
- 하지만 고려아연 지분 다툼은 **D001(주식등의대량보유상황보고서, 5%)**로 신고되고 있었다.
  2026-05까지 영풍 41%·한국기업투자홀딩스(MBK) 37%·최윤범 18%가 계속 5%보고로 움직임.

즉 **I004 narrowing 자체는 옳았지만(삼성 82건 복구), `changes` scope 정의가 I004 한 종류에
갇혀** 분쟁사의 진짜 변동(5%보고)을 못 보여줬다. `changes`에 5% 변동(`timeline_rows`)을
합쳐 해결 — 이 데이터는 build 함수가 scope 무관하게 753에서 majorstock으로 이미 받아 784에서
window 필터까지 해두고 changes에서 버리던 것이라 **추가 DART 콜 0**.

→ 교훈: **"좁히기"의 정확도와 "scope의 포괄성"은 별개다.** 한 공시유형으로 좁힌 scope는
같은 사건이 다른 공시유형으로 신고될 때 조용히 빈다. 사용자의 "이게 맞아?" 의심이 이를 잡았다.

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
- **helper를 안 거치는 직접 search_filings 호출도 전수 점검하라.** 단일 호출(page_count=20)은
  helper의 max_pages=10보다 더 심한 컷을 낳는다(ownership I/20 → 삼성 82건 누락). 단,
  '최근 공시 인덱스'처럼 의도적 광역은 좁히지 말 것 — 타깃 공시 검색만 detail로 좁힌다.

## Related commits

- `bd81fde` 단일코드 3 tool / `d38b4f3` filing_search 멀티코드+013 fix + treasury / `6d4ccca` related_party+proxy_contest

## Related

- [[공시유형코드체계]] (detail 코드 → 실제 공시 매핑 — 좁히기의 근거)
- [[배당공시유형]] (dividend I001 좁히기 — 같은 패턴 첫 적용)
