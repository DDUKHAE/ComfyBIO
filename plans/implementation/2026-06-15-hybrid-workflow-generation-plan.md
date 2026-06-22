# Hybrid Workflow Generation Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 자연어 기반 LLM의 자유 워크플로우 생성 능력을 유지하면서, 후단의 정규화·의도 판별·템플릿 비교·국소 보정을 통해 모델 간 결과 편차를 줄이고 연구용 비교 가능성을 높인다.

**Architecture:** 기존 `goal -> prompt -> adapter -> workflow spec -> ComfyUI JSON` 경로는 유지한다. 다만 LLM이 생성한 raw workflow spec 뒤에 `normalize -> classify intent -> compare against canonical template -> local repair -> final spec` 단계를 추가한다. 템플릿은 생성기를 대체하지 않고, 판정기와 보정 기준으로만 사용한다.

**Tech Stack:** Python 3, asyncio, aiohttp SSE, JSON templates, existing `harness_core` registry/prompt pipeline, pytest.

---

## Current Status

- Core hybrid architecture implementation is complete in code: guidance, normalization, equivalence scoring, local repair, API/history integration, experiment runner, and CLI utilities are present.
- Template strengthening work and experiment scaffolding are complete enough for local provider comparison.
- Operational multi-provider execution is still conditional on provider state. As of June 15, 2026, `codex` works with `gpt-5.5`, `claude` is authenticated but hit a session limit during live smoke runs, and `gemini` is not yet installed/readied in this environment.
- Therefore this plan is implementation-complete but not provider-environment-complete.


## Open Issues

- `codex`는 현재 환경에서 `gpt-5.5`를 써야 안정적으로 동작한다. 구형 기본값(`codex-mini-latest`)은 계정 호환성 이슈가 있었다.
- `claude`는 인증은 되어 있지만 live generation 시 session limit에 걸릴 수 있다.
- `gemini`는 현재 환경에서 아직 설치/로그인되지 않았다.
- 따라서 architecture implementation 자체와 provider-operational readiness는 구분해서 판단해야 한다.

## File Map

| 파일 | 변경 |
|------|------|
| `llm_interface/harness_core/workflow_guidance/__init__.py` | 신규 생성 |
| `llm_interface/harness_core/workflow_guidance/intent_classifier.py` | 신규 생성 |
| `llm_interface/harness_core/workflow_guidance/template_registry.py` | 신규 생성 |
| `llm_interface/harness_core/workflow_guidance/workflow_normalizer.py` | 신규 생성 |
| `llm_interface/harness_core/workflow_guidance/workflow_equivalence.py` | 신규 생성 |
| `llm_interface/harness_core/workflow_guidance/workflow_repair.py` | 신규 생성 |
| `llm_interface/harness_core/workflow_guidance/templates/*.json` | 신규 생성 |
| `llm_interface/harness_core/llm_runner.py` | 수정 |
| `llm_interface/harness_core/workflow_history.py` | 수정 |
| `llm_interface/harness_nodes/__init__.py` | 수정 |
| `llm_interface/harness_core/biopython_prompts.py` | 소폭 수정 |
| `llm_interface/harness_core/llm_contracts.py` | 소폭 수정 가능 |
| `tests/harness_core/test_intent_classifier.py` | 신규 생성 |
| `tests/harness_core/test_workflow_normalizer.py` | 신규 생성 |
| `tests/harness_core/test_workflow_equivalence.py` | 신규 생성 |
| `tests/harness_core/test_workflow_repair.py` | 신규 생성 |
| `tests/harness_core/test_llm_runner_hybrid.py` | 신규 생성 |
| `tests/harness_nodes/test_generate_api.py` | 수정 |

---

## Design Principles

1. **Free generation stays first-class.** LLM은 여전히 전체 workflow spec을 생성한다.
2. **Template is guidance, not a substitute generator.** 템플릿은 비교·판정·국소 보정 기준으로만 쓴다.
3. **Deterministic post-processing.** 정규화와 점수 계산은 입력이 같으면 항상 같은 결과를 내야 한다.
4. **Repair must stay local.** 보정은 edge 정리, 필수 노드 보완, 불필요 노드 제거 수준에 제한한다.
5. **Research traceability matters.** raw / normalized / final spec과 메타데이터를 모두 기록한다.

---

## Task 1: Guidance 디렉토리와 canonical template 뼈대 추가

**Files:**
- Create: `llm_interface/harness_core/workflow_guidance/__init__.py`
- Create: `llm_interface/harness_core/workflow_guidance/templates/fasta_parse.json`
- Create: `llm_interface/harness_core/workflow_guidance/templates/blast_basic.json`
- Create: `llm_interface/harness_core/workflow_guidance/templates/msa_basic.json`
- Create: `llm_interface/harness_core/workflow_guidance/templates/phylogeny_basic.json`
- Create: `llm_interface/harness_core/workflow_guidance/templates/annotation_basic.json`

- [x] **Step 1: 패키지 디렉토리와 빈 `__init__.py` 생성**

`workflow_guidance` 패키지를 만들고 최소 import surface만 둔다.

- [x] **Step 2: intent별 template JSON 5종 추가**

각 템플릿은 생성용 full graph가 아니라 비교/보정 기준만 담는다.

권장 형식:

```json
{
  "template_id": "fasta_parse",
  "intent": "fasta_parse",
  "description": "Parse FASTA and summarize records",
  "required_nodes": [
    "SeqIO_parse",
    "SeqIO_records_info"
  ],
  "required_edges": [
    {
      "from_class": "SeqIO_parse",
      "from_port": "records",
      "to_class": "SeqIO_records_info",
      "to_port": "records"
    }
  ],
  "optional_nodes": [],
  "forbidden_nodes": []
}
```

- [x] **Step 3: JSON 형식 검토**

최소한 `json.loads()` 가능 여부와 필수 키 존재 여부를 확인한다.

---

## Task 2: Intent classifier 구현

**Files:**
- Create: `llm_interface/harness_core/workflow_guidance/intent_classifier.py`
- Create: `tests/harness_core/test_intent_classifier.py`

- [x] **Step 1: 실패하는 테스트 작성**

테스트는 대표 프롬프트가 기대 intent로 분류되는지 검증한다.

예시 케이스:
- `"parse a fasta file and summarize sequence ids"` -> `fasta_parse`
- `"run blast against a nucleotide database"` -> `blast_search`
- `"build a phylogenetic tree from aligned sequences"` -> `phylogeny`

- [x] **Step 2: rule-based classifier 구현**

함수 시그니처 권장:

```python
def classify_intent(goal: str) -> str:
    ...
```

초기에는 keyword 기반으로 충분하다. 재현성이 우선이다.

- [x] **Step 3: 테스트 통과 확인**

---

## Task 3: Template registry 구현

**Files:**
- Create: `llm_interface/harness_core/workflow_guidance/template_registry.py`

- [x] **Step 1: 템플릿 로더 구현**

함수 시그니처 권장:

```python
def load_template(template_id: str) -> dict: ...
def get_template_for_intent(intent: str) -> dict | None: ...
def list_templates() -> list[dict]: ...
```

- [x] **Step 2: 파일 경로를 패키지 기준으로 resolve**

상대 경로 하드코딩 대신 `Path(__file__).resolve().parent / "templates"` 기준으로 읽는다.

- [x] **Step 3: 잘못된 템플릿은 명시적으로 실패**

필수 키 누락 시 `ValueError` 또는 전용 예외를 던진다.

---

## Task 4: Workflow normalizer 구현

**Files:**
- Create: `llm_interface/harness_core/workflow_guidance/workflow_normalizer.py`
- Create: `tests/harness_core/test_workflow_normalizer.py`

- [x] **Step 1: 실패하는 테스트 작성**

검증 대상:
- node id가 `n1`, `n2`, ... 순서로 재정렬되는가
- edge가 deterministic order로 정렬되는가
- 중복 edge가 제거되는가
- registry에 없는 class_type 노드가 제거 또는 실패 처리되는가

- [x] **Step 2: 정규화 함수 구현**

함수 시그니처 권장:

```python
def normalize_workflow_spec(spec: dict, registry: dict) -> dict:
    ...
```

최소 동작:
- nodes 재번호
- old id -> new id 매핑
- edges remap
- 중복 제거
- 정렬

- [x] **Step 3: deterministic 동작 확인**

같은 입력을 두 번 넣어 완전히 같은 출력이 나와야 한다.

---

## Task 5: Workflow equivalence scorer 구현

**Files:**
- Create: `llm_interface/harness_core/workflow_guidance/workflow_equivalence.py`
- Create: `tests/harness_core/test_workflow_equivalence.py`

- [x] **Step 1: 실패하는 테스트 작성**

검증 대상:
- template의 required node/edge를 모두 만족하면 높은 score
- required node가 빠지면 점수 하락
- extra node/edge가 있으면 penalty

- [x] **Step 2: 점수 함수 구현**

함수 시그니처 권장:

```python
def score_workflow_against_template(spec: dict, template: dict) -> dict:
    return {
        "score": ...,
        "missing_nodes": [...],
        "missing_edges": [...],
        "extra_nodes": [...],
        "extra_edges": [...],
    }
```

점수 구성 권장:
- required node coverage
- required edge coverage
- extra node penalty
- extra edge penalty

- [x] **Step 3: deterministic score 보장**

정렬되지 않은 input 순서에 따라 score가 바뀌지 않아야 한다.

---

## Task 6: Workflow local repair 구현

**Files:**
- Create: `llm_interface/harness_core/workflow_guidance/workflow_repair.py`
- Create: `tests/harness_core/test_workflow_repair.py`

- [x] **Step 1: 실패하는 테스트 작성**

허용 repair 예시:
- 불필요한 extra node prune
- 누락된 필수 종료 노드 보완
- 명백한 invalid edge 제거

금지 동작 테스트:
- template 전체로 갈아엎기 금지
- 원래 생성 결과의 대부분을 교체하는 rewrite 금지

- [x] **Step 2: 국소 보정 함수 구현**

함수 시그니처 권장:

```python
def repair_workflow_spec(spec: dict, template: dict, registry: dict) -> tuple[dict, dict]:
    ...
```

메타데이터 예시:

```python
{
  "repair_applied": True,
  "repair_summary": [
    "removed extra node SeqIO_records_info",
    "dropped invalid edge n2.foo -> n3.bar"
  ]
}
```

- [x] **Step 3: 보정 범위 제한 확인**

보정 전후 노드 수 차이와 수정 유형이 지나치게 크지 않은지 테스트로 고정한다.

---

## Task 7: `llm_runner.py`에 hybrid pipeline 통합

**Files:**
- Modify: `llm_interface/harness_core/llm_runner.py`
- Create: `tests/harness_core/test_llm_runner_hybrid.py`

- [x] **Step 1: 실패하는 통합 테스트 작성**

mock 기반으로 아래 흐름을 검증한다.
- adapter가 raw spec 반환
- normalize 호출
- intent classify 호출
- template load 및 score 호출
- 필요 시 repair 호출
- 최종 반환에 metadata 포함

- [x] **Step 2: runner 반환 구조 확장**

권장 반환 형식:

```python
{
  "raw_spec": raw_spec,
  "normalized_spec": normalized_spec,
  "final_spec": final_spec,
  "intent": intent,
  "template_id": template_id,
  "equivalence_score": score,
  "repair_applied": repair_applied,
  "repair_summary": repair_summary,
}
```

기존 API와의 호환을 위해 downstream에서 `final_spec`를 사용하게 맞춘다.

- [x] **Step 3: mode 지원 추가**

권장 모드:
- `free`
- `normalized`
- `hybrid`

동작:
- `free`: raw spec을 final로 사용
- `normalized`: normalized spec을 final로 사용
- `hybrid`: normalized 후 repair 결과를 final로 사용

- [x] **Step 4: exec_log에 guidance 단계 기록 추가**

예:
- `Intent classified: phylogeny`
- `Template selected: phylogeny_basic`
- `Equivalence score: 0.82`
- `Repair applied: removed 1 extra node`

---

## Task 8: API 레이어와 history 저장 확장

**Files:**
- Modify: `llm_interface/harness_nodes/__init__.py`
- Modify: `llm_interface/harness_core/workflow_history.py`
- Modify: `tests/harness_nodes/test_generate_api.py`

- [x] **Step 1: generate API에서 `mode` 입력 지원**

요청 body에서 `mode`를 읽고 `generate_biopython_workflow()`에 전달한다.

- [x] **Step 2: `final_spec`만 ComfyUI JSON 변환에 사용**

`raw_spec`와 `normalized_spec`는 기록용으로 남기고, 실제 `canonical_to_comfy_json()`에는 `final_spec`를 넣는다.

- [x] **Step 3: SSE done payload에 연구용 metadata 추가**

권장 필드:
- `intent`
- `template_id`
- `equivalence_score`
- `repair_applied`
- `mode`

- [x] **Step 4: history 필드 확장**

`append_record()` 저장 구조에 다음 필드 추가:
- `raw_workflow_spec`
- `normalized_workflow_spec`
- `final_workflow_spec`
- `intent`
- `template_id`
- `equivalence_score`
- `repair_applied`
- `repair_summary`
- `mode`

- [x] **Step 5: API 테스트 갱신**

done payload와 저장 레코드에 위 필드가 반영되는지 검증한다.

---

## Task 9: Prompt / contract 계층 소폭 보강

**Files:**
- Modify: `llm_interface/harness_core/biopython_prompts.py`
- Modify: `llm_interface/harness_core/llm_contracts.py` (선택)

- [x] **Step 1: prompt에 canonicality 힌트 강화**

권장 문구:
- minimum nodes
- valid type-matched edges only
- use standard Biopython analysis flow
- avoid decorative or redundant nodes

중요: template를 직접 삽입해 자유 생성을 대체하지 않는다.

- [x] **Step 2: contract의 기초 검증 강화 여부 판단**

필요하면 아래만 추가한다.
- duplicate node id 검출
- empty class_type 검출
- malformed `node.port` 검증 강화

template 비교/repair 로직은 여기 넣지 않는다.

---

## Task 10: End-to-end 테스트와 실험 기준 확정

**Files:**
- Modify/Create: `tests/...`

- [x] **Step 1: 핵심 단위 테스트 모두 실행**

권장 실행:

```bash
cd /home/ydj/main/ComfyBIO_biopython
python -m pytest tests/harness_core/test_intent_classifier.py -v
python -m pytest tests/harness_core/test_workflow_normalizer.py -v
python -m pytest tests/harness_core/test_workflow_equivalence.py -v
python -m pytest tests/harness_core/test_workflow_repair.py -v
python -m pytest tests/harness_core/test_llm_runner_hybrid.py -v
python -m pytest tests/harness_nodes/test_generate_api.py -v
```

- [x] **Step 2: 실험 모드 비교 기준 정리**

비교 대상:
- `free`
- `normalized`
- `hybrid`

비교 지표:
- valid JSON rate
- executable workflow rate
- inter-model agreement
- equivalence score
- repair frequency

- [x] **Step 3: 문서화 또는 결과 기록 위치 확정**

실험 결과를 `docs/superpowers/experiments/` 또는 별도 report 문서에 축적할지 결정한다.

---

## Expected Outcomes

구현 완료 후 시스템은 다음을 만족해야 한다.

1. 동일 자연어 요청에 대해 provider별 raw workflow 차이를 수집할 수 있다.
2. deterministic normalization으로 표면 차이를 줄일 수 있다.
3. intent별 canonical template를 기준으로 workflow 유사도를 계산할 수 있다.
4. 필요 시 local repair를 적용하되, full rewrite 없이 최종 workflow를 안정화할 수 있다.
5. raw / normalized / final spec이 모두 기록되어 연구용 분석이 가능하다.

---

## Non-Goals

- 템플릿 기반 full generation으로 전환하지 않는다.
- repair 단계에서 workflow 전체를 template로 대체하지 않는다.
- 초기 단계에서 학습 기반 intent classifier를 도입하지 않는다.
- ComfyUI workflow JSON 변환기(`biopython_comfy_adapter.py`)의 구조를 대폭 바꾸지 않는다.
