# Template Workflow Strengthening Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** canonical template의 구조 품질을 높여, 생성된 workflow가 실제 분석 흐름과 더 유사하게 평가·보정되도록 한다. 특히 `required_edges`를 실질적으로 채우고, intent coverage를 확장하며, template 품질을 fixture 기반으로 검증한다.

**Why now:** 현재 hybrid architecture는 동작하지만, template가 일부 intent에서 “필수 노드 존재 여부” 중심으로만 정의되어 있어 실제 분석 workflow 유사도(C3)와 repair 품질이 제한된다. template가 더 구체적이어야 equivalence score와 local repair가 실제 분석 흐름을 더 잘 반영한다.

**Architecture:** 기존 `workflow_guidance` 계층은 유지한다. 변경은 주로 `templates/*.json`, `workflow_equivalence.py`, `workflow_repair.py`, 그리고 fixture 기반 테스트에 집중한다. 자유 생성 구조는 유지하고, template는 계속 판정·보정 기준으로만 사용한다.

**Tech Stack:** JSON templates, Python 3, existing `node_registry.json`, pytest.

---

## Current Status

- Template strengthening work itself is complete: canonical `required_edges`, expanded intent coverage, fixture-based validation, edge-sensitive scoring, structured repair actions, and template benchmark documentation are in place.
- Remaining open items in the broader thread are operational rather than template-definition issues: provider readiness, live experiment reruns, and dated comparison report accumulation.


## File Map

| 파일 | 변경 |
|------|------|
| `llm_interface/harness_core/workflow_guidance/templates/fasta_parse.json` | 수정 |
| `llm_interface/harness_core/workflow_guidance/templates/blast_basic.json` | 수정 |
| `llm_interface/harness_core/workflow_guidance/templates/msa_basic.json` | 수정 |
| `llm_interface/harness_core/workflow_guidance/templates/phylogeny_basic.json` | 수정 |
| `llm_interface/harness_core/workflow_guidance/templates/annotation_basic.json` | 수정 |
| `llm_interface/harness_core/workflow_guidance/templates/*.json` | 신규 추가 가능 |
| `llm_interface/harness_core/workflow_guidance/workflow_equivalence.py` | 수정 |
| `llm_interface/harness_core/workflow_guidance/workflow_repair.py` | 수정 |
| `tests/harness_core/test_template_registry.py` | 수정 |
| `tests/harness_core/test_workflow_equivalence.py` | 수정 |
| `tests/harness_core/test_workflow_repair.py` | 수정 |
| `tests/harness_core/test_template_fixtures.py` | 신규 생성 |
| `docs/superpowers/experiments/*.md` | 선택적 추가 |

---

## Design Principles

1. **Template는 실제 분석 흐름을 표현해야 한다.** 노드 목록만이 아니라 핵심 데이터 흐름 edge를 포함해야 한다.
2. **Repair는 template-driven full rewrite가 되면 안 된다.** 템플릿이 구체화되더라도 local correction 범위는 유지한다.
3. **Intent별 template는 대표 workflow family를 표현해야 한다.** 모든 변형을 포괄하려 하지 말고, 가장 canonical한 흐름부터 고정한다.
4. **Registry truth를 따른다.** template의 node/port 이름은 반드시 `node_registry.json`과 일치해야 한다.
5. **Fixture로 검증한다.** template 품질은 hand-wavy하게 두지 말고, gold workflow fixture와 score/repair 결과로 고정한다.

---

## Task 1: 기존 template의 required_edges 보강

**Files:**
- Modify: `llm_interface/harness_core/workflow_guidance/templates/fasta_parse.json`
- Modify: `llm_interface/harness_core/workflow_guidance/templates/blast_basic.json`
- Modify: `llm_interface/harness_core/workflow_guidance/templates/msa_basic.json`
- Modify: `llm_interface/harness_core/workflow_guidance/templates/phylogeny_basic.json`
- Modify: `llm_interface/harness_core/workflow_guidance/templates/annotation_basic.json`

- [x] **Step 1: 각 template의 실제 node/port 흐름 재검토**

`node_registry.json` 기준으로 실제 가능한 포트명을 다시 확인한다.

- [x] **Step 2: `required_edges`를 최소 canonical path 수준까지 채움**

예시 방향:
- `fasta_parse`: `SeqIO_parse.records -> SeqIO_records_info.records`
- `blast_basic`: query parsing / BLAST / SearchIO parsing 간 핵심 edge 반영
- `msa_basic`: sequence parsing 후 alignment output으로 이어지는 핵심 edge 반영
- `phylogeny_basic`: sequence/align/tree transformation의 핵심 path 반영
- `annotation_basic`: parse된 record에서 feature/annotation inspection으로 이어지는 핵심 edge 반영

- [x] **Step 3: optional vs required 경계 재조정**

현재 optional node에 들어가 있는 항목 중 canonical path에 필수인 것은 `required_nodes`로 승격한다.

---

## Task 2: intent coverage 확장

**Files:**
- Create/Modify: `llm_interface/harness_core/workflow_guidance/templates/*.json`
- Modify: `llm_interface/harness_core/workflow_guidance/intent_classifier.py`
- Modify: `tests/harness_core/test_intent_classifier.py`
- Modify: `tests/harness_core/test_template_registry.py`

- [x] **Step 1: 다음 우선 intent 후보를 선정**

우선순위 예시:
- `searchio_analysis`
- `pairwise_alignment`
- `entrez_fetch`
- `sequence_annotation_edit`
- `pdb_structure_basic`

- [x] **Step 2: intent classifier keyword 확장**

너무 넓은 intent보다 좁고 canonical한 intent를 우선 추가한다.

- [x] **Step 3: 새 template 추가**

각 template는 최소한 아래를 포함한다.
- `template_id`
- `intent`
- `description`
- `required_nodes`
- `required_edges`
- `optional_nodes`
- `forbidden_nodes`

---

## Task 3: template fixture 기반 검증 추가

**Files:**
- Create: `tests/harness_core/test_template_fixtures.py`
- Modify: `tests/harness_core/test_workflow_equivalence.py`
- Modify: `tests/harness_core/test_workflow_repair.py`

- [x] **Step 1: intent별 gold fixture 정의**

fixture는 “이 intent에서 canonical하다고 간주할 수 있는 normalized/final workflow spec”이다.

권장 fixture 세트:
- exact canonical fixture
- edge 1개 누락 fixture
- extra node 포함 fixture
- 잘못된 branch 포함 fixture

- [x] **Step 2: equivalence score expectation 고정**

예시:
- exact canonical fixture -> 높은 score (예: `>= 0.95`)
- required edge 누락 -> 유의미한 penalty
- extra node 추가 -> penalty
- forbidden node 포함 -> 더 큰 penalty

- [x] **Step 3: repair expectation 고정**

repair는 아래만 하도록 테스트로 고정한다.
- extra node prune
- missing required edge 추가
- missing required node 보완

full rewrite가 발생하지 않도록 보정 전후 차이를 검증한다.

---

## Task 4: equivalence scorer를 edge-sensitive하게 보강

**Files:**
- Modify: `llm_interface/harness_core/workflow_guidance/workflow_equivalence.py`
- Modify: `tests/harness_core/test_workflow_equivalence.py`

- [x] **Step 1: edge coverage 가중치 재조정**

현재 node presence 중심으로 점수가 높게 나오는 intent가 있으면, `required_edges` 비중을 올린다.

- [x] **Step 2: optional edge 개념 도입 여부 검토**

필요 시 `optional_edges`를 template에 도입한다. 단, 처음부터 복잡하게 만들지 말고 필요한 intent에만 제한적으로 적용한다.

- [x] **Step 3: forbidden edge / structurally implausible edge penalty 검토**

실제 분석 흐름과 어긋나는 edge가 있을 때 penalty를 더 줄지 판단한다.

---

## Task 5: repair 로직을 edge-driven으로 미세 조정

**Files:**
- Modify: `llm_interface/harness_core/workflow_guidance/workflow_repair.py`
- Modify: `tests/harness_core/test_workflow_repair.py`

- [x] **Step 1: missing required edge 보완 우선순위 상향**

현재는 node 보완과 prune 중심이므로, edge-driven correction 품질을 올린다.

- [x] **Step 2: optional node는 함부로 제거하지 않도록 intent별 기준 재검토**

canonical path 바깥이라도 valid analysis branch면 남길지 여부를 template 기준으로 결정한다.

- [x] **Step 3: repair summary를 더 구조적으로 남길지 검토**

예:
- `removed_extra_node`
- `added_required_node`
- `added_required_edge`

연구 분석용이면 free-text보다 typed summary가 더 좋다.

---

## Task 6: template-coverage 및 quality 리포트 준비

**Files:**
- Create/Modify: `docs/superpowers/experiments/*.md`
- Optional Create: `llm_interface/harness_core/template_report.py`

- [x] **Step 1: template coverage 표 작성**

최소 포함 항목:
- intent
- required node 수
- required edge 수
- optional node 수
- covered category

- [x] **Step 2: quality benchmark 기록 형식 정리**

예시 비교 항목:
- exact match score
- missing-edge score
- extra-node score
- repair after score

- [x] **Step 3: 결과 문서 저장 위치 고정**

`docs/superpowers/experiments/` 아래 날짜별 문서로 축적한다.

---

## Task 7: 검증 실행

**Files:**
- Modify/Create: `tests/...`

- [x] **Step 1: registry / template 일치 검증**

모든 template의 node/port가 registry에 존재하는지 확인한다.

- [x] **Step 2: 핵심 테스트 실행**

권장 실행:

```bash
cd /home/ydj/main/ComfyBIO_biopython
python -m pytest tests/harness_core/test_template_registry.py -v
python -m pytest tests/harness_core/test_workflow_equivalence.py -v
python -m pytest tests/harness_core/test_workflow_repair.py -v
python -m pytest tests/harness_core/test_template_fixtures.py -v
```

- [x] **Step 3: hybrid regression suite 재실행**

기존 `llm_runner`, `workflow_history`, `generate_api` 테스트까지 함께 돌려 회귀가 없는지 확인한다.

---

## Expected Outcomes

구현 완료 후 다음을 만족해야 한다.

1. 각 canonical template가 실제 분석 workflow의 핵심 edge 흐름을 포함한다.
2. equivalence score가 “노드 존재”보다 “실제 흐름”을 더 잘 반영한다.
3. repair가 missing edge와 missing node를 실제 분석 흐름 기준으로 보완한다.
4. intent coverage가 현재 5개보다 넓어져 더 많은 자연어 요청을 canonical family에 매핑할 수 있다.
5. fixture 기반 검증으로 template 품질을 반복 가능하게 평가할 수 있다.

---

## Non-Goals

- template를 full generator로 바꾸지 않는다.
- 자유 생성 경로를 제거하지 않는다.
- 모든 159개 노드 조합을 완전 포괄하는 template ontology를 한 번에 만들지 않는다.
- repair 단계에서 workflow 전체를 canonical template로 대체하지 않는다.
