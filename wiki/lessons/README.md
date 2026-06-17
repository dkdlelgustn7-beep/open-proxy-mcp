---
type: readme
title: lessons/ — 작업 회고
updated: 2026-06-13
---

# lessons/

작업하면서 배운 것 + 결정의 trade-off. 시점에 묶지 않은 정체성 문서 (`{topic}.md`).

각 페이지 schema:
- **Context**: 왜 이걸 다뤘나
- **Did**: 무엇을 했나
- **Improved**: 무엇이 나아졌나
- **Trade-off**: 무엇을 잃었나
- **Takeaway**: 다음에 반복할 원칙

## 목록 (2026-06-13 기준)

1. [[acode-semantic-markers]] — DART 본문 ACODE 발견 → text regex 한계 돌파, 99% 안정성
2. [[scope-simplification]] — tool 안 specialized scope 폐지 → 사용자 라우팅 단순화
3. [[time-axis-tool-split]] — shareholder_meeting을 사전(notice)/사후(results)로 분리 → fragility 격리
4. [[hard-rate-limit]] — DART 분당 1000회 hard rule을 코드로 강제 → 차단 사고 재발 방지
5. [[ralph-threshold-realism]] — 표준 서식 99% / 자유 텍스트 90% — 데이터 자체 한계가 threshold 결정
6. [[decision-vs-raw-separation]] — decision logic은 tool 안에서, raw expose는 외부 tool로
7. [[enrichment-as-infrastructure]] — facts/risk/citation/근거공고 = 검증 가능한 응답의 핵심
8. [[distribution-calibrated-thresholds]] — classification cutoff은 prior 직관이 아니라 audit 표본 분포 본 후 정함
9. [[decision-tree-vs-matrix]] — 안건 결정 2가지 방식 (매트릭스 vs 트리), 안건 성격이 방식 결정
10. [[perf-timing-260524]] — stage timing 먼저, 의미 보존 범위에서만 latency 개선
11. [[agenda-relation-parser-260525]] — agenda relation은 결론이 아니라 자동 판단을 멈추는 guardrail, KOSPI300 parser regression 0 확인
12. [[agenda-classification-260507]] — agenda parent/child short-circuit와 high-impact 분류
13. [[classify-high-impact-260508]] — high-impact 안건 분류 threshold와 false positive 회피
14. [[law-layer-260508]] — 법령 layer 도입의 결정/검증 분리
15. [[law-layer-precision-260508]] — 법령 layer 정밀화와 parent pattern guard
16. [[law-layer-body-260510]] — 제목 매칭 한계와 body fallback
17. [[parser-precision-260508]] — 파서 정밀화 판단 기준: source 한계 vs parser 한계 분리
18. [[parser-omnibus-260506]] — parser omnibus 검증과 DART table edge case
19. [[agenda-hierarchy-260510]] — 호수 hierarchy 추출과 D 패턴 fallback
20. [[subagenda-mapping-260510]] — sub-agenda와 amendment 1:1 매핑
21. [[director-faithfulness-260510]] — 사외이사 겸직/충실성 fact 노출
22. [[career-parser-concat-260510]] — careerDetails concat/boundary 처리
23. [[260510_daily-summary]] — 2026-05-10 일일 작업 요약

### 2026-06 (분쟁신호 · 데이터 정밀화 · 전수조사)

24. [[contest-signals-500-260605]] — 경영권 분쟁 신호 다축화 (5% 동학·소송 4단계), 정보 구조화 + LLM 위임
25. [[dispute-reverse-lookup-260607]] — 분쟁 공시 역추적이 시총순보다 5배 효율 (142종목 → 70 분쟁)
26. [[dividend-source-of-truth-260609]] — 배당 출처맵 확정 + 정기보고서 누적 차분, 51사 정합성 100%
27. [[page-cut-detail-code-260609]] — 페이지컷 truncation → detail-code 좁히기 (6 tool, 차집합 0 검증)
28. [[ownership-summary-integrity-260610]] — ownership summary 재설계(100% 분해·단독/특관) + 정합성 버그·DART 단위 오염, 450사 전수
29. [[proxy-advise-stage2-parallel-260610]] — 2단계 조기 발사: 모델 이득이 wall-clock 실측서 반증 → 롤백 (component 모델 ≠ wall-clock)
30. [[tool-naming-discovery-260610]] — tool 이름·desc가 자연어 라우팅을 좌우 (related_party_transaction → corporate_deals)
31. [[risk-events-pipeline-260611]] — 리스크 이벤트 6종 통합 tool (I001+B001 채널 매핑, 사상자 supersede 집계)
32. [[financial-metrics-precision-260612]] — 모델 hedge 역추적 → 412사 전수, 누적 공시는 항상 차분
33. [[tool-coverage-audit-260612]] — audit 미커버 툴 전수조사 (proxy_result 0건 회귀·seam·render·production), baseline 없는 툴은 죽어도 모른다
34. [[order-contracts-260613]] — 수주 tool 신설(매출대비%·정정 dedup/diff) + proxy_advise 별도 fact, 같은 공시도 관점 다르면 다른 tool. 해지 파서 전수·corporate_deals 공급계약 일원화·추론 제거(파싱만)
35. [[proxy-advise-perf-fact-260614]] — 성과 매트릭스 점수는 절제·펀더멘털은 fact(영업이익률·수주), treasury 동적 lookback(정확도 보존 mismatch 0), throttle 하한
36. [[shareholder-meeting-agenda-parse-260615]] — 주총 안건 파싱 점검: 보수한도 단위 미환산·폴백 4종 + agenda 카테고리 분류. 큰샘플 진단→폴백→regression 방법론. 재무제표·정관·parse_status확대는 병렬 세션 진행, **실질 남은 건 선임(board) 세부**
37. [[render-output-audit-260616]] — render 출력 점검(11 tool·410사): 데이터는 멀쩡한데 화면만 이상(dict 노출·None%·군더더기) 3종 + 독립성 evidence 화면 구조화 노출 + 경고 아이콘 ⚠️ 통일. `.get(key,default)`는 None값에 default 안 씀
38. [[topdown-screening-feasibility-260617]] — 탑다운 스크리닝(영업이익30%+·주주제안) 500사 전수: 파서(b)·정보(필드 인벤토리)도 충분(financial 36지표·ownership 42필드) → 정보상 지금 바로 가능. 막힌 건 효율(순회 비용)뿐 — 설계(a)/사전인덱싱(c)으로. 탑다운 3유형(공시유형 콜1/본문안건 콜1천/본문지표 콜7천)
39. [[treasury-multitype-result-260617]] — 자사주 취득결과 보통주+우선주 복수 종류일 때 ACODE(ACQ_AMT)가 보통주만 잡아 우선주 누락(미래에셋 600억 vs 결정 1,000억). 일별 취득가액총액 합산으로 보정, 5%가드+단일종류 무변=회귀 안전
