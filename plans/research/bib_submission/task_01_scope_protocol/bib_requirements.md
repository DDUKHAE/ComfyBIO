# BIB 공식 요건 및 프로젝트 매핑

- 확인일: 2026-06-22
- 목표 저널: Briefings in Bioinformatics
- 기준 문서: [공식 저자 지침](https://academic.oup.com/bib/pages/General_Instructions), [저널 소개](https://academic.oup.com/bib/pages/About)

## 공식 Scope 핵심

BIB는 contemporary biology, biotechnology 및 medicine의 data와 analytical tool을 이해하고 활용하려는 experimental practitioner에게 실용적이고 해석 가능한 지침을 제공하는 것을 목표로 한다.

포함 범위에는 genomics, proteomics, metabolomics, structural bioinformatics, systems biology, computational biology, clinical/medical informatics 및 AI/ML applications가 포함된다.

## 본 연구에 직접 적용되는 편집 정책

### Standalone 신방법 제한

공식 지침은 아직 다른 곳에 기술되지 않은 신방법만을 단독으로 다루는 논문을 출판하지 않으며, 해당 주제 분야의 더 넓은 review 맥락에서 제시할 것을 요구한다.

프로젝트 적용:

- ComfyBIO 자체를 논문 전체 기여로 제시하지 않는다.
- 자연어 기반 bioinformatics workflow generation의 기존 접근, tool selection, 한계 및 평가 관행을 구조적으로 review한다.
- ComfyBIO hybrid approach는 review에서 도출된 평가 framework를 적용하는 case study다.

### 관심 방법론

BIB는 다음 접근을 명시적 관심 분야로 제시한다.

- Software comparison and benchmarking
- Data cleaning and curation
- Predicted/extracted information의 accuracy
- Ontology와 text mining
- Biological data의 large-scale analysis
- Tool selection, limitation 및 result interpretation

프로젝트 적용:

- 논문의 중심을 reproducible comparative benchmark로 둔다.
- Structural validity뿐 아니라 actual execution과 biological task correctness를 평가한다.
- 단일 성능표가 아니라 failure taxonomy와 method-selection guidance를 제공한다.

### 독자 가치

기초 개념, 올바른 tool 선택, limitation 및 결과 해석을 비전문 독자도 이해할 수 있게 설명해야 한다.

프로젝트 적용:

- 자유 생성, normalization, template repair가 각각 어떤 상황에서 유효한지 설명한다.
- Workflow family·난이도·실패 유형별 권고안을 도출한다.
- 설치나 API 설명만 나열하지 않고 재현 가능한 선택 기준을 제공한다.

## 경쟁도와 지표

공식 지침과 저널 소개에 공개된 값:

- 연간 submission 2,000편 이상
- 출판 비율 25% 미만
- 2024 Journal Impact Factor: 7.7
- 2024 5-Year Impact Factor: 8.7
- 2025 CiteScore: 13.6
- Fully open access
- Single-anonymized peer review

높은 IF보다 scope 적합성과 broad interest가 우선이다. 단순 engineering integration은 desk reject 위험이 높다.

## AI 사용 공개

BIB는 AI를 저자로 인정하지 않는다. Content, image, code, data processing 또는 translation에 AI를 사용하면 cover letter와 Methods 또는 Acknowledgements에 공개해야 한다.

프로젝트 적용:

- LLM은 연구 대상이자 workflow generation algorithm의 구성요소로 명시한다.
- 문서 및 코드 작성 보조에 사용된 AI도 최종 원고의 정책에 맞게 공개한다.
- Human author가 모든 내용과 분석 결과를 검증한다.

## Data 및 Software 공개

- 결론을 뒷받침하는 data, code, benchmark와 analysis artifact를 가능한 범위에서 공개한다.
- Third-party data의 accession, license 및 redistribution 조건을 기록한다.
- Model/provider가 완전히 재현되지 않는 경우 raw response, exact date, reported model id와 configuration을 보존한다.

## BIB Submission-readiness Gate

다음을 모두 만족해야 BIB 제출 가능으로 판정한다.

1. 구조화된 review protocol과 재현 가능한 search log가 있다.
2. 관련 접근을 분류한 taxonomy와 baseline registry가 있다.
3. 최소 2개의 외부 실행 가능 baseline 또는 실행 불가 사유가 투명하게 정리된 comprehensive comparison이 있다.
4. 120개 held-out query와 12개 workflow family가 검증된다.
5. 실제 biological data fixture와 다단계 workflow가 포함된다.
6. Actual ComfyUI e2e execution과 expected-output verification이 있다.
7. Blinded expert review와 inter-rater agreement가 있다.
8. Method별 강점·한계·선택 지침이 도출된다.
9. Raw data, code, environment 및 analysis가 archive된다.
10. ComfyBIO를 standalone novelty가 아니라 review/benchmark case study로 일관되게 기술한다.

## 즉시 Reject Risk

- ComfyBIO 기능 소개가 원고 대부분을 차지함
- Wider review 없이 unpublished new method만 제시함
- External baseline 없이 free/normalized/hybrid 내부 비교만 수행함
- 실제 biological data 없이 synthetic prompt만 평가함
- JSON/schema validity를 biological correctness로 과장함
- 실패 사례와 limitation을 누락함
- Provider/model drift와 raw response를 기록하지 않음
- AI 사용을 공개하지 않음
