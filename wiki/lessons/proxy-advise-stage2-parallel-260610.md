---
type: lesson
title: proxy_advise 2단계 조기 발사 — 모델상 이득이 실측 노이즈에 묻혀 롤백
context: 2026-06-10 proxy_advise 병목 분석 → 방법 C 시도 → 복잡/흔한 케이스 실측 반증 → 롤백
date_learned: 2026-06-10
related: [ownership-summary-integrity-260610]
---

# proxy_advise 2단계 조기 발사 시도 — 모델의 함정과 롤백

## 결론 먼저

**방법 C(2단계 perf 조기 발사)는 component-timing 모델상 이득(중앙 1.7초)이었으나,
실제 wall-clock 실측에서 이득이 입증되지 않고(오히려 약한 손해 경향) 측정 노이즈에 묻혀 롤백했다.**
결과 정합성(회귀)은 0이었지만 시간 이득이라는 전제 자체가 무너졌다.

## Context

proxy_advise(의결권 자문 복합툴)는 하위 8개 서비스를 조합한다. 총 6446ms 중 1차(8개, 3163ms)와
2차(perf 3개, 3048ms)가 순차였다. 2차 perf(dividend+treasury 10년+financial)는 사내이사
재직 성과용으로 `director_eval`의 `inside_renewed` gate가 있을 때만 실행되는 조건부다.

## 시도한 것 (방법 C)

director_eval만 1차에서 분리해 먼저 await → gate 판단 → perf를 1차 완료 전 조기 발사
(나머지 1차와 겹치게). perf는 company_query만 필요(1차 결과 무관)하고 director가 일찍
끝나므로(중앙 596ms) perf가 나머지 1차에 숨는다는 논리.

- **모델**: 현재 `L1+P` → 방법C `max(L1, D+P)`. D≤L1이라 회귀 수학적 불가능, 100개에서 중앙 1.7초↓.
- **구현 + 정합성**: before/after `agenda_decisions`/`candidates_evaluations` **bit-identical**
  (현대차·삼성). 결과는 완전 동일 — 타이밍만 변경.

## 무엇이 반증했나 (실측)

100개의 "이득"은 `timings_ms`의 component 시간(L1, P)으로 계산한 **모델 예측**이었다. 실제
wall-clock으로 before/after를 측정하니:

- **복잡 케이스(D 큰 renewed) 20개**: 손해 16/20, 이득 중앙 **-356ms**. 하나금융 -2477, SK -2189.
- **흔한 케이스(D 작은 renewed) 15개**: 손해 12/15, 이득 중앙 **-349ms**, 평균 -433ms.
- **측정 노이즈**(같은 코드 2회 차이): |중앙| **426ms**, 범위 [-1893, +195].

→ **노이즈(426ms)가 방법C 효과(-350ms)보다 크다.** HD건설기계 손해 -1951ms 중 노이즈가
-1893ms, LS 손해 -1265 중 노이즈 -1187 — 손해의 대부분이 측정 변동이었다. 즉 효과가 노이즈에
완전히 묻혔고, 그럼에도 양쪽 평균이 일관되게 음수라 **약한 손해 경향**(Semaphore 경합 가설 부합).

## 왜 모델이 틀렸나

모델 `max(L1, D+P)`는 component 시간을 깔끔히 합산/겹침으로 환산했지만, 실제 wall-clock은:

- **`_UPSTREAM_SEM = Semaphore(3)`** — 동시성 3 제한. perf를 일찍 발사해도 무거운 1차 작업
  (ownership·meeting·treasury 10년)과 슬롯을 경쟁 → "공짜 겹침"이 안 됨.
- **throttle(0.066초/콜)** — 모든 DART 호출 직렬 간격. 콜 수가 시간을 지배. 발사 순서를 바꿔도
  총 콜 수가 같으면 총 시간이 크게 안 줄고, 무거운 작업이 한 풀에 몰리면 오히려 악화.
- **DART 응답 변동** — wall-clock이 ±400~1900ms 출렁여 component 모델과 괴리.

## Takeaway

- **component-timing 모델 ≠ wall-clock.** `timings_ms` 단계별 합으로 계산한 이득은 Semaphore·
  throttle·네트워크 경합을 무시한다. 모델 기반 최적화는 **반드시 wall-clock 실측으로 검증**하라.
- **효과를 재기 전에 측정 노이즈부터 baseline으로 재라.** 같은 코드 2회 차이가 426ms인데
  효과가 350ms면 그 효과는 측정 불가다. 노이즈 < 효과일 때만 유의미.
- **모델상 "수학적으로 이득 보장"도 실측에서 증발할 수 있다.** 추상화(component 합산)가 실제
  실행 모델(동시성 제한·직렬 throttle)을 안 담으면 결론이 뒤집힌다.
- **사용자의 "복잡 케이스 전수조사" 요구가 모델의 함정을 잡았다.** 흔한 케이스 모델 이득만 봤다면
  잘못 배포했을 것. 엣지 케이스 실측 + 노이즈 baseline이 안전망이었다.
- **회귀(결과 정합)와 성능(시간)은 별개로 검증하라.** 회귀 0이어도 시간 이득이 없으면 복잡도만
  늘어 롤백이 맞다.

## Related

- [[ownership-summary-integrity-260610]] (같은 세션 — 거기선 throttle interval 조정이 전역 실효)
