---
type: lesson
title: tool 이름은 사용자 어휘로 — related_party_transaction → corporate_deals rename
context: 2026-06-10 사용자 "SK스퀘어가 최근 인수하거나 매각한 회사 알려줘" → 클라이언트 LLM이 tool을 못 찾음
date_learned: 2026-06-10
related: [scope-simplification, page-cut-detail-code-260609]
---

# tool 이름은 사용자 어휘로 — corporate_deals rename

## Context

사용자가 "SK스퀘어가 최근 인수하거나 매각한 회사 알려줘"를 물었는데 클라이언트(Claude)가
tool을 선택하지 못했다. 서버·배포는 정상이었고, 정답 tool(`related_party_transaction`
scope=`equity_deal`)도 데이터(취득 4/처분 3)를 잘 갖고 있었다. 실패 지점은 **라우팅(디스커버리)**.

## 진단 — 라우팅은 2단계, 실패는 1단계에서 났다

클라이언트 LLM의 tool 선택은 ① 어떤 tool인가(이름+desc로 후보 선정) → ② 인자를 뭘로
주나(schema로 scope 선택). 이번 실패는 ①:

1. **이름·desc에 사용자 어휘가 없었다.** 시스템은 "취득/처분·출자"로 쓰는데 사용자는
   "인수/매각"으로 묻는다. 같은 개념, 다른 단어 → 매칭 실패.
2. **이름(`related_party_transaction` 내부거래·일감몰아주기)이 기능보다 좁았다.** 실제
   기능의 절반(타법인주식 취득/처분 = 지분 딜 추적)이 이름에 안 보임. 단순 인수/매각
   질문엔 무관해 보여 후보 탈락.
3. **이웃 tool이 키워드를 선점.** `corporate_restructuring`이 desc에 "M&A"를 갖고 있어
   "인수"가 그쪽으로 새는데, 거긴 합병/분할/주식교환만 다뤄 지분 양수도는 없다 → 양쪽 다 빗나감.

## Did

- **분기 대신 rename.** scope를 여러 tool로 쪼개는 안은 기각 — 실패가 ①에서 났으므로
  tool 수를 늘려도(=① 후보만 늘어남) 원인이 안 고쳐지고, tool 16개의 "이름은 적게,
  scope로 분기" 기존 설계 방향(scope-simplification)과도 역행. desc 어휘만 있으면
  ②의 scope 선택은 LLM이 schema 보고 잘 한다(실측: equity_deal 자동 선택 확인).
- `related_party_transaction` → **`corporate_deals`** rename (서비스/스크립트 내부
  plumbing 포함 전면 통일, 기능·scope·파싱 변화 0).
- desc/when에 **사용자 어휘 보강**: "회사·지분 인수/매각", "어떤 회사를 인수했나/팔았나",
  "계열사 출자·회수", "투자 포트폴리오 재편". 일감몰아주기·내부거래·특수관계자 어휘는 유지.
- **상호 경계 문구**: corporate_deals에 "합병·분할·주식교환은 corporate_restructuring",
  restructuring에 "단순 지분 인수·매각(주식 양수도)은 corporate_deals" + ref 상호 링크.
- summarizer 스크립트는 과거 audit JSON 호환 위해 구/신 키 병기.

## Takeaway

- **tool 이름·desc는 사용자의 질문 어휘로 써라.** 공시 용어(취득/처분/양수도)는 rule:에,
  사용자 용어(인수/매각)는 desc/when에. 라우팅 LLM이 보는 건 이름과 desc뿐이다.
- **디스커버리 실패의 1차 수단은 desc 보강, 2차가 rename, 분기는 최후.** 싼 수단부터.
  분기는 desc 보강 후에도 같은 류 질의가 계속 빗나갈 때만 재검토.
- **이웃 tool과 키워드 충돌을 양방향 경계 문구로 해소하라.** 한쪽에만 쓰면 반대 방향
  질의가 또 샌다.
- **rename은 클라이언트 커넥터 재등록 전까지 안 보인다.** 배포 후 tool 목록 캐시 때문에
  재연결 안내가 필수 (README 참고 문구와 동일 케이스).

## Related commits

- (이 lesson과 함께 커밋)

## Related

- [[scope-simplification]] (tool 수 억제 + scope 분기 설계 방향)
- [[page-cut-detail-code-260609]] (narrowing 정확도 ≠ scope 포괄성 — 비슷한 "보이는 범위" 교훈)
