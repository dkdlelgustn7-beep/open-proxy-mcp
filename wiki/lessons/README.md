---
type: readme
title: lessons/ — 작업 회고 (카테고리 인덱스)
updated: 2026-06-21
---

# lessons/

작업하면서 배운 것 + 결정의 trade-off. 아래 카테고리로 분류한다 — **파일은 평면 유지**(시점작업
4축 link 그래프 ralph↔audit↔lesson↔decision 보존), 분류는 이 인덱스에서만. **신규 lesson은 해당
카테고리에 한 줄 추가**하고, 가능하면 frontmatter `category:` 태그를 단다(향후 자동 인덱스 전환용).

각 페이지 schema: **Context**(왜) · **Did**(무엇) · **Improved**(나아진 것) · **Trade-off**(잃은 것) · **Takeaway**(반복할 원칙)

## ① 파서·파싱 정밀화
- [[agenda-relation-parser-260525]] — relation은 결론이 아니라 자동판단을 멈추는 guardrail, KOSPI300 regression 0
- [[shareholder-meeting-agenda-parse-260615]] — 주총 안건 파싱: 보수한도 단위·폴백 4종 + 큰샘플 진단→폴백→regression
- [[holder-table-parser-260615]] — 5% 대량보유 합계표 파서(본인 vs 특관) 140사
- [[acode-semantic-markers]] — DART 본문 ACODE → text regex 한계 돌파
- [[page-cut-detail-code-260609]] — 페이지컷 truncation → detail-code 좁히기

## ② tool 개선·신설·라이프사이클
- [[dividend-source-of-truth-260609]] — 배당 출처맵 + 누적 차분, 51사 정합 100%
- [[financial-metrics-precision-260612]] — 모델 hedge 역추적 → 412사 전수
- [[financial-metrics-evidence-fsdiv-260615]] — plausible-dismissal 경계 + evidence/CFS 폴백
- [[financial-metrics-account-id-260630]] — 순이익·ROE 오염(총포괄손익 오매칭) → account_id 매칭 + ROE 분모 지배자본 교정, 39사 구조검증
- [[order-contracts-260613]] — 수주 tool 신설, 같은 공시도 관점 다르면 다른 tool
- [[risk-events-pipeline-260611]] — 리스크 6종 통합 tool (I001+B001 채널)
- [[treasury-multitype-result-260617]] — 자사주 복수종류 우선주 누락 보정
- [[ownership-summary-integrity-260610]] — ownership 재설계 + 단위 오염, 450사
- [[contest-signals-500-260605]] — 경영권 분쟁 신호 다축화
- [[dispute-reverse-lookup-260607]] — 분쟁 역추적이 시총순보다 5배 효율
- [[tool-naming-discovery-260610]] — 이름·desc가 자연어 라우팅 좌우
- [[time-axis-tool-split]] — 사전/사후 분리로 fragility 격리
- [[scope-simplification]] — specialized scope 폐지로 라우팅 단순화
- [[render-output-audit-260616]] — render 출력 점검(데이터 OK 화면만 이상 3종)
- [[proxy-advise-perf-fact-260614]] — 성과는 절제·펀더멘털은 fact
- [[proxy-advise-stage2-parallel-260610]] — 2단계 조기발사 wall-clock 반증 → 롤백
- [[perf-timing-260524]] — stage timing 먼저, 의미 보존 범위 latency

## ③ 도메인·법령·의결권 판단
- [[law-layer-260508]] — 법령 layer 도입의 결정/검증 분리
- [[law-layer-precision-260508]] — 법령 정밀화 + parent pattern guard
- [[law-layer-body-260510]] — 제목 매칭 한계와 body fallback(회귀 위험 보류)
- [[director-faithfulness-260510]] — 사외이사 겸직/충실성 fact 노출
- [[classify-high-impact-260508]] — high-impact threshold + false positive 회피
- [[decision-tree-vs-matrix]] — 안건 결정 2방식(트리 vs 매트릭스)
- [[distribution-calibrated-thresholds]] — cutoff은 prior 직관이 아니라 audit 분포 본 후

## ④ 검증 방법론·측정 함정 ⭐ (재사용 핵심)
- [[agenda-parser-validation-260621]] — **측정 함정 5패턴 + 프로토콜**(html 픽스처 0콜·전수 diff·직접 표본·체크리스트)
- [[parser-precision-260508]] — 가정 vs 실측, source 한계 vs parser 한계 분리
- [[tool-coverage-audit-260612]] — 커버리지 2층위(파싱 성공률 vs 내용 정확도), baseline 없는 툴은 죽어도 모른다
- [[topdown-screening-feasibility-260617]] — 스크리닝 타당성(정보 충분, 막힌 건 효율뿐)

## ⑤ 인프라·아키텍처 원칙
- [[enrichment-as-infrastructure]] — facts/risk/citation = 검증 가능한 응답 인프라
- [[hard-rate-limit]] — DART 분당 1000회 hard rule 코드 강제
- [[decision-vs-raw-separation]] — decision logic은 안에서, raw expose는 밖으로
- [[ralph-threshold-realism]] — 데이터 자체 한계가 threshold 결정
- [[agenda-typed-status-audit-260615]] — parse_status 확대 불필요 결정 + 진단 시 production 경로 우회 금지

## ⑥ 초기·superseded (참고용 — 후속 lesson이 발전, 4축 link 그래프는 유지)
- [[parser-omnibus-260506]] · [[agenda-classification-260507]] · [[agenda-hierarchy-260510]] · [[subagenda-mapping-260510]] · [[career-parser-concat-260510]] — 초기 파서 탐색 (→ ① 의 후속이 발전)
- [[260510_daily-summary]] — 일일 작업 종합(개별 lesson에 흡수)
