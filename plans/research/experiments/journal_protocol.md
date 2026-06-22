# 저널 벤치마크 프로토콜

- Protocol ID: `COMFYBIO-JOURNAL-001`
- 버전: 1.2
- 최초 freeze 일자: 2026-06-22
- 상태: **HELD-OUT 실행 전 FROZEN**
- Scope 문서: `docs/superpowers/experiments/journal_scope.md`
- Freeze manifest: `docs/superpowers/experiments/journal_protocol_freeze.json`
- 분석 모집단: 12개 workflow family에 걸친 schema-valid held-out query 120개
- Amendments: `COMFYBIO-JOURNAL-001-A001`, `COMFYBIO-JOURNAL-001-A002`

최종 artifact hash, 환경 버전 및 실행 시각과 같은 운영 필드는 실행 시점에 채운다. 가설, endpoint, benchmark membership, 제외 기준, retry 규칙 또는 분석 방법을 변경하려면 날짜가 기록된 amendment가 필요하다.

## 1. 목적

Template-guided hybrid 생성이 자연어 Biopython 워크플로우 과제에서 free-form LLM 생성보다 robust expected-output-verified ComfyUI 실행 성공을 향상시키는지 평가한다.

## 2. 가설

### Primary hypothesis

- Null: `hybrid`와 `free`의 robust execution success가 같다.
- Alternative: `hybrid`의 robust execution success가 `free`보다 높다.

설계 기대는 방향성을 가지지만, 원고에는 양측 95% confidence interval과 양측 primary test를 보고한다.

### Secondary hypothesis

- `normalized`는 `free`보다 schema/graph validity를 향상시킨다.
- `hybrid`는 `normalized`보다 robust execution success를 향상시킨다.
- `hybrid`는 `free`보다 blinded expert biological-validity rating을 향상시킨다.
- Template equivalence는 functional execution 및 expert correctness와 양의 관련성이 있지만 서로 대체 가능한 지표는 아니다.

Secondary hypothesis는 보조 근거이며 primary endpoint를 대체하지 않는다.

## 3. 실험 단위와 Pairing

- Benchmark unit: 고정된 fixture와 expected-output specification을 가진 held-out query 1개.
- Invocation unit: query × provider/model × mode × repeat 1회.
- Primary analysis pairing unit: 동일 provider/model과 동일 repeat 수로 `hybrid`와 `free`에서 평가한 동일 query.
- Primary provider/model: 현재 프로젝트에 기록된 최신 작동 설정인 `codex` / `gpt-5.5`.
- Deterministic provider: pipeline validation 전용이며 LLM effect estimate에서 제외.
- 추가 provider: 별도 secondary analysis로 보고.

Held-out invocation을 시작하기 전에 `gpt-5.5`를 사용할 수 없으면 readiness와 dev-set 근거만 사용하여 dated pre-run amendment로 대체 모델을 선택할 수 있다. Held-out outcome을 확인한 뒤에는 모델을 교체할 수 없다.

## 4. Benchmark 구성

Primary benchmark는 schema-valid held-out query 120개로 구성한다.

| 난이도 | Query 수 |
|---|---:|
| easy | 36 |
| medium | 48 |
| hard | 24 |
| adversarial | 12 |
| 합계 | 120 |

Coverage 규칙:

- 사전 지정된 12개 family가 각각 최소 2개 query를 가진다.
- Family imbalance와 그 근거를 실행 전에 기록한다.
- Supported request와 의도적인 unsupported/adversarial request를 명시적으로 표시한다.
- Query text를 dev query, template id, class name 및 template description과 비교하여 leakage와 near-duplication을 검사한다.
- 첫 held-out run 이후 benchmark record는 immutable로 유지한다. 입증된 data error를 수정할 경우 원본 record를 보존하는 amendment를 사용한다.

## 5. 표본 수 근거

Primary query-level comparison에는 paired binary robust-success label을 사용한다. Planning assumption은 다음과 같다.

- `hybrid`는 성공하고 `free`는 실패하는 query: 25%.
- `free`는 성공하고 `hybrid`는 실패하는 query: 10%.
- Discordant-pair difference: 15 percentage point.
- 양측 alpha: 0.05.
- 목표 power: 0.80.

표준 large-sample McNemar approximation은 다음과 같다.

```text
n = [z(0.975) * sqrt(p10 + p01)
     + z(0.80) * sqrt(p10 + p01 - (p10 - p01)^2)]^2
    / (p10 - p01)^2
```

`p10 = 0.25`, `p01 = 0.10`을 적용하면 evaluable paired query 약 120개가 필요하다. 따라서 120개는 임의의 정수가 아니라 power에 근거한 planning target이다.

모든 query record는 benchmark freeze 전에 schema 및 referential-integrity validation을 통과해야 한다. 관측 결과가 어렵거나 부정적이거나 `hybrid`에 불리하다는 이유로 query를 제거하지 않는다. Pre-run validation failure로 evaluable set이 120개 미만이 되면 held-out outcome을 보지 않은 상태에서 replacement query를 작성·freeze할 때까지 실행을 중단한다.

## 6. 실험 Arm

- `free`: deterministic normalization 또는 template-guided repair를 적용하지 않은 raw LLM workflow spec.
- `normalized`: template-guided repair 없이 deterministic normalization만 적용.
- `hybrid`: normalization 후 template-guided local repair 적용.

Primary contrast: `hybrid - free`.

Secondary contrast:

- `normalized - free`
- `hybrid - normalized`

모든 mode에 동일한 prompt goal, fixture, provider/model 및 사용 가능한 decoding configuration을 적용한다. 방법 자체에 포함된 mode-specific context는 intervention의 일부로 문서화한다.

## 7. 반복 실행과 Randomization

- 각 LLM query/mode combination을 5회 실행한다.
- Query × mode × repeat invocation 순서를 randomize한다.
- 실행 전에 생성한 randomization manifest와 seed를 저장한다.
- Temperature, top-p, provider seed, CLI version, system/developer prompt 및 model-reported id를 사용 가능한 범위에서 기록한다.
- 제어할 수 없는 provider setting은 추정하지 않고 `unavailable`로 기록한다.
- Concurrency가 provider throttling 또는 shared application state에 영향을 줄 수 있으면 run을 병렬화하지 않는다.

## 8. Primary Endpoint

### Invocation-level success

다음 조건을 모두 만족해야 invocation success로 판정한다.

1. Final workflow spec이 존재한다.
2. Schema 및 graph validation을 통과한다.
3. ComfyUI workflow JSON 변환에 성공한다.
4. Server가 prompt를 수락한다.
5. Node/runtime error 없이 실행을 완료한다.
6. 사전 지정된 expected-output criteria를 모두 통과한다.

`workflow_json`이 존재하는 것만으로는 execution success가 아니다.

### Query-level robust success

5회 invocation 중 4회 이상 invocation-level endpoint를 만족하면 해당 query와 mode를 robust success로 판정한다.

Primary endpoint는 120개 query에서 `hybrid`와 `free` 사이 query-level robust-success proportion의 paired difference다.

## 9. Secondary Endpoint

- Valid JSON rate
- Schema-valid rate
- Graph-valid rate
- Workflow JSON conversion rate
- ComfyUI loadable rate
- Prompt acceptance rate
- Execution completion rate
- Expected-output match rate
- Functional gold-criteria pass rate
- Blinded expert task relevance, biological validity, executable usefulness, correction burden 및 critical-error rate
- Template match rate
- Equivalence score
- Repair frequency 및 action taxonomy
- Latency
- Failure taxonomy

현재 `workflow_experiments.py`의 legacy `executable_workflow_rate`는 verified execution이 아니라 `workflow_json` 존재 여부를 측정하므로 endpoint로 사용하지 않는다.

## 10. Functional Ground Truth

각 query에 대해 독립적으로 검토된 criteria가 다음을 정의한다.

- Input fixture와 format
- 필수 biological operation
- 허용 가능한 output property
- Tolerance 또는 contains-match rule
- Critical semantic error
- 허용 가능한 workflow alternative

Canonical template은 구현에 참고할 수 있지만 유일한 ground truth로 사용하지 않는다. Template equivalence는 structural secondary metric으로 유지한다.

## 11. 제외 규칙

### 실행 전 Query-level exclusion

Held-out 실행 전에 다음 사유로만 query를 제외하거나 교체할 수 있다.

- Schema failure
- 깨진 fixture 또는 expected-output reference
- 고정된 leakage threshold를 넘는 duplicate/near-duplicate
- 사전 지정 family 또는 node capability 밖의 task
- Fixture redistribution 또는 licensing failure

### 금지된 제외

다음 사유로 query 또는 invocation을 제외하지 않는다.

- Provider/model failure
- Invalid JSON
- Wrong intent/template
- Low equivalence
- Runtime failure
- Semantic failure
- `hybrid`에 불리한 outcome

모든 exclusion과 replacement는 original id와 audit entry를 보존한다.

## 12. Provider Failure 및 Retry 정책

- Randomized benchmark 시작 전에 readiness check를 실행한다.
- 명확한 transient timeout, connection interruption 또는 provider 5xx error에 대해서만 invocation당 최대 1회 retry한다.
- Retry에는 동일한 query, mode, model 및 사용 가능한 decoding setting을 적용한다.
- 최초 attempt와 retry 및 retry reason을 모두 보존한다.
- Authentication, quota, session limit, missing model 또는 missing CLI error는 provider operational failure로 분류하고 benchmark 안에서 반복 retry하지 않는다.
- 생성된 workflow를 수동으로 수정하지 않는다.

Primary intention-to-evaluate analysis에서는 해결되지 않은 provider operational failure를 failure로 계산한다. Per-protocol sensitivity analysis에서는 사전 지정된 provider operational failure를 제외하고 변경된 denominator를 보고한다.

## 13. 통계 분석

### Primary analysis

- `hybrid`와 `free`에 대해 paired query-level robust-success label을 생성한다.
- 각 mode proportion, paired percentage-point difference, discordant-pair count, exact McNemar p-value 및 paired difference의 95% confidence interval을 보고한다.
- Statistical significance는 양측 alpha 0.05를 사용한다.
- P-value보다 effect estimate와 confidence interval을 우선 해석한다.

### Sensitivity analysis

- Mode를 fixed effect, query를 random intercept로 둔 invocation-level mixed-effects logistic regression.
- Robust-success threshold 3/5 및 5/5.
- Provider failure에 대한 intention-to-evaluate와 per-protocol 비교.
- Supported-only와 supported plus adversarial query 비교.
- Primary provider-only와 별도 보고되는 additional provider 비교.

### Secondary analysis

- Continuous metric에 대한 paired bootstrap confidence interval.
- Expert rating에 대한 ordinal 또는 mixed-effects model.
- Family 및 difficulty subgroup estimate와 confidence interval.
- Confirmatory secondary comparison family 안에서 Holm correction.
- 그 외 모든 비교는 exploratory analysis로 명시.

모든 표에 missingness, denominator, software package, version 및 analysis code를 기록한다.

## 14. 전문가 평가 프로토콜

- 자격을 갖춘 reviewer 3명 이상이 사전 지정된 stratified random sample을 독립적으로 평가한다.
- Planning minimum은 query 50개이며 세 mode를 모두 포함한다.
- Mode, provider, file order 및 internal method metadata를 blind 처리한다.
- 가능한 경우 동일 query의 여러 mode output이 presentation order에서 연속하지 않게 한다.
- 모든 reviewer가 shared core subset을 평가하고 나머지는 balanced block으로 배정한다.
- Ordinal endpoint에는 weighted kappa 또는 Krippendorff alpha를 사용한다.
- Binary critical-error rating에는 Fleiss kappa 또는 Krippendorff alpha와 percent agreement를 함께 사용한다.
- Agreement estimate에는 95% bootstrap confidence interval을 포함한다.
- Independent raw rating은 adjudicated label과 분리하여 보존한다.

기관의 ethics review/exemption requirement, reviewer information/consent, compensation 및 conflict를 문서화하기 전에는 rating 수집을 시작하지 않는다.

## 15. Blinding

- Reviewer에게 randomized opaque artifact id를 제공한다.
- Review artifact에서 mode/provider/template/repair metadata를 제거한다.
- Analyst는 automated analysis를 위해 mode label을 알 수 있지만 expert result unblinding 전에 script와 endpoint rule을 고정한다.
- Blinding failure를 기록하고 affected rating은 조용히 삭제하지 않고 dated amendment에 따라 처리한다.

## 16. Raw Data 및 Provenance

각 invocation record는 다음을 포함한다.

- Protocol/version 및 run id
- Query, fixture, expected-output 및 gold-spec id
- Provider, model, CLI version, decoding setting 및 run index
- Timestamp 및 randomization position
- Raw, normalized 및 final spec
- Converted workflow JSON
- ComfyUI 및 node-package version
- 각 e2e stage의 status
- Stdout/stderr 또는 artifact path
- Output, expected-output result, error taxonomy 및 retry count
- Source 및 generated artifact의 SHA-256

Raw record는 append-only로 관리한다. 표와 그림은 versioned script로 생성한다.

## 17. Quality Gate

다음 상황에서는 held-out 실행을 중단한다.

- Schema 또는 referential-integrity validation 실패
- Gold lint 실패
- Positive-control e2e execution 불안정
- Provider operational failure가 run manifest에 지정된 threshold를 초과
- Randomization 또는 provenance artifact 누락
- Reviewer blinding 또는 assignment 파손

Hybrid effect 또는 execution rate가 낮은 것은 중단 조건이 아니다.

Provider operational-failure threshold는 첫 complete randomized block에서 scheduled invocation의 10%로 고정한다. 이를 초과하면 operational diagnosis를 위해 새 호출을 중단하며 기존 수집 data는 immutable로 유지한다.

## 18. 재현성 요건

원고 제출 전에 다음을 archive한다.

- Code commit 및 release tag
- Benchmark, schema, fixture, expected output 및 gold criteria
- Raw run record 및 hash
- Analysis script와 생성된 table/figure
- Dependency lockfile 또는 container image digest
- ComfyUI, Biopython, CLI, provider/model, OS, locale, timezone 및 hardware metadata
- 공개 제한을 명시한 system/developer prompt 및 template snapshot
- License, `CITATION.cff`, data/software availability statement 및 가능한 경우 archival DOI

## 19. Freeze 및 Amendment 절차

이 버전은 `journal_query_set_v1`의 held-out 실행 전에 freeze한다.

Amendment에는 다음을 포함한다.

- Amendment id 및 날짜
- 정확한 old/new text
- 변경 이유
- Held-out outcome 확인 여부
- 영향받는 record 및 analysis
- Author approval

Held-out outcome을 확인한 뒤에는 primary endpoint를 재정의하거나 failure를 제거하거나 primary contrast를 변경하거나 불리한 성능을 이유로 모델을 교체할 수 없다. 모든 deviation을 원고와 submission-readiness audit에 보고한다.

## 20. Task 1 완료 기록

이 protocol과 `journal_scope.md`의 hash를 held-out 실행 전에 기록하면 Task 1 내용이 완료된다. 다음 허용 작업은 Task 2 benchmark schema 설계이며 journal benchmark 실행은 아직 허용되지 않는다.
