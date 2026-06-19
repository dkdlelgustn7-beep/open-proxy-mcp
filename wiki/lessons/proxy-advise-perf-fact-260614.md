---
type: lesson
title: proxy_advise 성과 매트릭스 — 펀더멘털 fact 분리 + treasury 동적 lookback + 성능
context: 2026-06-14 "적자기업을 어떻게 판단하나 / 주주가치 지표 충분한가 / 시간 병목" 사용자 질문 연쇄
date_learned: 2026-06-14
related: [order-contracts-260613]
related_decisions: [260505_1700_decision_inside-director-performance-matrix]
---

# proxy_advise 성과 매트릭스 — 점수와 fact의 분리, 그리고 정확도 보존 성능 개선

## Context

사내이사 연임 성과 매트릭스(ROE/부채/CSR × avg/trend)에 대한 사용자(코붕이) 질문 연쇄:
"적자기업은 어떻게 판단하나" → "수주·해지도 fact로" → "ROE 말고 영업이익률도?" →
"주주가치 지표 이 정도면 충분?" → "시간 병목 있나" → "동적 lookback 안 된다며?".

## 점수 vs fact — 펀더멘털은 점수에 넣지 말고 분리

매트릭스 **점수는 주주가치 3축**(ROE=주주수익률 / 부채=재무위험 / CSR=환원)으로 절제하고,
사업 펀더멘털은 **점수 미반영 fact**로 분리했다. 이유: 적자 디폴트인 코스닥 바이오가 ROE만으로
부당하게 '저조'로 깔리는 걸 막되, 점수 로직(분기 키)은 오염시키지 않기 위함.

- **영업이익률 fact** (`director_performance.operating_margin`): ROE는 순이익/자기자본이라
  레버리지·일회성·자본잠식에 왜곡된다. 영업이익률(IS만, BS 무관)은 본업 수익성이라 그 왜곡을
  보완 — 특히 `core_profitable`로 적자기업의 '영업흑자+순손실(금융비용)' vs '영업적자(본업 부실)'를
  구분. `compute_performance(operating_margin_yearly=...)` → avg/trend/core_profitable 반환,
  `total_score`에는 미반영(구조로 보장).
- **수주·해지 fact** (order_contracts signal_summary): 적자기업 미래매출 가시성. 점수 미반영.

→ **주주가치 지표는 3축 + 펀더멘털 2 fact로 확정.** 빈틈으로 짚은 이익의 질(FCF)·이자보상배율·
ROIC는 의도적으로 제외(데이터는 financial_metrics에 다 있음). 매트릭스 비대화 방지 — 더 깊이
필요할 때 financial_metrics로 따로. **"점수는 절제, 해석 단서는 fact로"가 원칙.**

## treasury lookback 동적화 — 정확도 보존하며 단축

성능 측정 결과 proxy_advise wall의 큰 병목이 `treasury_share.summary`(자사주 소각 120개월).
사용자 직관("이사가 10년씩 안 산다") + 내 첫 오판("동적은 gather 순서상 불가")을 데이터로 검증:

- **내 오판 정정**: `director_evaluation`은 1차 gather에서 끝나 `earliest_start`(재직 시작)가
  treasury fetch(2차 gather) **전에** 이미 결정됨. 두 gather를 한 묶음으로 착각했을 뿐, 동적 가능.
- **동적 lookback**: `max(36, min(120, (target - min(earliest_start) + 2)*12))`.
  소각은 사내이사 재직기간만 CSR에 쓰이므로(나머지는 tenure 필터로 어차피 버려짐), 가장 오래
  재직한 사내이사 기준으로 좁힌다. detect fail(None) 1명이라도 있으면 보수적 120.
- **정확도 보존 실증 (20사)**: 동적 CSR 소각합 == 고정 120 기준 재직기간 소각합, **mismatch 0**.
  earliest detect 100%. 두산(이사 2025년 재직시작→36개월, 2016-19 소각은 재직 밖이라 무관)이
  가장 명쾌 — 자르는 게 정확. 삼성(전영현 17년)·SK(1995)·NAVER(1990)는 120 clamp 유지.
- 상한이 120이라 기존보다 더 자르지 않음 → 손해 0, 단기재직 회사만 빨라짐.

## 성능 — 줄일 수 있는 건 다 줄였고, 남은 건 구조적 하한

- **order_contracts fact 경량화**: 매트릭스 fact는 signal_summary 집계만 필요한데 문서 30개
  전체 파싱이 병목. `max_documents=10` → 삼성전자 order_contracts 2205ms→276ms(87%↓).
- **병목 측정 결과**: order_contracts 단독(수주 30건 조선·건설) 2.2초가 가장 무거운데 원인은
  **문서 HTML 파싱 CPU**(DART콜은 캐시로 1~2). corporate_deals는 공급계약 일원화로 0.2초로 개선.
  proxy_advise 4~6초는 treasury/dividend의 **throttle 직렬화가 근본 하한**(gather 병렬 무효 —
  [[order-contracts-260613]]의 방법C 교훈 재확인).
- 더 짜내려면 throttle 구조를 건드려야 하는데 그건 손해로 확인된 영역. **정확도·정합을 해치지
  않는 선에서 줄일 수 있는 건 다 줄였다.**

## Takeaway

- **점수는 절제, 펀더멘털은 fact.** 적자기업 오판을 막되 점수 분기 키는 오염시키지 않는다.
  영업이익률은 ROE 왜곡(레버리지·일회성)을 보완하는 해석 단서이지 점수가 아니다.
- **"안 된다"는 데이터·코드로 재확인하라.** 동적 lookback 불가 판단은 gather 단계 착각이었다.
  사용자의 "안 된다며?" 한 마디가 정확한 칼이었다.
- **성능 단축은 정확도 보존이 전제.** treasury 동적화는 mismatch 0(20사)를 확인하고서야 확정.
  재직기간 밖 데이터는 어차피 버려지므로 안 가져오는 게 정확하고 빠르다.
- **throttle 직렬화가 종합 tool의 하한.** gather 병렬은 무효 — 콜 수 자체를 줄이는 것(경량화·
  동적 lookback)만이 실효.

## Related

- [[order-contracts-260613]] (수주 tool 신설·일원화·파싱만 — fact 공급원, 방법C throttle 교훈)
- decision: [[260505_1700_decision_inside-director-performance-matrix]] (매트릭스 점수 설계)
- 검증: `scripts/dynamic_treasury_lookback_audit.py` (20사 mismatch 0)
