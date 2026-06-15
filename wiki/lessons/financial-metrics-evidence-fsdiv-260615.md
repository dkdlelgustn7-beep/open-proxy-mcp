---
type: lesson
title: financial_metrics — "불가능해 보인 실적"이 실제였던 SK하이닉스 26Q1 + evidence/fs_div/순이익 alert 3대 보강
context: 2026-06-15 실사용 "SK하이닉스 26Q1 실적·현금흐름·원문링크" 질의에서 호스트 모델이 헤드라인을 산출 아티팩트로 오판 → 본문 대조로 실수치 확인 + 부수 결함 3건 교정
date_learned: 2026-06-15
related: [financial-metrics-precision-260612]
---

# financial_metrics — 실수치 오판 사건 + evidence/fs_div/순이익 alert 보강

## Context

웹(claude.ai) "SK하이닉스 26년 1분기 실적" 질의에서 도구가 매출 **52.6조 / 영업이익
37.6조 / OPM 71.5% / 순이익 40.3조(>영업이익)**를 반환했다. 호스트 모델은 이를 "메모리
사이클 정점" 서사로 풀었고, 이어 진단 과정에서 **"분기 differencing·annualize 아티팩트"**
로 의심했다. 사용자: *"그냥 돈을 존나 많이 벌어서 그런걸 수 있잖아."* — 본문 대조 결과
**사용자가 맞았다.**

## 핵심 교훈 — 컷오프 이전 상식으로 실수치를 아티팩트로 단정하지 말 것

분기보고서 본문(rcept `20260515002287`, production 경로 `get_document`)을 직접 열어 대조:

- 회사가 자기 입으로 *"영업이익은 37.6조원으로 **4개 분기 연속 사상 최대**, 영업이익률은
  전분기 대비 13%p 개선된 **72%**"* 라고 서술. 매출 52,576,287백만, 분기순이익
  40,345,909백만, 그리고 **순이익 QoQ +164.6% / YoY +397.6%가 공시 실적표에 그대로**.
- **API = 본문 = 보도문구 3자 완전 일치** → 도구는 처음부터 정직했다. "DART XBRL 이상"
  가설은 틀렸다.
- NI>OI도 정상: 법인세차감전 51.62조 = 영업이익 37.61 + 영업외 약 14조, 세금 약 11조 →
  순이익 40.35. 영업외가 세금보다 커서 순이익이 영업이익을 넘은 것(본문에 그대로).
- 메모리는 고정비 레버리지가 커서 **가격 폭등 시 증분 매출이 거의 그대로 영업이익**으로
  떨어진다 → 초호황기 OPM 폭증은 물리적으로 가능. 71.5%가 "팹리스 엔비디아도 안 넘는다"는
  내 직관이 컷오프(2026-01) 이전 사이클 기준이라 과잉 기각이었다.

원칙: **API 수치가 의심되면 본문(production `get_document`)으로 대조한다.** raw API ↔ 본문
재무제표 ↔ 보도문구 3자 대조가 "도구 버그 / DART 소스 오류 / 진짜 극단값"을 가른다.
"그럴듯하게 틀림(plausible wrong)"만 위험한 게 아니라 **"그럴듯해서 틀렸다고 오판(plausible
dismissal)"**도 똑같이 위험 — 진짜 사건(초호황)을 산출 버그로 묻을 뻔했다.
([[financial-metrics-precision-260612]]은 반대 방향 — 모델 hedge가 진짜 버그를 가리킨 사례.
이번엔 모델 의심이 *오진*이었다. 둘 다 결론은 "본문/전수로 검증".)

## Did (부수적으로 드러난 진짜 결함 3건 교정 — 단일 파일)

오판 추적 중, 헤드라인은 멀쩡했지만 **주변부 3건이 진짜 결함**이었다.

1. **evidence 빈 링크 → 원문 rcept 부착** (가장 큰 실익). 헤드라인 숫자는 진짜인데
   원문 링크를 못 주는 신뢰 역전(`[](-)`)이 있었다. 원인: 숫자 출처가 `fnlttSinglAcnt`
   (재무 집계 API)인데 이 API는 **rcept_no를 안 돌려준다**. 그런데 rcept는 `list.json`
   (정기공시) 1회면 나온다. 헬퍼 `_periodic_filing_ref(corp_code, year, reprt_code)`로
   reprt_code↔보고서명 매칭해 최신 정기보고서 rcept/접수일/보고서명을 5개 scope
   (summary/yearly/quarterly/yoy/qoq) EvidenceRef에 부착 → `viewer_url` 자동 생성.
   실패 시 None(graceful, 합성 마커 유지). 추가 비용 scope당 list.json 1콜(캐시).
   검증: SK하이닉스 → `분기보고서 (2026.03)` rcept `20260515002287` + DART 뷰어 URL.
2. **순이익 QoQ alert 비대칭 → 대칭화**. row-level qoq/yoy엔 순이익이 있었으나(누락은
   서술 문제), `_detect_qoq_alerts`가 **영업이익·매출만 보고 순이익을 안 봤다**(YoY signals는
   봄). `net_loss_quarter`(적자전환, 영업이익과 대칭) + `net_income_below_operating`
   (영업흑자인데 순이익 적자 = 영업외/일회성 주도 신호) 추가.
3. **CFS→OFS 조용한 폴백 → 경고 + 실제 기준 라벨**. `_safe_fetch_acnt`는 연결 미작성 시
   말없이 OFS를 반환했고 `metrics["fs_div"]`는 요청값(CFS)을 그대로 기록 → 별도 수치를
   연결로 오인할 위험 + 분기 시리즈 혼재 가능. 헬퍼 `_actual_fs_div`(반환 rows의 fs_div
   다수결)로 감지해 `_fetch_year_metrics`·`_build_quarterly`에서 경고 + `fs_div`를
   **실제값**으로 기록. 검증: 신라섬유·조비·카프로·광명전기(연결 미작성) → `fs_div=OFS` +
   "연결재무제표(CFS) 미작성 — 별도(OFS) 기준" 경고 발화.

## 메타 교훈

- **출처 없이 수치 보증 금지.** evidence 빈 링크는 "실제 공시 데이터"라 보증하면서 정작
  출처를 못 대는 모순을 만든다. 도구는 수치와 함께 rcept를 항상 실어야 한다.
- **선택적 서술 경계.** 모델이 가장 이상한 지표(순이익 +398%, NI>OI)를 서술에서 빼는
  편향이 있었고, alert 비대칭이 이를 거들었다. payload·alert를 대칭으로 두면 편향이 준다.
- **plausible dismissal 경계.** 극단값일수록 기각 전에 본문 대조. 사용자 직관(현장 감각)이
  컷오프 묶인 모델 직관을 이긴 사례.

## 회귀
- financial 관련 테스트 통과, 전체 82통과(잔여 3 실패 dividend/treasury timing은 본 변경과
  무관 — stash 대조로 사전 존재 확인). 변경은 `services/financial_metrics.py` 1파일.
