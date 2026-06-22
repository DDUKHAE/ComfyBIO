# Journal Data Package Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Use superpowers:subagent-driven-development only for implementation-heavy subtasks such as adding new benchmark runners or ComfyUI e2e automation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI/Bioinformatics 관련 저널 제출을 위해 `ComfyBIO Biopython`의 워크플로우 생성 성능을 held-out 데이터셋, independently reviewed functional gold criteria, 실제 생물정보 입력 파일, ablation, ComfyUI end-to-end 실행, 전문가 평가로 검증하는 재현 가능한 데이터 패키지를 구축한다.

**Target claim:** 자연어 goal에서 Biopython/ComfyUI workflow를 생성하는 hybrid workflow generation 방식이 free generation보다 구조적 유효성, template equivalence, 실행 가능성, 의미 정확성에서 더 안정적이다.

**Architecture:** 기존 `free / normalized / hybrid` 실험 계층과 template registry를 유지하되, 현재 runner의 journal schema 처리, raw record 보존, 실제 ComfyUI e2e 채점 공백을 보완한다. benchmark 데이터, fixture, independently reviewed functional gold criteria, 실행 리포트, 전문가 평가표와 재현성 패키지를 versioned pipeline으로 연결한다.

**Tech Stack:** JSON/JSONL benchmark data, small bioinformatics fixture files, canonical workflow specs, existing Python experiment runner, pytest, headless ComfyUI `/prompt` execution, Markdown reports.

**Documentation language:** 생성되는 연구 문서와 보고서는 한국어를 기본으로 작성한다. 코드 식별자, 파일 경로, 공식 지표명 및 인용 제목은 정확성을 위해 원문을 유지할 수 있다.

## 변경 전후 비교

아래에는 교체되거나 추가된 핵심 내용을 `기존:`과 `chanege:` 쌍으로 보존한다.

### 1. 목표와 구현 범위

기존:
> **Goal:** AI/Bioinformatics 관련 저널 제출을 위해 `ComfyBIO Biopython`의 워크플로우 생성 성능을 독립 데이터셋, gold workflow, 실제 생물정보 입력 파일, ablation, ComfyUI end-to-end 실행, 전문가 평가로 입증하는 재현 가능한 데이터 패키지를 구축한다.
>
> **Architecture:** 기존 `free / normalized / hybrid` 실험 계층, `workflow_guidance/templates`, `workflow_experiments.py`, `workflow_history.jsonl`를 유지한다. 새 작업은 주로 benchmark 데이터, fixture 데이터, gold workflow, 실행 리포트, 전문가 평가표, 재현성 패키지에 집중한다. 코드 변경은 필요한 자동화가 확인될 때만 수행한다.
>
> **Tech Stack:** JSON/JSONL benchmark data, small bioinformatics fixture files, canonical workflow specs, existing Python experiment runner, pytest, optional headless ComfyUI `/prompt` execution, Markdown reports.

chanege:
> **Goal:** 독립성이 입증되지 않은 author-written set은 `independent`가 아니라 `held-out`으로 표현하고, independently reviewed functional gold criteria로 검증한다.
>
> **Architecture:** 현재 runner의 journal schema, raw record 보존, 실제 ComfyUI e2e 채점 공백을 보완하는 코드 작업을 명시한다.
>
> **Tech Stack:** 실제 실행이 primary endpoint이므로 headless ComfyUI 실행을 optional에서 필수로 변경한다.

### 2. 기존 실행 지표 해석

기존:
> Recorded smoke comparison은 small set 기준이며, provider 상태 제약이 있고 실제 `executable_workflow_rate`가 논문 주장에 충분하지 않다.
>
> 기존 runner가 `acceptable_template_ids` 같은 새 필드를 무시해도 실행은 가능해야 한다. 정밀 채점이 필요할 때만 새 scorer를 추가한다.

chanege:
> 현재 `executable_workflow_rate`는 실제 ComfyUI 실행이 아니라 `workflow_json` 존재 여부를 집계하며, runner는 그 필드도 채우지 않는다. 기존 수치를 runtime/e2e 증거로 재사용하지 않는다.
>
> journal schema adapter, raw result writer, 실제 e2e scorer 구현을 본실험 전 필수 작업으로 둔다. 기존 지표는 `workflow_json_present_rate`로 이름을 바꾸거나 deprecated 처리한다.

### 3. 제출 프로토콜과 데이터 검증

기존:
> 처음에는 Markdown + JSON 수동 검토로 충분하다. query set이 100개를 넘으면 작은 Python validator를 추가한다.

chanege:
> 첫 seed set부터 machine-readable schema, referential-integrity validator와 pytest를 사용한다.
>
> target venue checklist, frozen protocol/statistical analysis plan, immutable raw records, environment lock, citation/archive metadata를 필수 산출물로 추가한다.

### 4. 평가셋 규모와 독립성

기존:
> full set 120개로 확장한다.
>
> easy 36개, medium 48개, hard 24개, adversarial 12개로 고정한다.
>
> query 작성 후에는 classifier 튜닝에 사용하지 않는다.

chanege:
> 120개는 planning target으로만 두고 pilot의 paired discordance 또는 최소 검출 효과에 근거해 표본 수를 정한다. 기존 난이도 분포는 120개를 유지할 때의 권장안으로 보존한다.
>
> 시스템 개발에 참여하지 않은 작성자를 우선하며 dev prompt/template과의 exact·near-duplicate를 자동 검사한다. author-written-only set이면 `independent`가 아니라 `held-out`이라고 보고한다.

### 5. Gold workflow의 순환 검증 방지

기존:
> template별 canonical gold workflow 1개씩 작성한다.
>
> 각 gold workflow는 기존 `workflow_guidance/templates/*.json`와 `node_registry.json`의 class/port 이름을 따른다.

chanege:
> 입력, 허용 출력, 필수 생물학 연산과 critical-error 조건으로 independent functional gold spec을 먼저 작성한다. 기존 template을 그대로 복사하거나 유일한 정답으로 사용하지 않는다.
>
> 작성자·검토자·근거 문서를 기록하고 independent reviewer가 acceptable alternatives를 승인한다. template equivalence는 secondary metric으로만 사용한다.

### 6. 실험 반복, endpoint와 통계

기존:
> deterministic은 1회, LLM provider는 최소 3회, 가능하면 5회 반복한다.
>
> Primary: semantic correctness, actual execution success rate, equivalence score.
>
> Secondary: valid JSON rate, template match rate, repair frequency, inter-model agreement, runtime latency.

chanege:
> deterministic은 pipeline validation에만 사용한다. LLM repeat는 pilot variance로 정하고 실행 순서와 seed를 기록한다.
>
> Primary endpoint는 하나만 사전 지정하며 `expected-output-verified ComfyUI execution success`를 권장한다. expert correctness, functional gold pass와 equivalence는 secondary로 분리한다.
>
> paired McNemar 또는 mixed-effects model, paired bootstrap CI, 95% CI, multiple-comparison 처리와 sensitivity analysis를 본실험 전에 고정한다.

### 7. ComfyUI e2e 범위

기존:
> e2e runner는 optional이다.
>
> 처음에는 12개 family마다 1개씩 총 12개만 e2e로 검증한다. 안정화 후 50개 이상으로 확장한다.

chanege:
> e2e runner를 필수 산출물로 둔다. 12개는 harness pilot으로만 사용한다.
>
> actual execution이 primary endpoint이면 모든 eligible query 또는 sample-size calculation으로 정한 stratified subset을 실행한다. 12개 pilot 수치를 primary 결과로 사용하지 않는다.

### 8. 전문가 평가

기존:
> 50개 query를 mode별 blind 처리하고 reviewer 3명 이상에게 평가를 요청한다.
>
> 최소 Cohen/Fleiss kappa 또는 percent agreement를 보고한다.

chanege:
> 50개는 planning minimum으로 두고 사전 정의된 stratified random sample을 사용한다. mode/provider와 순서를 blind 처리하고 동일 query의 mode 결과가 연속 노출되지 않게 배치한다.
>
> ordinal rating에는 weighted kappa 또는 Krippendorff alpha, binary error에는 Fleiss kappa/alpha와 percent agreement를 사용하며 95% CI와 adjudication 규칙을 추가한다.
>
> reviewer eligibility, instruction version, 동의·보상·이해상충과 기관 윤리 검토/면제 필요 여부를 기록한다.

### 9. 원시 데이터, 분석과 재현성

기존:
> Markdown mode/provider comparison report, 결과표와 reproducibility manifest를 생성한다.

chanege:
> 각 invocation의 raw/final spec, workflow JSON, 설정, 시간, 오류와 artifact hash를 immutable JSONL로 먼저 저장한다. Markdown report만 있는 실행은 본실험으로 인정하지 않는다.
>
> 모든 주요 결과에 denominator, paired effect size와 95% CI를 포함하고 sensitivity table을 생성한다.
>
> dependency lock/container digest, randomization seed, prompt/template snapshot, clean-environment 재실행, license, `CITATION.cff`, data availability와 archival DOI 준비를 추가한다.

### 10. 제출 판단 기준

기존:
> Go 기준: full benchmark가 재현 가능하고, e2e subset이 의미 있는 성공률을 보이며, expert evaluation에서 hybrid가 free보다 명확히 나아야 한다.
>
> Stop condition: hybrid가 free보다 개선되지 않거나 ComfyUI e2e 성공률이 50% 미만이면 실험을 중단한다.

chanege:
> 결과 방향과 무관하게 frozen protocol의 분석, raw evidence, effect estimate와 95% CI, blind expert agreement, archive와 journal checklist가 완료되면 submission-ready로 판단한다.
>
> hybrid가 개선되지 않거나 성공률이 낮은 것은 중단 조건이 아니라 보고할 결과다. schema 오류, e2e positive-control 실패, blinding 파손, provenance 누락처럼 측정 체계가 무효일 때만 pause한다.

### 11. 일정과 최소 제출 패키지

기존:
> 5주 일정이며 최소 패키지는 120개 독립 query, 12개 gold workflow/fixture, deterministic + one LLM, 30개 e2e, 50개 expert review와 manifest다.

chanege:
> protocol/schema, runner/e2e 보강, frozen full run, blinded review, independent rerun과 archive를 분리한 6주 일정으로 변경한다.
>
> 최소 패키지에 sample-size rationale, independent functional gold criteria, validator/checksum, randomized paired runs, powered/전수 e2e, agreement, immutable raw records, environment lock, license/citation/data availability와 archival release를 포함한다.

---

## Review Verdict (2026-06-22)

이 계획의 데이터셋, fixture, gold workflow, e2e, 전문가 평가 방향은 적절하다. 다만 원안 그대로는 exploratory engineering benchmark에는 충분해도 peer-reviewed journal submission protocol로는 부족하다. 아래 수정본은 다음 reject risk를 명시적으로 통제한다.

- 기존 runner의 `executable_workflow_rate`는 실제 ComfyUI 실행이 아니라 `workflow_json` 존재 여부를 집계한다. 이 값을 runtime/e2e 성공률로 해석하지 않는다.
- 기존 template에서 직접 만든 gold workflow로 같은 template equivalence를 평가하면 순환 검증이 된다. 독립적인 기능 요구사항과 expert-authored reference를 primary ground truth로 사용한다.
- 고정된 query 수와 반복 수만 제시해서는 표본 크기의 근거가 없다. 최소 검출 효과와 불확실성에 기반해 표본 수를 정한다.
- 유리한 결과가 나올 때만 진행하는 stop/go 기준은 선택적 보고 위험이 있다. 분석 계획과 제외 기준을 결과 확인 전에 동결한다.
- 실제 실행과 biological correctness가 핵심 claim이면 12개 e2e 사례만으로는 부족하다. primary endpoint를 지지하는 powered/전수 e2e 평가가 필요하다.

이 문서는 특정 저널의 형식 요건을 대신하지 않는다. target journal을 정한 뒤 해당 저널의 software/data availability, human evaluation, supplementary material checklist를 별도로 매핑한다.

---

## Current Status

- Hybrid architecture, template registry, normalization, equivalence scoring, repair, experiment runner는 구현되어 있다.
- 현재 대표 benchmark는 `docs/superpowers/experiments/benchmarks/2026-06-15-core-query-set.json`의 10개 query 수준이다.
- Template coverage report는 19개 template family를 다룬다.
- Recorded smoke comparison은 small set 기준이며 provider 상태 제약이 있다. 현재 runner의 `executable_workflow_rate`는 실제 실행 지표가 아니므로 기존 수치를 논문 결과로 재사용할 수 없다.
- 따라서 저널 제출용으로는 독립 평가셋, 실제 입력 파일, gold workflow, e2e 실행 데이터, 전문가 의미 평가가 추가로 필요하다.

---

## Deliverables

| 산출물 | 위치 | 목적 |
|---|---|---|
| 독립 자연어 benchmark | `docs/superpowers/experiments/benchmarks/journal_query_set_v1.json` | intent/template/generation 평가 |
| Gold workflow specs | `docs/superpowers/experiments/gold_workflows/*.json` | 구조 정답 및 equivalence 기준 |
| Bioinformatics fixture files | `tests/fixtures/journal_bio_data/*` 또는 `docs/superpowers/experiments/fixtures/*` | 실제 실행 입력 |
| Expected outputs | `docs/superpowers/experiments/expected_outputs/*.json` | 실행 결과 검증 |
| Experiment reports | `docs/superpowers/experiments/2026-*-journal-*.md` | 논문 표/그림 근거 |
| Expert review sheet | `docs/superpowers/experiments/expert_review/*.csv` | 의미 정확성/유용성 평가 |
| Reproducibility manifest | `docs/superpowers/experiments/reproducibility_manifest.json` | 모델/환경/해시/실험 추적 |
| Frozen protocol/statistical analysis plan | `docs/superpowers/experiments/journal_protocol.md` | 가설, endpoint, 제외 기준, 표본 수, 분석 동결 |
| Machine-readable schemas and validators | `docs/superpowers/experiments/schemas/*`, `scripts/validate_journal_package.py` | 데이터 무결성 자동 검증 |
| Immutable raw run records | `docs/superpowers/experiments/raw_runs/<run_id>/*` 또는 외부 artifact archive | 재분석 가능한 원시 산출물 보존 |
| Environment lock and archive metadata | `requirements-journal.lock`, `CITATION.cff`, archive metadata | 환경 재현 및 DOI 공개 준비 |

---

## Design Principles

1. **평가셋은 시스템 개발 데이터와 분리한다.** 기존 10개 core query는 smoke/dev set으로만 쓰고, 논문 수치는 새 journal set에서 산출한다.
2. **키워드 누수를 줄인다.** query 문장은 template id나 node 이름을 직접 반복하지 않는 paraphrase를 포함한다.
3. **단일 정답을 강요하지 않는다.** `acceptable_template_ids`, `acceptable_workflow_ids`, `functional_equivalence_group`를 사용한다.
4. **실행 가능성과 의미 정확성을 분리한다.** JSON valid, schema valid, ComfyUI loadable, runtime success, biological correctness를 별도 지표로 보고한다.
5. **외부 API 의존성을 캐시한다.** Entrez/UniProt/KEGG 등은 fixture 또는 cached response를 사용해 재현성을 확보한다.
6. **실패 케이스를 버리지 않는다.** invalid JSON, wrong template, runtime error, semantically wrong workflow를 모두 failure taxonomy에 기록한다.
7. **분석 계획을 결과보다 먼저 동결한다.** primary endpoint, 제외 기준, 비교쌍, 통계 방법과 sample-size rationale을 pilot 이후 본실험 전에 commit/tag로 고정한다.
8. **비교는 paired design으로 수행한다.** 같은 query, provider/model, replicate에서 mode만 바꾸고 실행 순서는 무작위화한다. 가능한 경우 동일 seed/decoding 설정을 사용한다.
9. **자동 지표와 독립 ground truth를 분리한다.** template equivalence는 구조적 secondary metric이며 biological task correctness의 대리 지표로 단독 사용하지 않는다.
10. **원시 결과는 불변으로 보존한다.** 오류 로그를 포함한 원시 JSONL을 먼저 저장하고 표/그림은 versioned analysis script로 파생한다. 수동으로 결과표를 편집하지 않는다.
11. **provider 운영 실패를 사전 정의한다.** timeout, quota, auth 실패의 재시도 횟수와 제외/실패 처리 규칙을 protocol에 고정하고 결과를 본 뒤 바꾸지 않는다.

---

## Task 1: 논문 주장과 평가 범위 고정

**Files:**
- Create: `docs/superpowers/experiments/journal_scope.md`
- Create: `docs/superpowers/experiments/journal_protocol.md`
- Create: `docs/superpowers/experiments/journal_protocol_freeze.json`
- Create: `docs/superpowers/experiments/journal_protocol_amendment_001.md`

- [x] **Step 1: 논문 핵심 claim을 한 문장으로 작성**

권장 문장:

```text
Template-guided hybrid workflow generation improves structural validity and biological task correctness over free-form LLM generation for natural-language Biopython workflow construction in ComfyUI.
```

`biological task correctness`는 독립 expert rating과 expected-output-verified execution에서 모두 지지될 때만 최종 claim에 유지한다. 그렇지 않으면 structural validity/runtime success claim으로 낮춘다.

- [x] **Step 2: 평가할 workflow family를 고정**

최소 포함:
- `fasta_parse`
- `pairwise_alignment`
- `multiple_alignment`
- `blast_search`
- `searchio_analysis`
- `phylogeny`
- `annotation`
- `pdb_structure_basic`
- `motif_scan_basic`
- `entrez_fetch`
- `uniprot_lookup`
- `kegg_pathway_basic`

- [x] **Step 3: 제외 범위를 명시**

예:
- 대규모 production BLAST DB 검색은 제외하고 cached/small DB 또는 fixture 기반 실행만 평가한다.
- 외부 네트워크 API의 live availability는 평가 대상이 아니며 cached response로 대체한다.
- 식물 육종/멀티모달 확장은 본 논문 본실험이 아니라 future work 또는 별도 PoC로 둔다.

- [x] **Step 4: target venue와 reporting checklist를 고정**

Software paper, bioinformatics methods paper, data descriptor 중 manuscript type을 선택하고 해당 저널의 최신 author guideline을 `journal_scope.md`에 기록한다. human expert evaluation에 대한 기관 윤리 검토/면제 필요 여부, consent, 이해상충과 보상도 기관 규정에 따라 확인한다.

- [x] **Step 5: 본실험 전 protocol freeze**

가설, primary/secondary endpoint, sample-size rationale, 제외 기준, 재시도 정책, 통계 분석을 `journal_protocol.md`에 작성한다. pilot 결과로 protocol을 수정할 수 있지만 본실험 raw output을 보기 전에 commit hash와 날짜를 기록하고 이후 변경은 amendment로 남긴다.

---

## Task 2: Benchmark 스키마 정의

**Files:**
- Create: `docs/superpowers/experiments/benchmarks/journal_query_schema.md`
- Create: `docs/superpowers/experiments/benchmarks/journal_query_set_v1.json`
- Create: `docs/superpowers/experiments/schemas/journal_query_set_v1.schema.json`
- Create: `scripts/validate_journal_package.py`
- Create: `tests/llm_core/test_validate_journal_package.py`

- [x] **Step 1: query record 스키마를 문서화**

권장 필드:

```json
{
  "id": "JQ001",
  "label": "fasta_paraphrase_easy_001",
  "query": "open a sequence file and list the records it contains",
  "expected_intent": "fasta_parse",
  "acceptable_template_ids": ["fasta_parse"],
  "acceptable_workflow_ids": ["GW_fasta_parse_001"],
  "difficulty": "easy",
  "domain": "sequence_io",
  "input_fixture_id": "FX_FASTA_SMALL_001",
  "expected_output_id": "OUT_FASTA_SUMMARY_001",
  "source": "author_written_heldout",
  "notes": ""
}
```

- [x] **Step 2: difficulty 기준 정의**

권장 기준:
- `easy`: 단일 목적, 1-2개 핵심 노드.
- `medium`: 2-4개 노드, parse 후 summary/analysis.
- `hard`: 4개 이상 노드, 여러 중간 산출물 또는 branch.
- `adversarial`: 모호 표현, 키워드 미포함, 잘못된 포맷, 비지원 요청.

- [x] **Step 3: machine-readable schema와 validation을 구현**

수동 검토만으로 진행하지 않는다. 첫 seed set부터 JSON Schema(또는 동등한 Python schema), referential-integrity validator, pytest를 추가한다. 최소 검증 항목은 unique id, enum, fixture/output/gold 참조 존재, family/difficulty 분포, 중복 query, 빈 필드와 schema version이다.

---

## Task 3: 독립 자연어 query set 작성

**Files:**
- Modify: `docs/superpowers/experiments/benchmarks/journal_query_set_v1.json`

- [ ] **Step 1: seed set 30개 작성**

목표:
- 12개 workflow family마다 최소 2개.
- easy/medium 중심.
- 기존 `core-query-set` 문장을 그대로 복사하지 않는다.

- [ ] **Step 2: pilot 후 근거 있는 full set으로 확장**

120개는 초기 planning target으로만 사용한다. pilot의 paired success discordance 또는 사전 정의한 최소 검출 효과를 이용해 primary endpoint의 표본 수를 결정하고 `journal_protocol.md`에 계산/가정을 남긴다. 120개를 유지할 경우 권장 분포는 다음과 같다.

- easy 36개
- medium 48개
- hard 24개
- adversarial 12개

- [ ] **Step 3: template keyword leakage 점검**

각 query에서 template id, class_type, 노드명을 직접 쓰는 항목을 표시한다. 직접 키워드가 필요한 경우 `notes`에 이유를 기록한다.

- [ ] **Step 4: held-out 원칙 기록**

query 작성 후에는 template/intent classifier 튜닝에 `journal_query_set_v1`을 직접 사용하지 않는다. 튜닝이 필요하면 `journal_query_dev.json`를 별도로 만든다.

- [ ] **Step 5: 독립성과 중복을 검증**

가능하면 시스템 개발에 참여하지 않은 2명 이상이 task brief에서 query를 작성하고, 저자는 supported/unsupported label만 검토한다. 기존 prompt, template 설명, dev query와의 exact/near-duplicate 및 핵심 n-gram overlap을 자동 보고한다. author-written-only set이면 이를 한계로 명시하고 “independent” 대신 “held-out”이라고 부른다.

---

## Task 4: Gold workflow spec 제작

**Files:**
- Create directory: `docs/superpowers/experiments/gold_workflows/`
- Create: `docs/superpowers/experiments/gold_workflows/index.json`
- Create: `docs/superpowers/experiments/gold_workflows/GW_*.json`

- [ ] **Step 1: family별 independent functional gold spec과 reference workflow 작성**

각 gold spec은 입력, 허용 가능한 출력, 필수 생물학적 연산, 금지/critical-error 조건을 먼저 정의한다. 그 후 `node_registry.json`에 맞는 reference workflow를 작성한다. 기존 `workflow_guidance/templates/*.json`를 그대로 복사하거나 이를 유일한 정답으로 사용하지 않는다. 작성자와 검토자, 근거 문서, review date를 metadata에 남긴다.

- [ ] **Step 2: query별 acceptable workflow mapping 작성**

`journal_query_set_v1.json`의 `acceptable_workflow_ids`가 실제 `gold_workflows/index.json`에 존재해야 한다.

- [ ] **Step 3: 복수 정답이 필요한 case를 표시**

예:
- sequence summary는 `SeqIO_parse -> SeqIO_records_info`와 다른 summary node 조합이 모두 가능할 수 있다.
- phylogeny는 tree read/summary/render 중 goal 표현에 따라 acceptable workflow가 달라질 수 있다.

- [ ] **Step 4: gold workflow lint 수행**

검증 항목:
- 모든 `class_type`이 `node_registry.json`에 존재한다.
- 모든 edge port가 registry와 일치한다.
- graph가 acyclic이다.
- required input이 fixture 또는 default로 충족된다.

- [ ] **Step 5: circularity audit 수행**

gold 작성자가 hybrid template 구현을 보지 않았는지 기록한다. 불가피하게 같은 개발자가 작성한 경우 independent reviewer가 functional criteria와 허용 가능한 대안 workflow를 승인한다. template equivalence는 secondary metric으로만 보고한다.

---

## Task 5: 실제 bioinformatics fixture 데이터 수집

**Files:**
- Create directory: `docs/superpowers/experiments/fixtures/`
- Create: `docs/superpowers/experiments/fixtures/fixture_manifest.json`

- [ ] **Step 1: small local fixture 우선 작성**

필수 fixture:
- FASTA: 2-5개 sequence
- GenBank: 짧은 annotated record
- Alignment: Clustal 또는 Stockholm small alignment
- Newick: 4-8 taxa tree
- BLAST/SearchIO: small XML 또는 tabular result
- PDB/mmCIF: 작은 구조 파일 또는 최소 fixture
- Motif: simple motif file

- [ ] **Step 2: external API fixture는 cached response로 저장**

대상:
- Entrez
- UniProt
- KEGG

Live API 호출 결과를 논문 실험의 필수 조건으로 만들지 않는다.

- [ ] **Step 3: negative fixture 추가**

최소 포함:
- empty file
- wrong extension/format mismatch
- malformed FASTA
- invalid Newick
- missing required file

- [ ] **Step 4: 라이선스와 출처 기록**

공개 데이터는 accession/source/license를 `fixture_manifest.json`에 기록한다. 직접 만든 synthetic fixture는 `synthetic`으로 표시한다.

각 fixture는 SHA-256, byte size, retrieval date, 원본 URL/accession, redistribution 가능 여부를 포함한다. 재배포가 불가능한 데이터는 다운로드/검증 script와 pinned checksum을 제공하고 package에 직접 포함하지 않는다.

---

## Task 6: Expected output 정의

**Files:**
- Create directory: `docs/superpowers/experiments/expected_outputs/`
- Create: `docs/superpowers/experiments/expected_outputs/index.json`
- Create: `docs/superpowers/experiments/expected_outputs/OUT_*.json`

- [ ] **Step 1: fixture별 핵심 expected output 작성**

예:
- FASTA record count, sequence ids, lengths
- alignment rows/columns
- tree terminal count
- BLAST hit count 또는 top hit id
- PDB chain count 또는 residue count

- [ ] **Step 2: exact match와 contains match를 구분**

부동소수점 또는 문자열 formatting이 흔들릴 수 있는 항목은 tolerance 또는 contains 기반으로 둔다.

- [ ] **Step 3: semantic success 기준을 별도로 작성**

실행 결과가 예상 문자열을 포함하는 것과 goal을 달성하는 것은 다르다. expected output에는 `runtime_success_criteria`와 `semantic_success_criteria`를 분리한다.

---

## Task 7: Experiment matrix 설계

**Files:**
- Create: `docs/superpowers/experiments/journal_experiment_matrix.md`
- Modify: `docs/superpowers/experiments/journal_protocol.md`

- [ ] **Step 1: mode 비교를 고정**

필수:
- `free`
- `normalized`
- `hybrid`

- [ ] **Step 2: provider 비교를 고정**

권장:
- `deterministic`
- `codex` with known working model
- `claude` if quota/session state allows
- `gemini` only after readiness is confirmed

Provider 수를 늘리는 것보다 동일한 frozen model에서 mode 비교를 완결하는 것을 우선한다. deterministic provider는 pipeline test이며 LLM 효과의 통계적 근거로 합산하지 않는다. model snapshot/version을 고정할 수 없는 provider는 실행 날짜와 reported model id를 명시하고 temporal drift limitation을 보고한다.

- [ ] **Step 3: repeat 수와 실행 순서 결정**

- deterministic: 1회(pipeline validation only)
- LLM provider: pilot variance를 근거로 정하되, stochastic reliability를 주장하려면 query/mode당 기본 5회 이상을 권장한다.
- query × mode × replicate 순서를 randomize하고 randomization seed를 보존한다.
- temperature/top-p/seed를 제어할 수 있으면 고정·기록한다. 제어할 수 없으면 명시한다.

- [ ] **Step 4: primary/secondary metric 지정**

Primary endpoint는 하나를 사전 지정한다. 권장 primary는 fixture-backed task의 `expected-output-verified ComfyUI execution success`이다.

Secondary:
- blinded expert semantic correctness
- functional gold criteria pass rate
- valid JSON rate
- schema/graph validity rate
- template match rate
- equivalence score
- repair frequency
- inter-model agreement
- runtime latency

- [ ] **Step 5: paired comparison과 통계 분석을 사전 정의**

- binary primary endpoint: query 단위 paired comparison(McNemar 또는 query/provider random effect를 둔 mixed-effects logistic model)
- continuous/ordinal metric: paired bootstrap CI 또는 적절한 ordinal/mixed model
- 모든 효과에 point estimate, 95% CI, denominator를 보고하고 p-value만으로 결론 내리지 않는다.
- provider/family/difficulty subgroup은 secondary로 표시하고 multiple-comparison correction 또는 명시적 exploratory label을 사용한다.
- 실패한 provider call을 임의 삭제하지 않고 protocol의 intention-to-evaluate/per-protocol 정의에 따라 둘 다 sensitivity analysis한다.

- [ ] **Step 6: ablation이 claim을 식별하는지 확인**

`free`, `normalized`, `hybrid`는 현재 구현의 핵심 ablation이다. 동일 provider/model과 가능한 한 동일 generation settings를 사용한다. hybrid 개선이 classifier/template 선택과 repair 중 어디서 오는지 주장하려면 `normalized + oracle template` 또는 `repair without template selection` 같은 추가 arm을 구현하거나, 해당 구성요소별 인과 claim을 하지 않는다.

---

## Task 8: 기존 runner로 dry run 수행

**Files:**
- Create: `docs/superpowers/experiments/2026-06-18-journal-dry-run.md`

- [ ] **Step 1: seed set 30개로 deterministic dry run**

예상 명령:

```bash
python scripts/run_workflow_experiment.py \
  --query-json docs/superpowers/experiments/benchmarks/journal_query_set_v1.json \
  --provider deterministic \
  --mode free --mode normalized --mode hybrid \
  --repeat 1 \
  --report docs/superpowers/experiments/2026-06-18-journal-dry-run.md \
  --title "Journal Benchmark Dry Run"
```

- [ ] **Step 2: journal schema adapter와 raw result writer 구현**

현재 runner는 `expected_template_id` 단일값만 읽고 `acceptable_template_ids`, fixture별 input, expected output을 처리하지 않는다. 또한 실제 ComfyUI 실행을 하지 않으며 `workflow_json`도 채우지 않는다. 본실험 전에 adapter/scorer를 추가하고 `executable_workflow_rate`를 `workflow_json_present_rate`로 이름 변경하거나 deprecated 처리한다. 원시 JSONL, stdout/stderr, provider metadata를 run id별로 저장한다.

- [ ] **Step 3: failure taxonomy 초안 작성**

분류:
- provider_error
- invalid_json
- schema_validation_error
- wrong_intent
- wrong_template
- low_equivalence
- no_workflow_json
- runtime_error
- semantically_wrong

---

## Task 9: ComfyUI e2e 실행 검증 설계

**Files:**
- Create: `docs/superpowers/experiments/comfyui_e2e_protocol.md`
- Create: `scripts/run_comfyui_e2e_benchmark.py`

- [ ] **Step 1: e2e 성공 정의**

단계별 성공:
- generated spec exists
- converted ComfyUI JSON exists
- workflow loads into ComfyUI
- prompt accepted by server
- execution completes
- expected output criteria satisfied

- [ ] **Step 2: headless 실행 방식 결정**

선택지:
- ComfyUI 서버를 띄운 뒤 `/prompt` API로 실행.
- 불가능하면 노드 직접 호출 기반 runtime benchmark를 별도 보조 지표로 둔다.

- [ ] **Step 3: 최소 e2e subset 선정**

12개 family마다 1개씩 총 12개는 e2e harness 검증용 pilot으로만 사용한다. actual execution이 primary endpoint이면 본실험은 모든 eligible query를 실행하거나 sample-size calculation으로 정한 stratified subset을 실행한다. 12개 pilot 결과를 논문의 primary 성능 수치로 사용하지 않는다.

- [ ] **Step 4: e2e result schema 정의**

필드:
- query_id
- provider
- model
- mode
- workflow_id
- loadable
- prompt_accepted
- completed
- runtime_seconds
- output_match
- error_type
- error_message
- stdout/stderr 또는 artifact path
- generated spec/workflow/output hashes
- ComfyUI/node package version
- retry_count와 provider_operational_status

---

## Task 10: Full benchmark 실행

**Files:**
- Create: `docs/superpowers/experiments/2026-*-journal-mode-comparison.md`
- Create: `docs/superpowers/experiments/2026-*-journal-provider-comparison.md`

- [ ] **Step 1: deterministic full run**

목적은 dataset/gold/equivalence pipeline의 기본 오류를 잡는 것이다.

- [ ] **Step 2: Codex full run**

현재 환경 기록상 Codex는 working model을 명시해야 한다. 실행 리포트에 model id를 남긴다.

- [ ] **Step 3: Claude/Gemini run은 readiness 확인 후 수행**

session limit 또는 미설치 상태에서 나온 실패를 모델 성능 실패로 해석하지 않는다. provider operational failure는 별도 표로 분리한다.

- [ ] **Step 4: immutable raw record와 provenance 저장**

각 invocation의 query id, mode, provider/model, decoding 설정, run index, timestamps, raw/final spec, workflow JSON, 오류와 artifact hash를 JSONL로 먼저 저장한다. Markdown report만 남기는 실행은 본실험으로 인정하지 않는다.

- [ ] **Step 5: mode별 통계표 생성**

표:
- records
- valid_json_rate
- workflow_json_rate
- e2e_execution_success_rate
- mean_equivalence_score
- semantic_correctness_rate
- repair_frequency

---

## Task 11: 전문가 평가 패키지 준비

**Files:**
- Create directory: `docs/superpowers/experiments/expert_review/`
- Create: `docs/superpowers/experiments/expert_review/review_instructions.md`
- Create: `docs/superpowers/experiments/expert_review/review_sheet_template.csv`

- [ ] **Step 1: 평가할 sample 선정**

권장:
- sample-size rationale로 정한 query(50개는 planning minimum)
- mode/provider 정보와 파일 순서를 blind 처리하고 무작위 익명 id 사용
- cherry-picking 없이 사전 정의된 stratified random sample 사용
- 같은 query의 여러 mode 결과가 reviewer에게 연속 노출되지 않도록 순서/블록을 배치

- [ ] **Step 2: reviewer instruction 작성**

평가 기준:
- task relevance: 0/1/2
- biological validity: 0/1/2
- executable usefulness: 0/1/2
- required manual correction: none/minor/major/unusable
- critical error: yes/no

- [ ] **Step 3: reviewer 3명 이상에게 독립 평가 요청**

가능하면 생물정보학 경험자와 wet-lab 생물학자를 섞는다. reviewer eligibility, 경력, 시스템 개발 참여 여부를 익명 집계로 보고한다. 모든 평가자가 같은 core subset을 평가하고 나머지는 균형 블록 배정하여 agreement 계산이 가능하게 한다.

- [ ] **Step 4: inter-rater agreement 계산**

ordinal 평점에는 weighted kappa 또는 Krippendorff alpha, binary critical error에는 Fleiss kappa/alpha와 percent agreement를 함께 보고한다. 95% bootstrap CI, missing rating 처리, disagreement adjudication 규칙을 사전 정의한다. consensus/adjudicated label은 raw independent rating과 분리 보존한다.

- [ ] **Step 5: reviewer process와 ethics metadata 보존**

동의 문구, 보상, 이해상충, 평가 시간, instruction version을 기록한다. 기관 정책상 human-subject review 또는 면제가 필요한지 본실험 전에 확인하고 manuscript에 해당 statement를 포함한다.

---

## Task 12: 결과 분석과 논문용 표/그림 생성

**Files:**
- Create: `docs/superpowers/experiments/2026-*-journal-results-summary.md`

- [ ] **Step 1: main results table 작성**

권장 columns:
- method
- valid JSON
- schema valid
- ComfyUI executable
- semantic correctness
- mean equivalence
- repair frequency

- [ ] **Step 2: difficulty별 성능 분석**

easy/medium/hard/adversarial로 나눠 성능 하락 패턴을 보여준다.

- [ ] **Step 3: family별 성능 분석**

SeqIO, BLAST, Phylo, PDB 등 어떤 도메인에서 약한지 보여준다.

- [ ] **Step 4: failure taxonomy 표 작성**

논문에는 성공률만이 아니라 실패 원인 분포를 넣는다. 이 시스템의 한계를 정직하게 보여주는 것이 리뷰 대응에 유리하다.

- [ ] **Step 5: uncertainty와 sensitivity analysis 생성**

Primary/secondary 결과에 95% CI와 paired effect size를 포함한다. provider 운영 실패 포함/제외, unsupported/adversarial 포함/제외, reviewer consensus/raw rating 분석을 각각 sensitivity table로 생성한다. 결측치와 denominator를 모든 표에 명시한다.

- [ ] **Step 6: representative case study 3개 선정**

추천:
- hybrid가 free보다 명확히 나은 case
- repair가 missing edge를 고친 case
- 실행은 됐지만 의미적으로 틀린 failure case

---

## Task 13: Reproducibility manifest 작성

**Files:**
- Create: `docs/superpowers/experiments/reproducibility_manifest.json`

- [ ] **Step 1: 코드/템플릿 fingerprint 기록**

포함:
- git commit hash
- `node_registry.json` hash
- template directory hash
- benchmark query set hash
- fixture manifest hash

- [ ] **Step 2: provider/model metadata 기록**

포함:
- provider
- model id
- temperature 또는 CLI 기본값
- run timestamp
- account/session issue 여부

- [ ] **Step 3: 실행 환경 기록**

포함:
- OS
- Python version
- ComfyUI version if available
- Biopython version
- relevant CLI versions
- dependency lockfile 또는 container image digest
- locale/timezone, hardware, randomization seed
- system/developer prompt와 template snapshot(공개 불가 부분은 정확한 제한을 명시)

- [ ] **Step 4: 재실행 명령어 기록**

논문 supplementary에서 그대로 실행 가능한 command block을 남긴다. clean environment에서 package validation, 최소 smoke run, table regeneration을 제3자가 따라 할 수 있는지 확인한다.

- [ ] **Step 5: archival release 준비**

코드·data package version, license, `CITATION.cff`, data/code availability statement, checksums를 준비한다. 가능한 경우 Zenodo/OSF 등 장기 보존소에 immutable release와 DOI를 만들고 manuscript commit/tag와 연결한다. credentials, account id, private path, provider response의 민감정보는 공개 전 자동/수동으로 점검한다.

---

## Task 14: Submission readiness audit

**Files:**
- Create: `docs/superpowers/experiments/2026-*-journal-submission-readiness-audit.md`

- [ ] **Step 1: 필수 산출물 존재 여부 점검**

체크:
- protocol에 근거한 query 수와 분포 충족
- gold workflow coverage
- fixture/expected output manifest
- mode/provider comparison report
- e2e execution report
- expert review report
- reproducibility manifest

- [ ] **Step 2: reject-risk 항목 점검**

위험:
- 평가셋이 너무 작음
- keyword leakage가 큼
- e2e 실행 증거 부족
- provider failure를 모델 실패로 오해
- semantic correctness가 자동 지표에만 의존

- [ ] **Step 3: 논문 claim 수정 여부 결정**

결과가 약하면 claim을 낮춘다.

예:
- 강한 claim: "hybrid improves biological task correctness."
- 약한 claim: "hybrid improves structural validity and template equivalence, while semantic correctness remains variable."

- [ ] **Step 4: 최종 go/no-go 결정**

Submission-ready 기준:
- frozen protocol에서 정한 benchmark와 분석이 누락 없이 재현 가능하다.
- primary endpoint의 분모, raw evidence, effect estimate와 95% CI가 존재한다.
- expert evaluation의 blind procedure와 agreement가 보고된다.
- 결과의 방향과 무관하게 모든 prespecified analysis, 실패 분석과 한계가 문서화되어 있다.
- claim 강도가 관측된 효과와 불확실성을 넘지 않는다.
- archive/license/citation/data availability와 target-journal checklist가 완료된다.

---

## Recommended Timeline

| 기간 | 목표 |
|---|---|
| Week 1 | Task 1-3: venue/scope, frozen protocol draft, schema, pilot query set |
| Week 2 | Task 4-6: gold workflow, fixtures, expected outputs |
| Week 3 | Task 7-9: powered matrix, runner/scorer 보강, e2e pilot |
| Week 4 | Task 10: frozen full benchmark와 raw artifact audit |
| Week 5 | Task 11-12: blinded expert review, prespecified analysis |
| Week 6 | Task 13-14: independent rerun, archive, submission audit |

---

## Minimum Viable Submission Package

시간이 부족하면 아래를 최소 제출 패키지로 삼는다.

- target venue checklist와 frozen protocol/statistical analysis plan
- sample-size rationale를 충족한 held-out query set(120개는 planning target)
- 12개 family independent functional gold criteria와 reviewed reference workflow
- 재배포 가능한 fixture, expected output, schema validator와 checksums
- deterministic pipeline validation + 최소 one frozen live LLM model
- paired free vs normalized vs hybrid, randomized run order, 충분한 repeats
- primary endpoint를 지지하는 powered/전수 ComfyUI e2e execution
- blinded expert review와 inter-rater agreement
- immutable raw records, versioned analysis code, environment lock, reproducibility manifest
- license, citation, data/code availability statement와 archival release

---

## Quality Gates and Pause Conditions

결과가 불리하다는 이유로 본실험을 중단하거나 사례를 제거하지 않는다. 아래 조건은 outcome-based stopping rule이 아니라 측정 체계가 유효하지 않을 때의 사전 정의된 pause condition이다. 중단 시점, 원인, protocol amendment와 이미 수집된 데이터를 보존한다.

- schema/referential-integrity validation 또는 gold workflow lint가 실패한다.
- ComfyUI e2e harness가 positive control을 안정적으로 실행하지 못한다.
- provider operational failure가 protocol의 허용 한도를 넘는다.
- blinding이 깨지거나 reviewer instruction/assignment 오류가 발견된다.
- raw artifact, hash, model/config metadata가 누락되어 실행을 추적할 수 없다.
- expert semantic correctness와 자동 지표가 크게 어긋나지만 ground-truth/adjudication 절차가 원인을 판별하지 못한다.

`hybrid`가 `free`보다 개선되지 않거나 e2e 성공률이 낮은 것은 중단 조건이 아니라 보고해야 할 연구 결과다. 이 경우 prespecified 분석을 완료하고 claim을 null/negative result에 맞게 수정한다.

---
