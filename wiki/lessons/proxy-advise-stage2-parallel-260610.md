---
type: lesson
title: proxy_advise 2단계(perf) 조기 발사 — director gate를 1차 완료 전에 판단
context: 2026-06-10 proxy_advise 6.4초 병목 분석 → 100개 전수조사 → 방법 C 구현
date_learned: 2026-06-10
related: [ownership-summary-integrity-260610]
---

# proxy_advise 2단계 perf 조기 발사 (방법 C)

## Context

proxy_advise(의결권 자문 복합툴)는 하위 8개 서비스를 조합한다. 측정 결과 총 6446ms 중
**1차(upstreams 8개, 3163ms)와 2차(perf 3개, 3048ms)가 순차**여서 거의 시간이 합산됐다.
2차 perf(dividend + treasury 10년 + financial yearly)는 사내이사 재직 성과 매트릭스용으로,
1차 `director_eval`의 `inside_renewed`(사내이사 renewed) 후보가 있을 때만 실행되는 조건부다.

## 뭐에서 뭐로

**Before** — 1차 gather(director_eval 포함 8개) **전부 완료 후** gate 판단 → 2차 perf gather:
```
[1차 8개 gather] ──3163ms── [gate] [2차 perf gather] ──3048ms──  = 6.4초
```

**After (방법 C)** — director_eval을 1차에서 분리해 **먼저 await** → gate 판단 →
perf를 **1차 완료 전에 조기 발사**(나머지 1차 7개와 병렬로 겹침):
```
[director_task] ─596ms─ [gate] ┐
[others 7개 gather] ──────────── ┴ [perf 발사] ──── 나머지 1차와 perf 겹침 = 3.8초
```

## 왜 가능한가

- **perf는 1차 결과와 무관** — 입력이 `company_query`뿐(dividend/treasury/financial은 회사 단위).
  gate(`inside_renewed`)만 director_eval 결과를 필요로 한다.
- **director_eval이 1차에서 일찍 끝난다** — KOSPI 100 측정 중앙 596ms (1차 전체의 ~1/4 시점).
  그래서 perf를 director 완료 직후 발사하면 perf 3초가 나머지 1차(아직 2.4초 진행 중)에 숨는다.

## 구조

```python
director_task = asyncio.create_task(_safe_throttled(director_eval, ...))   # 먼저 발사
others_task   = asyncio.gather(meeting×4, ownership, gov, fin)             # 나머지 1차 7개
director_eval = await director_task                                        # director만 먼저 회수
inside_renewed = [ev for ev in evals if 사내 and renewed]                   # gate 판단
perf_task = asyncio.gather(dividend, treasury, financial) if inside_renewed else None  # 조기 발사
meeting, ..., fin = await others_task                                      # 나머지 1차 회수
...                                                                        # 1차 의존 로직
if perf_task: perf_div, perf_treas, perf_fin = await perf_task             # perf 회수
```

## Trade-off 분석 (3개 방법 비교)

| 방법 | renewed 회사 | renewed 없는 회사 | 헛콜 | 회귀 |
|---|---|---|---|---|
| A 낙관적(perf 무조건 병렬) | 이득 | 시간 동일 | 🔴 treasury(10년) 헛콜 | - |
| B director 먼저 순차 | 이득 | 🔴 +0.6초 손해 | 0 | 발생 |
| **C 조기 발사(채택)** | **이득** | **동일** | **0** | **0** |

방법 C 시간 모델: 현재 `L1+P` → 방법C `max(L1, D+P)`. D ≤ L1이므로 **항상 ≤ L1+P (회귀 수학적 불가능)**.
renewed 없는 회사는 perf 미발사 → 현재와 동일(손해 0). A의 헛콜은 gate 정확 판단으로 차단.

## 검증 (100개 전수조사 + 회귀)

- **renewed 비율 64/100** — perf 실행(이득 가능) 회사. 나머지 36%는 perf 미발사(손해 0).
- **회귀 케이스 0/100** — 모델 `gain = (L1+P) - max(L1,D+P) ≥ 0` 실측 확인 (`min gain = 701ms`).
- **이득 중앙 1687ms, 최대 3291ms** (현대차 8924→5633 모델 / 실측 7408→4773).
- **결과 동일성** — git stash로 before/after 비교: 현대차·삼성전자 `agenda_decisions`/
  `candidates_evaluations` **bit-identical**(decisions·성과 매트릭스 무손실). 타이밍만 변경.
- 측정 데이터: `wiki/architecture/audits/data/proxy_advise_stage2_parallel_260610.json`,
  스크립트: `scripts/proxy_advise_stage2_parallel_analysis.py`.

## Takeaway

- **조건부 2단계는 gate 입력만 먼저 확보하면 조기 발사로 합산을 겹침으로 바꾼다.** 2단계가
  1단계 "결과 전체"가 아니라 "일부(gate)"에만 의존하면, 그 일부를 먼저 await해 2단계를 당긴다.
- **trade-off를 막는 핵심은 gate 정확성.** 낙관적 병렬(A)의 헛콜은 gate를 건너뛰어 생긴다.
  gate를 정확히(director 결과로) 판단하면 헛콜 0 + 손해 0을 동시에 얻는다.
- **수학적 회귀 불가능 + 100개 실측 회귀 0 + before/after bit-identical** 3중 검증으로 안전 확인.

## Related

- [[ownership-summary-integrity-260610]] (같은 세션 ownership 성능/정합성 작업)
