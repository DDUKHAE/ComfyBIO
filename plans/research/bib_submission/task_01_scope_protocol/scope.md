# BIB 연구 범위

- Protocol ID: `COMFYBIO-BIB-001`
- 버전: 1.0
- 결정일: 2026-06-22
- 목표 저널: **Briefings in Bioinformatics**
- 연구 형태: **구조화된 review + comparative benchmark + ComfyBIO case study**
- 상태: held-out 결과 확인 전 scope 고정

## 연구 Framing

본 연구는 ComfyBIO라는 새 소프트웨어만 소개하는 논문이 아니다. 자연어 또는 LLM 기반 생물정보학 workflow generation 접근을 구조적으로 정리하고, 공통 benchmark에서 비교하며, template-guided hybrid design을 하나의 재현 가능한 case study로 평가한다.

BIB 공식 정책상 standalone unpublished new method는 wider review 맥락 없이 제출하지 않는다. 따라서 원고에서 ComfyBIO 설명과 내부 실험이 전체 내용의 과반을 차지하지 않도록 한다.

## 잠정 제목

> Natural-language generation of executable bioinformatics workflows: a structured review, comparative benchmark, and template-guided case study

최종 제목은 Task 13에서 review coverage와 benchmark 결과를 반영해 확정한다. 결과가 나오기 전에 성능 우월성을 제목에 넣지 않는다.

## 연구 기여

1. **분야 구조화:** 자연어 기반 bioinformatics workflow generation 접근을 generation strategy, grounding, validation, execution, repair 및 evaluation으로 분류한다.
2. **평가 framework:** Structural validity, actual execution, expected-output correctness 및 expert semantic validity를 분리하는 benchmark를 제안한다.
3. **비교 근거:** 실행 가능한 외부 baseline과 free/normalized/hybrid ablation을 동일 조건에서 비교한다.
4. **실무 지침:** Workflow family, 난이도 및 실패 유형에 따라 적합한 접근과 한계를 제시한다.
5. **Case study:** ComfyBIO의 template-guided hybrid approach를 framework 적용 사례로 평가한다.

## Primary Claim

> Template grounding과 deterministic repair를 포함한 workflow-generation strategy는 free-form generation과 비교할 때 구조적 유효성뿐 아니라 expected-output-verified execution에서도 다른 failure profile을 보이며, 그 효과는 task family와 난이도에 따라 달라진다.

이 claim은 무조건적인 우월성을 전제하지 않는다. 방향, 크기 및 불확실성은 benchmark 결과에 따라 보고한다.

## 조건부 Claim

다음 claim은 paired analysis의 effect estimate와 95% confidence interval이 개선을 지지하고 blinded expert evaluation이 같은 방향일 때만 사용한다.

> Template-guided hybrid generation은 free-form generation보다 robust biological task execution을 향상시킨다.

## 연구 질문

### Review 질문

- RQ1: 자연어 기반 bioinformatics workflow generation에는 어떤 architecture와 grounding strategy가 사용되는가?
- RQ2: 기존 연구는 structural validity, executability 및 biological correctness를 어떻게 정의·평가하는가?
- RQ3: 현재 평가 관행에서 재현성, data leakage, provider drift 및 single-gold bias가 어떻게 처리되는가?

### Benchmark 질문

- RQ4: 외부 baseline과 ComfyBIO arm은 expected-output-verified execution에서 어떻게 다른가?
- RQ5: Free, normalized 및 hybrid arm의 차이는 normalization과 repair 기여를 어느 정도 설명하는가?
- RQ6: 성능과 failure taxonomy는 workflow family와 난이도에 따라 어떻게 달라지는가?
- RQ7: Automatic structural metric은 blinded expert semantic rating과 어느 정도 일치하는가?

### 실무 질문

- RQ8: 어떤 조건에서 free-form, constrained generation, retrieval/template grounding 또는 repair 전략을 선택해야 하는가?

## 대상 접근과 Baseline 범위

Task 2에서 다음 범주를 조사하고 registry를 고정한다.

- Free-form LLM workflow generation
- Structured-output 또는 schema-constrained generation
- Retrieval-augmented 또는 template-grounded generation
- Tool-calling/agentic bioinformatics assistant
- GUI 또는 visual workflow platform의 natural-language generation
- Repair/validation loop를 포함한 workflow generation

Primary quantitative benchmark에는 재현 가능하고 동일 과제를 수행할 수 있는 접근만 포함한다. 실행 불가능한 published method는 review와 qualitative comparison에는 포함하되 quantitative ranking에서 제외 사유를 기록한다.

외부 baseline이 2개 미만이면 BIB submission-ready로 판정하지 않는다. 다만 포괄적인 조사 결과 재현 가능한 외부 구현이 실제로 부족한 경우, 그 사실과 search evidence를 보고하고 editor pre-submission inquiry 여부를 검토한다.

## Workflow Family

Primary benchmark는 다음 12개 family를 유지한다.

1. `fasta_parse`
2. `pairwise_alignment`
3. `multiple_alignment`
4. `blast_search`
5. `searchio_analysis`
6. `phylogeny`
7. `annotation`
8. `pdb_structure_basic`
9. `motif_scan_basic`
10. `entrez_fetch`
11. `uniprot_lookup`
12. `kegg_pathway_basic`

Family 목록은 review에서 발견되는 실제 사용 사례와의 mapping을 Task 2에서 점검한다. Primary benchmark family 변경은 held-out query 작성 전에 amendment로만 허용한다.

## 대상 Query 모집단

- 영어 자연어 요청
- 소규모·중간 규모 Biopython task
- ComfyBIO node 또는 공정한 external baseline tool로 표현 가능
- Local fixture 또는 controlled cached response로 재현 가능
- Easy, medium, hard 및 adversarial 표현 포함

## 포함 Evidence

- 구조화된 literature/tool review
- Search log와 inclusion/exclusion 기록
- Baseline registry 및 reproducibility status
- 120개 held-out query
- 실제 biological data와 필요한 synthetic negative fixture
- Independent functional gold criteria
- Actual headless ComfyUI execution
- External baseline execution 또는 명시적 non-runnable 판정
- 반복 실행과 paired analysis
- Blinded expert review
- Failure taxonomy와 method-selection guidance
- 공개 가능한 raw data와 analysis package

## 제외 범위

- Clinical decision support 성능 claim
- Production-scale BLAST throughput benchmark
- Live API availability를 model quality로 해석하는 것
- 식물 육종·multimodal extension
- 비영어 query 일반화 claim
- 실제 실행 근거 없는 UI screenshot 중심 평가
- ComfyBIO에만 유리하도록 정의된 template-equivalence 단독 primary endpoint
- 결과 확인 후 baseline, query 또는 endpoint를 선택하는 것

## Generalization 경계

결과는 사전 지정된 12개 family, 영어 query, 선택된 provider/model, fixture 규모 및 실행 가능한 baseline에 한정된다. 임의의 omics pipeline, 대규모 workflow engine, clinical environment 또는 모든 LLM provider에 일반화하지 않는다.

## BIB 독자 가치

원고는 다음 실무 질문에 답해야 한다.

- 사용자는 어떤 generation strategy를 언제 선택해야 하는가?
- Schema-valid workflow가 실제로 실패하는 주된 이유는 무엇인가?
- Template grounding이 도움이 되는 task와 해가 되는 task는 무엇인가?
- Biological correctness를 자동으로 평가할 수 있는 범위는 어디까지인가?
- Provider drift가 있는 환경에서 benchmark를 어떻게 재현해야 하는가?

## Human Evaluation 범위

Expert review는 benchmark의 secondary evidence다. Reviewer 모집 전에 기관 ethics review/exemption 판단, consent, compensation, conflict, eligibility, blinding 및 adjudication을 문서화한다.

## 목표 저널 변경 규칙

BIB scope 부적합 또는 review/baseline gate 미충족 시에만 Bioinformatics Original Paper를 2차 목표로 검토한다. 저널 변경은 결과가 불리하다는 이유로 endpoint, query membership 또는 분석을 바꾸는 근거가 될 수 없다.

## Scope 완료 기준

- BIB 정책에 맞는 review + benchmark + case-study framing이 고정됨
- 연구 질문과 claim ladder가 고정됨
- Workflow family, 모집단, 제외 범위와 generalization 경계가 명시됨
- External baseline 및 review evidence가 필수 gate로 지정됨
- Human evaluation governance가 명시됨
- Held-out 결과 확인 전 protocol과 hash가 기록됨
