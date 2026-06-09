---
type: lesson
title: ownership_structure summary 재설계 + 100% 정합 분해 + 정합성 버그 2건
context: 2026-06-10 사용자 "고려아연 지분구조" 질문 → summary 구조 점검 → 33개사 스크리닝
date_learned: 2026-06-10
related: [공시유형코드체계, page-cut-detail-code-260609]
---

# ownership_structure summary 재설계 + 정합성 버그

## Context

사용자가 "고려아연 지분구조 알려줘"를 물으며 summary scope의 구조를 점검했다.
분쟁사(영풍-MBK)인데 명부 최대주주(와이피씨 25%)만 헤드라인에 떠 실세(영풍 41%)가
안 보였고, "지분율 합산 100% summary"를 요청했다. 이어 33개사 버그 스크리닝으로 이어졌다.

## Did

- **changes scope** — `pblntf_ty="I"` 20건 단일조회 → **I004(최대주주변동신고서)** 좁힘
  (삼성 8→90건, I 전체 20건이 배당·실적에 밀려 변동신고서 누락). + **5% 대량보유 변동
  통합**(`timeline_rows`, 753에서 이미 받아 784서 window 필터 — 추가 콜 0). 분쟁사는
  최대주주변동(I004) 대신 5%보고(D001)로 지분이 움직여 I004만 보면 빈다(고려아연 0→15건).
- **summary 재설계** —
  - 헤드라인 **단독/특관 구분**: "명부상 최대주주(본인 단독) 25.21%" vs "본인+특관 32.88%".
    집계 기준이 달라 합산 오해를 부르므로 라벨 분리(솔루엠: 단독 13% vs 5%보고 32.78%).
  - **5% 대량보유 실세** 한 줄(영풍 41%) — "보고자 합산 기준" 명시.
  - **지분 구성 (발행주식총수 100%)** 표 — 명부(본인+특관)/자사주/기타로 중복 없이 분해.
  - 명부 테이블 **노이즈 컷**(0.1% 미만 → "외 N인"), 자사주 중복 섹션 제거,
    요약+100%구성 **병합**(6블록 → 3블록).
- **director_evaluation** — `pblntf_ty=None` 6페이지 → **E006(주주총회소집공고)** (차집합0).

## Bug (33개사 스크리닝으로 발견·교정)

- 🔴 **셀트리온 `issued=0`** — `_treasury_snapshot`이 `se`에 "보통" 들어간 행만 봤는데,
  **우선주 없는 회사는 `보통주` 행 없이 `합계` 행만** 표기(셀트리온 발행총수 2.3억주)
  → issued=0 → 100% 분해·자사주 통째 누락. **합계 행 fallback**(우선주 발행분 차감해
  보통주 기준 유지)으로 교정. 우선주 있는 회사는 보통주 행이 있어 영향 없음(회귀 0).
- 🔴 **금호석유 resolve 실패** — "금호석유"가 정식명 "금호석유화학"의 prefix라 완전일치·
  정규화일치 모두 실패 → `_resolve_match` fallthrough로 AMBIGUOUS(후보 1개인데 selected=None).
  **상장사 후보가 유일하면 자동선택**(EXACT)하도록 보강. "금호"·"삼성" 같은 약칭은 후보
  0/다수라 1개로 잘못 안 좁혀짐(ERROR 유도) — 오선택 리스크 없음 확인.
- **맥쿼리인프라 `issued=0`(펀드형)** — 인프라펀드(집합투자기구)는 주식총수 미공시(013).
  조용히 사라지던 100% 섹션에 "발행주식총수 미확보 — 집합투자기구/미공시" **안내 추가**.

## 성능 — throttle 정합 + scope별 콜 절감

시간 병목을 측정(timings_ms)하니 summary 746ms 중 `annual_report_apis`(270) +
`block_holders`(270)가 지배. gather 병렬화를 시도했으나 **거의 안 줄었다(28ms)**.

- **원인 = `client._throttle_api`의 호출당 최소 간격이 직렬화.** 모든 DART 호출이
  `_api_rate_lock`(Lock)을 통과하며 `_MIN_INTERVAL_API`만큼 간격을 둔다 → gather로 동시
  발사해도 throttle이 하나씩 내보내 병렬화 무효. (→ 병렬화 롤백)
- 🔴 **`_MIN_INTERVAL_API = 0.1`이 과보수.** 0.1초 = 분당 600회 상한인데, 정작 cap으로
  둔 `_API_RATE_LIMIT_PER_MINUTE = 910` window에 **도달조차 불가**(600 < 910). 즉 의도한
  방어선이 무력. **0.066초**(=60/910)로 낮춰 분당 상한을 window cap과 정합시킴 →
  단일 흐름 1.5배, 안전마진 9%(<1000)는 그대로. interval은 **burst 평활화**용이고
  (window는 평균만 막아 순간 burst를 못 막음) race는 Lock이 직렬화로 보장하므로 간격과 무관.
  summary 746→360ms(warm).
- **scope별 불필요 콜 스킵** — `stock_total`·`treasury`는 summary/control_map만,
  `majorstock`은 major_holders 빼고 필요. 조건부 호출로 major_holders 4→1콜,
  blocks 4→2, changes 4→3. `major`는 top_holder/related_total 공유 로직이라 유지(회귀 회피).

## Takeaway

- **명부(hyslrSttus, 본인+특관)와 5%보고(majorstock, 보고자 합산)는 집계 기준이 다르다.**
  100% 정합 분해는 **명부 기준으로만** 가능(명부+자사주+기타). 5%보고는 보고자 공동보유·
  중복이라 합산 100%가 안 된다(영풍41+MBK37+최윤범18=111%↑). 둘을 라벨로 분리하라.
- **narrowing의 정확도와 scope의 포괄성은 별개다.** changes를 I004로 정확히 좁혔어도
  분쟁사가 5%보고로 움직이면 빈다 → scope에 5% 변동을 합쳐 포괄성 확보. (cf. [[page-cut-detail-code-260609]])
- **stockTotqySttus는 우선주 없는 회사면 `보통주` 행 없이 `합계` 행만 준다.** 보통주 행을
  가정하면 issued=0. 보통주 우선 → 합계 fallback이 안전.
- **정식명 prefix 단일 후보는 자동선택하라.** 완전일치만 고집하면 "금호석유"를 못 찾는다.
  단 약칭(다수 후보)은 모호하게 좁히지 말고 명확화 유도.
- **rate-limit throttle 환경에선 병렬화보다 콜 수 절감이 답이다.** 호출당 최소 간격이
  gather를 직렬화하므로(병렬 28ms뿐) 시간은 콜 수에 비례. 또 `_MIN_INTERVAL_API`가
  window cap보다 빡빡하면 cap이 무력화되니, **간격은 window cap과 정합**시켜야(0.066=60/910).
- **엣지 스크리닝은 일부러 까다로운 표본으로.** 우선주 대형주·소유분산·인프라펀드·합병사·
  분쟁사 33개를 돌려 정합(합 100%)·issued=0·기타음수 flag로 버그를 잡았다.

## Related commits

- (이 lesson과 함께 커밋)

## Related

- [[page-cut-detail-code-260609]] (detail-code 좁히기 — changes I004 narrowing 같은 맥락)
- [[공시유형코드체계]] (I004 최대주주변동신고서 / D001 5% 대량보유 매핑)
