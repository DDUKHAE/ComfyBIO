# BIB 연구 프로토콜

- Protocol ID: `COMFYBIO-BIB-001`
- 버전: 1.0
- Freeze 일자: 2026-06-22
- 목표 저널: Briefings in Bioinformatics
- 상태: **TASK 1 FROZEN / HELD-OUT 실행 금지**
- Scope: `scope.md`
- BIB 요건: `bib_requirements.md`

Task 2에서 review search와 baseline registry를 고정하기 전에는 held-out query 작성과 benchmark 실행을 허용하지 않는다. Baseline 이름은 아직 미정이지만 selection rule은 본 protocol에서 고정한다.

## 1. 연구 설계

본 연구는 다음 세 구성요소를 결합한다.

1. 자연어 기반 bioinformatics workflow generation의 structured review
2. 공통 과제를 이용한 reproducible comparative benchmark
3. ComfyBIO template-guided hybrid approach의 case study와 ablation

ComfyBIO는 review 없이 standalone unpublished method로 제시하지 않는다.

## 2. Review Protocol 개요

Task 2에서 상세 search protocol을 작성하되 다음 원칙은 변경하지 않는다.

- Review question과 eligibility를 search 결과 확인 전에 고정한다.
- Database, query string, 검색일, result count 및 deduplication을 기록한다.
- Paper뿐 아니라 공개 software/tool과 benchmark를 연결한다.
- Inclusion/exclusion은 최소 2단계 title/abstract 및 full-text screening으로 수행한다.
- 단일 reviewer인 경우 limitation을 명시하고 재검토 sample을 둔다.
- Systematic review 요건을 완전히 충족하지 않으면 systematic이라는 용어를 사용하지 않고 structured review로 보고한다.
- Search 결과와 screening decision을 공개 가능한 범위에서 archive한다.

## 3. Review Eligibility

### 포함

- Natural language 또는 LLM을 사용해 bioinformatics analysis/workflow/tool sequence를 생성하거나 실행하는 연구
- General workflow-generation 방법이 biological task에서 평가된 연구
- Structured output, retrieval, template grounding, tool calling, validation 또는 repair를 다루는 연구
- 실행 가능한 software, code, API 또는 충분한 algorithm description을 제공하는 연구
- Workflow correctness, execution 또는 biological task success를 평가하는 benchmark 연구

### 제외

- Workflow generation 없이 문헌 질의응답만 수행
- Bioinformatics와 연결되지 않은 일반 coding agent만 평가
- Method·data·evaluation 설명이 없는 commentary
- 중복 publication
- 원문이나 충분한 technical detail을 확보할 수 없음

Review에는 qualitative evidence로 포함할 수 있지만 quantitative benchmark에는 실행 가능성과 task compatibility가 추가로 필요하다.

## 4. Baseline Selection Rule

Quantitative baseline은 다음을 모두 만족해야 한다.

- 공개적으로 접근 가능한 구현 또는 재현 가능한 API/CLI
- 사전 지정 query 중 의미 있는 subset 수행 가능
- 입력과 output을 저장할 수 있음
- License 및 사용 조건 기록 가능
- 평가 시점의 version/model/configuration 고정 또는 기록 가능
- 수동 workflow 수정 없이 결과 평가 가능

우선 범주:

1. Free-form direct LLM generation
2. Schema-constrained/structured generation
3. Retrieval/template-grounded generation
4. Tool-calling 또는 agentic bioinformatics assistant
5. Validation/repair loop를 포함한 generation

최소 2개 external baseline을 목표로 한다. 충족하지 못하면 search evidence와 실행 불가 사유를 보고하고 BIB readiness를 재평가한다.

## 5. Benchmark 모집단

- Schema-valid held-out query 120개
- 12개 workflow family
- Easy 36, medium 48, hard 24, adversarial 12
- 실제 biological fixture를 사용하는 supported task
- 안전한 거부 또는 limitation 판단을 평가하는 unsupported/adversarial task

Query 작성자는 가능한 한 system developer와 분리한다. 불가능하면 `author_written_heldout`으로 명시하고 independent review를 추가한다.

## 6. 표본 수 근거

Primary paired contrast는 ComfyBIO `hybrid`와 `free`의 query-level robust success 차이다.

Planning assumption:

- Hybrid success/free failure: 25%
- Free success/hybrid failure: 10%
- Discordant difference: 15 percentage point
- Two-sided alpha: 0.05
- Power: 0.80

Large-sample McNemar approximation에서 약 120 paired query가 필요하다. External baseline comparison은 baseline coverage에 따라 denominator가 달라질 수 있으므로 effect estimate와 confidence interval을 우선하고 coverage를 별도로 보고한다.

## 7. 실험 Arm

### ComfyBIO case-study arm

- `free`: raw LLM generation
- `normalized`: deterministic normalization
- `hybrid`: normalization + template-guided repair

### External baseline arm

Task 2 registry에서 selection rule을 만족한 방법. 각 baseline의 native workflow representation을 유지하되 공통 functional endpoint로 평가한다.

Template equivalence는 ComfyBIO 내부 structural metric이며 외부 baseline의 primary 비교 지표로 사용하지 않는다.

## 8. Provider와 Model

ComfyBIO primary provider/model은 held-out 실행 전에 readiness evidence로 고정한다. 기존 기록의 `codex/gpt-5.5`는 후보이며 자동 확정하지 않는다.

고정 규칙:

- Exact provider, reported model id, CLI/API version 및 날짜 기록
- Temperature/top-p/seed를 제어할 수 있으면 고정
- 제어 불가능한 값은 `unavailable`로 기록
- Held-out outcome 확인 후 model 교체 금지
- 추가 model/provider는 secondary generalization analysis

## 9. 반복과 Randomization

- LLM 기반 query/method combination당 5회 반복
- Query × method × repeat 순서 randomization
- Randomization seed와 manifest를 실행 전에 저장
- Shared state 또는 throttling이 영향을 줄 수 있으면 병렬 실행 금지
- 모든 attempt와 retry를 raw record에 보존

## 10. Primary Endpoint

### Invocation-level expected-output-verified execution success

다음을 모두 만족해야 한다.

1. Workflow/spec 생성
2. Method-specific schema/structure validation 통과
3. 실행 가능한 workflow 또는 tool plan 변환
4. Runtime가 job을 수락
5. Error 없이 완료
6. 사전 지정 expected-output criteria 통과

### Query-level robust success

5회 중 4회 이상 invocation-level success이면 robust success로 판정한다.

Primary confirmatory contrast는 `hybrid - free`의 paired robust-success proportion difference다.

## 11. Secondary Endpoint

- Valid structured output rate
- Graph/schema validity
- Runtime acceptance 및 completion
- Expected-output match
- Functional gold-criteria pass
- Blinded expert biological validity
- Manual correction burden
- Critical semantic error
- Latency 및 token/cost when available
- Repair frequency
- Failure taxonomy
- Method coverage: 전체 query 중 실행 가능한 비율
- Review에서 보고된 evaluation practice와 실제 benchmark 결과의 gap

## 12. Ground Truth

Template을 복사한 single gold를 사용하지 않는다. 각 query는 다음을 포함한다.

- Input fixture
- 필수 biological operation
- 허용 output property
- Tolerance/contains rule
- Critical semantic error
- Acceptable alternative workflow

Independent reviewer가 functional criteria를 승인한다. Template equivalence는 secondary metric이다.

## 13. 제외 및 Missingness

### 실행 전 제외 가능

- Schema/reference failure
- Duplicate 또는 leakage threshold 초과
- License/redistribution 문제
- 사전 지정 scope 밖 task
- 깨진 fixture

### 결과 확인 후 제외 금지

- Invalid output
- Runtime failure
- Wrong intent/tool
- Semantic error
- Low score
- Hybrid 또는 특정 baseline에 불리한 결과

Baseline이 일부 family를 지원하지 않으면 실패와 미지원 상태를 구분해 coverage를 보고한다. 공통 supported subset analysis와 all-query intention-to-evaluate analysis를 모두 제공한다.

## 14. Retry 및 Operational Failure

- Readiness check 후 randomized run 시작
- Transient timeout, connection interruption 또는 5xx만 동일 설정으로 최대 1회 retry
- Auth, quota, session limit, missing model/CLI는 operational failure
- 두 attempt와 reason 모두 보존
- Unresolved operational failure는 intention-to-evaluate에서 failure
- Per-protocol sensitivity analysis에서 사전 정의된 operational failure 제외

## 15. 통계 분석

### Primary

- Hybrid와 free의 paired robust-success label
- 각 proportion, paired difference, discordant count, exact McNemar p-value, 95% CI
- Two-sided alpha 0.05
- Effect size와 CI 우선 해석

### External baseline

- Coverage-adjusted 및 all-query 결과를 별도 보고
- Pairing 가능한 query에서 paired difference와 bootstrap CI
- Multiple baseline comparison은 Holm correction
- 실행 범위가 다른 방법을 단일 순위로 과도하게 단순화하지 않음

### Sensitivity

- Invocation-level mixed-effects logistic model
- Robust threshold 3/5 및 5/5
- ITT versus per-protocol operational failure
- Supported-only versus adversarial 포함
- Family/difficulty subgroup

### Review-benchmark synthesis

Review에서 주장된 장점·평가 지표와 benchmark 관측 결과를 evidence table로 연결한다. Meta-analysis는 outcome이 충분히 동질적인 경우에만 수행한다.

## 16. Expert Review

- Reviewer 3명 이상
- 사전 지정 stratified sample 최소 50 query
- Method/provider metadata blind
- Shared core subset + balanced block
- Ordinal rating: weighted kappa 또는 Krippendorff alpha
- Binary critical error: Fleiss kappa 또는 Krippendorff alpha + percent agreement
- 95% bootstrap CI
- Raw independent rating과 adjudicated label 분리

기관 ethics review/exemption, consent, compensation 및 conflict 문서화 전에는 rating을 수집하지 않는다.

## 17. Raw Data와 Reproducibility

각 invocation에 다음을 저장한다.

- Protocol/method/query/run id
- Provider/model/version/configuration
- Raw response와 parsed/final workflow
- Runtime stage별 status
- Input/output/error/retry
- Timestamp/randomization position
- Source 및 generated artifact SHA-256

Review에는 search string, database, date, screening decision 및 baseline reproducibility status를 저장한다.

## 18. Quality Gate

다음이면 다음 단계로 진행하지 않는다.

- Review search protocol 미고정
- Baseline registry와 selection evidence 없음
- Query schema/reference validation 실패
- Positive-control execution 불안정
- Raw/provenance/randomization 누락
- Reviewer blinding 파손

낮은 hybrid 성능 또는 negative result는 중단 조건이 아니다.

## 19. BIB Submission Gate

- Wider review가 ComfyBIO 설명보다 충분히 넓음
- External baseline 비교 또는 포괄적 non-runnable evidence 존재
- 실제 biological data와 다단계 workflow 포함
- Functional execution과 expert correctness 보고
- Method-selection guidance 도출
- AI 사용, limitation, data/code availability 공개
- Archive와 independent rerun 완료

Gate 미충족 시 Bioinformatics Original Paper 또는 Bioinformatics Advances로 scope를 재평가하되 결과와 endpoint는 변경하지 않는다.

## 20. Freeze와 Amendment

Task 1 문서 hash를 `freeze_manifest.json`에 기록한다. 이후 변경은 `amendments/` 또는 Task 1 폴더의 dated amendment로 관리한다.

Task 2에서 baseline 이름과 review search string을 확정하는 것은 본 protocol이 예정한 operational completion이다. Selection rule, endpoint 또는 exclusion을 바꾸면 substantive amendment다.

## 21. 다음 허용 작업

Task 2 `review_baselines`만 허용한다. Task 3 schema 또는 held-out query 작성으로 건너뛰지 않는다.
