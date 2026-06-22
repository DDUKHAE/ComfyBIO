# Multi-Domain NL Workflow Generation — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tool Selection Registry(TSR), Multi-path Gold Criteria, Domain Plugin 인터페이스, HeldOutQuery 스키마를 구현한다. 이 Foundation이 CS2~CS5 도메인 plan의 공통 선행 조건이다.

**Architecture:** `llm_interface/llm_core/` 아래 `tsr/`, `gold/`, `benchmark/` 세 서브패키지를 신규 추가한다. TSR은 YAML rule 파일을 로드하는 rule engine이고, Gold는 Tiered 판정 로직이며, benchmark는 Domain Plugin ABC와 query 스키마를 제공한다. CS1(ComfyBIO)의 기존 코드는 이 plan에서 수정하지 않는다.

**Tech Stack:** Python 3.11+, dataclasses, PyYAML, pytest

## Global Constraints

- 모든 신규 파일은 `llm_interface/llm_core/` 하위에 위치한다.
- 테스트는 `tests/llm_core/` 하위에 위치한다.
- 테스트 실행: `cd /tmp && PYTHONPATH= python -m pytest /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/ -q`
- YAML 파싱에 `pyyaml` 사용 (`import yaml`)
- 외부 LLM, ComfyUI 런타임을 import하지 않는다 — 이 Foundation은 독립 실행 가능해야 한다.
- 모든 public 함수는 type annotation을 포함한다.

## Sub-plan 분리 안내

이 plan은 6개 plan 중 Plan 1이다.

| Plan | 내용 | 선행 조건 |
|------|-----|---------|
| **Plan 1 (본 문서)** | Foundation: TSR, Gold, Plugin ABC | 없음 |
| Plan 2 | CS2: ComfyTranscriptomics | Plan 1 |
| Plan 3 | CS3: ComfyChem | Plan 1 |
| Plan 4 | CS4: ComfyProteomics | Plan 1 |
| Plan 5 | CS5: ComfyEpigenomics | Plan 1 |
| Plan 6 | Cross-domain Meta-analysis | Plan 1~5 |

---

## File Structure

```
llm_interface/llm_core/
  tsr/
    __init__.py           # ToolValidity, ToolChoice, StepRule, DomainTSR export
    schema.py             # TSR 데이터 모델 (dataclasses)
    engine.py             # TSREngine — rule 평가 및 tool 조회
    loader.py             # YAML → DomainTSR 변환
    domains/
      bioinformatics.yaml # CS1 규칙 (Biopython — alternative 제한적이므로 canonical 위주)
      transcriptomics.yaml # CS2 규칙 샘플 (alignment, DE 분기 포함)
  gold/
    __init__.py           # TieredGold, GoldEvaluator, Verdict export
    schema.py             # Gold 데이터 모델 (dataclasses)
    evaluator.py          # GoldEvaluator — tier 판정 로직
  benchmark/
    __init__.py           # DomainPlugin, HeldOutQuery, ToolSpecificity export
    domain_plugin.py      # DomainPlugin ABC
    query_schema.py       # HeldOutQuery, ToolSpecificity, Difficulty dataclasses

tests/llm_core/
  test_tsr_schema.py      # ToolChoice, StepRule, DomainTSR 직렬화
  test_tsr_engine.py      # TSREngine.canonical / is_valid / resolve
  test_tsr_loader.py      # YAML → DomainTSR 로딩
  test_gold_schema.py     # TieredGold 직렬화
  test_gold_evaluator.py  # GoldEvaluator 판정 4가지 경우
  test_domain_plugin.py   # DomainPlugin ABC 계약 테스트
  test_query_schema.py    # HeldOutQuery 생성 및 직렬화
```

---

### Task 1: TSR 데이터 모델

**Files:**
- Create: `llm_interface/llm_core/tsr/__init__.py`
- Create: `llm_interface/llm_core/tsr/schema.py`
- Test: `tests/llm_core/test_tsr_schema.py`

**Interfaces:**
- Produces: `ToolValidity`, `ToolChoice`, `StepRule`, `DomainTSR` (dataclasses)

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/llm_core/test_tsr_schema.py`:
```python
from tsr.schema import DomainTSR, StepRule, ToolChoice, ToolValidity


def test_tool_choice_canonical():
    tc = ToolChoice(tool_id="STAR", validity=ToolValidity.CANONICAL, reason="splice-aware")
    assert tc.tool_id == "STAR"
    assert tc.validity == ToolValidity.CANONICAL


def test_step_rule_contains_tools():
    rule = StepRule(
        step_id="alignment",
        step_name="Genome Alignment",
        condition="data_type == 'short_read'",
        tools=[
            ToolChoice("STAR", ToolValidity.CANONICAL, "splice-aware"),
            ToolChoice("HISAT2", ToolValidity.ALTERNATIVE_VALID, "memory efficient"),
            ToolChoice("minimap2", ToolValidity.INVALID, "long-read only"),
        ],
    )
    assert len(rule.tools) == 3
    assert rule.tools[0].validity == ToolValidity.CANONICAL


def test_domain_tsr_step_count():
    tsr = DomainTSR(
        domain_id="transcriptomics",
        description="Bulk and single-cell RNA-seq analysis",
        steps=[
            StepRule("alignment", "Genome Alignment", "True", []),
            StepRule("de_analysis", "Differential Expression", "True", []),
        ],
    )
    assert len(tsr.steps) == 2
    assert tsr.domain_id == "transcriptomics"
```

- [ ] **Step 2: 실패 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_schema.py -v
```
Expected: `ModuleNotFoundError: No module named 'tsr'`

- [ ] **Step 3: 구현**

`llm_interface/llm_core/tsr/schema.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ToolValidity(str, Enum):
    CANONICAL = "canonical"
    ALTERNATIVE_VALID = "alternative_valid"
    INVALID = "invalid"


@dataclass
class ToolChoice:
    tool_id: str
    validity: ToolValidity
    reason: str = ""


@dataclass
class StepRule:
    step_id: str
    step_name: str
    condition: str
    tools: list[ToolChoice] = field(default_factory=list)


@dataclass
class DomainTSR:
    domain_id: str
    description: str
    steps: list[StepRule] = field(default_factory=list)
```

`llm_interface/llm_core/tsr/__init__.py`:
```python
from .schema import DomainTSR, StepRule, ToolChoice, ToolValidity

__all__ = ["DomainTSR", "StepRule", "ToolChoice", "ToolValidity"]
```

- [ ] **Step 4: 통과 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_schema.py -v
```
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add llm_interface/llm_core/tsr/__init__.py \
        llm_interface/llm_core/tsr/schema.py \
        tests/llm_core/test_tsr_schema.py
git commit -m "feat(tsr): add TSR schema dataclasses"
```

---

### Task 2: TSR Rule Engine

**Files:**
- Create: `llm_interface/llm_core/tsr/engine.py`
- Test: `tests/llm_core/test_tsr_engine.py`

**Interfaces:**
- Consumes: `DomainTSR`, `StepRule`, `ToolChoice`, `ToolValidity` (Task 1)
- Produces: `TSREngine(tsr: DomainTSR)` — `.canonical(step_id, ctx) -> str | None`, `.is_valid(step_id, tool_id, ctx) -> ToolValidity`, `.resolve(step_id, ctx) -> list[ToolChoice]`

condition 문자열은 Python `eval()`로 평가하되 `context` dict만 namespace로 제공한다. 조건이 `True` 리터럴이면 항상 매칭.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/llm_core/test_tsr_engine.py`:
```python
import pytest
from tsr.schema import DomainTSR, StepRule, ToolChoice, ToolValidity
from tsr.engine import TSREngine


@pytest.fixture
def rna_tsr():
    return DomainTSR(
        domain_id="transcriptomics",
        description="test",
        steps=[
            StepRule(
                step_id="alignment",
                step_name="Genome Alignment",
                condition="data_type == 'short_read' and read_length >= 75",
                tools=[
                    ToolChoice("STAR", ToolValidity.CANONICAL, "splice-aware"),
                    ToolChoice("HISAT2", ToolValidity.ALTERNATIVE_VALID, "memory efficient"),
                    ToolChoice("minimap2", ToolValidity.INVALID, "long-read only"),
                ],
            ),
            StepRule(
                step_id="alignment",
                step_name="Genome Alignment",
                condition="data_type == 'long_read'",
                tools=[
                    ToolChoice("minimap2", ToolValidity.CANONICAL, "long-read specialist"),
                    ToolChoice("STAR", ToolValidity.INVALID, "short-read only"),
                ],
            ),
            StepRule(
                step_id="de_analysis",
                step_name="Differential Expression",
                condition="n_samples_per_group < 6",
                tools=[
                    ToolChoice("edgeR", ToolValidity.CANONICAL, "small sample"),
                    ToolChoice("DESeq2", ToolValidity.ALTERNATIVE_VALID, "general"),
                ],
            ),
            StepRule(
                step_id="de_analysis",
                step_name="Differential Expression",
                condition="n_samples_per_group >= 6",
                tools=[
                    ToolChoice("DESeq2", ToolValidity.CANONICAL, "large sample"),
                    ToolChoice("edgeR", ToolValidity.ALTERNATIVE_VALID, "general"),
                    ToolChoice("limma_voom", ToolValidity.ALTERNATIVE_VALID, "large study"),
                ],
            ),
        ],
    )


def test_canonical_short_read(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.canonical("alignment", ctx) == "STAR"


def test_canonical_long_read(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "long_read"}
    assert engine.canonical("alignment", ctx) == "minimap2"


def test_is_valid_invalid_tool(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.is_valid("alignment", "minimap2", ctx) == ToolValidity.INVALID


def test_is_valid_alternative(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.is_valid("alignment", "HISAT2", ctx) == ToolValidity.ALTERNATIVE_VALID


def test_canonical_de_small_sample(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"n_samples_per_group": 3}
    assert engine.canonical("de_analysis", ctx) == "edgeR"


def test_canonical_de_large_sample(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"n_samples_per_group": 8}
    assert engine.canonical("de_analysis", ctx) == "DESeq2"


def test_unknown_step_returns_none(rna_tsr):
    engine = TSREngine(rna_tsr)
    assert engine.canonical("nonexistent_step", {}) is None


def test_unknown_tool_returns_invalid(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.is_valid("alignment", "bowtie2", ctx) == ToolValidity.INVALID
```

- [ ] **Step 2: 실패 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_engine.py -v
```
Expected: `ModuleNotFoundError: No module named 'tsr.engine'`

- [ ] **Step 3: 구현**

`llm_interface/llm_core/tsr/engine.py`:
```python
from __future__ import annotations

from .schema import DomainTSR, ToolChoice, ToolValidity

_SAFE_BUILTINS: dict = {}


class TSREngine:
    def __init__(self, tsr: DomainTSR) -> None:
        self._tsr = tsr

    def resolve(self, step_id: str, context: dict) -> list[ToolChoice]:
        result: list[ToolChoice] = []
        for rule in self._tsr.steps:
            if rule.step_id == step_id and self._eval(rule.condition, context):
                result.extend(rule.tools)
        return result

    def canonical(self, step_id: str, context: dict) -> str | None:
        for tc in self.resolve(step_id, context):
            if tc.validity == ToolValidity.CANONICAL:
                return tc.tool_id
        return None

    def is_valid(self, step_id: str, tool_id: str, context: dict) -> ToolValidity:
        for tc in self.resolve(step_id, context):
            if tc.tool_id == tool_id:
                return tc.validity
        return ToolValidity.INVALID

    def _eval(self, condition: str, context: dict) -> bool:
        try:
            return bool(eval(condition, {"__builtins__": _SAFE_BUILTINS}, context))  # noqa: S307
        except Exception:
            return False
```

`llm_interface/llm_core/tsr/__init__.py` 업데이트:
```python
from .engine import TSREngine
from .schema import DomainTSR, StepRule, ToolChoice, ToolValidity

__all__ = ["DomainTSR", "StepRule", "ToolChoice", "ToolValidity", "TSREngine"]
```

- [ ] **Step 4: 통과 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_engine.py -v
```
Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add llm_interface/llm_core/tsr/engine.py \
        llm_interface/llm_core/tsr/__init__.py \
        tests/llm_core/test_tsr_engine.py
git commit -m "feat(tsr): add TSREngine rule evaluator"
```

---

### Task 3: TSR YAML Loader + Domain Files

**Files:**
- Create: `llm_interface/llm_core/tsr/loader.py`
- Create: `llm_interface/llm_core/tsr/domains/bioinformatics.yaml`
- Create: `llm_interface/llm_core/tsr/domains/transcriptomics.yaml`
- Test: `tests/llm_core/test_tsr_loader.py`

**Interfaces:**
- Consumes: `DomainTSR`, `StepRule`, `ToolChoice`, `ToolValidity` (Task 1)
- Produces: `load_domain_tsr(domain_id: str) -> DomainTSR`, `list_domains() -> list[str]`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/llm_core/test_tsr_loader.py`:
```python
import pytest
from tsr.loader import list_domains, load_domain_tsr
from tsr.schema import ToolValidity


def test_list_domains_includes_bioinformatics():
    domains = list_domains()
    assert "bioinformatics" in domains


def test_list_domains_includes_transcriptomics():
    domains = list_domains()
    assert "transcriptomics" in domains


def test_load_bioinformatics_tsr():
    tsr = load_domain_tsr("bioinformatics")
    assert tsr.domain_id == "bioinformatics"
    assert len(tsr.steps) >= 1


def test_load_transcriptomics_tsr():
    tsr = load_domain_tsr("transcriptomics")
    assert tsr.domain_id == "transcriptomics"
    step_ids = [s.step_id for s in tsr.steps]
    assert "alignment" in step_ids
    assert "de_analysis" in step_ids


def test_transcriptomics_alignment_has_canonical():
    from tsr.engine import TSREngine
    tsr = load_domain_tsr("transcriptomics")
    engine = TSREngine(tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.canonical("alignment", ctx) == "STAR"


def test_load_unknown_domain_raises():
    with pytest.raises(FileNotFoundError):
        load_domain_tsr("nonexistent_domain_xyz")
```

- [ ] **Step 2: 실패 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_loader.py -v
```
Expected: `ModuleNotFoundError: No module named 'tsr.loader'`

- [ ] **Step 3: YAML 도메인 파일 작성**

`llm_interface/llm_core/tsr/domains/bioinformatics.yaml`:
```yaml
domain_id: bioinformatics
description: "Sequence bioinformatics via Biopython — CS1"
steps:
  - step_id: sequence_parsing
    step_name: Sequence Parsing
    condition: "True"
    tools:
      - tool_id: biopython_seqio
        validity: canonical
        reason: "Primary Biopython sequence I/O"

  - step_id: pairwise_alignment
    step_name: Pairwise Alignment
    condition: "True"
    tools:
      - tool_id: biopython_pairwise2
        validity: canonical
        reason: "Biopython built-in pairwise aligner"
      - tool_id: biopython_align_pairwisealigner
        validity: alternative_valid
        reason: "Newer Biopython PairwiseAligner API"

  - step_id: multiple_alignment
    step_name: Multiple Sequence Alignment
    condition: "True"
    tools:
      - tool_id: muscle
        validity: canonical
        reason: "Fast and accurate MSA"
      - tool_id: clustalw
        validity: alternative_valid
        reason: "Classic MSA tool"
      - tool_id: mafft
        validity: alternative_valid
        reason: "High accuracy for divergent sequences"

  - step_id: blast_search
    step_name: BLAST Search
    condition: "True"
    tools:
      - tool_id: biopython_blast_ncbiwww
        validity: canonical
        reason: "NCBI remote BLAST via Biopython"
      - tool_id: blast_cli
        validity: alternative_valid
        reason: "Local BLAST+ command-line"

  - step_id: phylogeny
    step_name: Phylogenetic Analysis
    condition: "True"
    tools:
      - tool_id: biopython_phylo
        validity: canonical
        reason: "Biopython Phylo module"

  - step_id: entrez_fetch
    step_name: Entrez Database Fetch
    condition: "True"
    tools:
      - tool_id: biopython_entrez
        validity: canonical
        reason: "Biopython Entrez efetch/esearch"
```

`llm_interface/llm_core/tsr/domains/transcriptomics.yaml`:
```yaml
domain_id: transcriptomics
description: "Bulk RNA-seq and scRNA-seq analysis — CS2"
steps:
  - step_id: adapter_trimming
    step_name: Adapter Trimming
    condition: "True"
    tools:
      - tool_id: fastp
        validity: canonical
        reason: "Fast, all-in-one quality control"
      - tool_id: trimmomatic
        validity: alternative_valid
        reason: "Widely used, highly configurable"
      - tool_id: cutadapt
        validity: alternative_valid
        reason: "Flexible adapter trimmer"

  - step_id: alignment
    step_name: Genome Alignment
    condition: "data_type == 'short_read' and read_length >= 75"
    tools:
      - tool_id: STAR
        validity: canonical
        reason: "Splice-aware aligner, RNA-seq standard"
      - tool_id: HISAT2
        validity: alternative_valid
        reason: "Memory-efficient splice-aware aligner"
      - tool_id: minimap2
        validity: invalid
        reason: "Designed for long reads; cannot handle short-read RNA-seq error profile"

  - step_id: alignment
    step_name: Genome Alignment
    condition: "data_type == 'long_read'"
    tools:
      - tool_id: minimap2
        validity: canonical
        reason: "Optimal for long-read RNA-seq (PacBio/Nanopore)"
      - tool_id: STAR
        validity: invalid
        reason: "Short-read aligner; fails on long-read error rates"

  - step_id: pseudo_alignment
    step_name: Pseudo-alignment / Quantification
    condition: "quantification_only == True"
    tools:
      - tool_id: kallisto
        validity: canonical
        reason: "Fast pseudo-alignment, sufficient for quantification"
      - tool_id: salmon
        validity: alternative_valid
        reason: "Quasi-mapping with GC-bias correction"

  - step_id: de_analysis
    step_name: Differential Expression Analysis
    condition: "n_samples_per_group < 6"
    tools:
      - tool_id: edgeR
        validity: canonical
        reason: "Best performance with small sample sizes"
      - tool_id: DESeq2
        validity: alternative_valid
        reason: "Acceptable but less optimal for n<6"

  - step_id: de_analysis
    step_name: Differential Expression Analysis
    condition: "n_samples_per_group >= 6"
    tools:
      - tool_id: DESeq2
        validity: canonical
        reason: "Negative binomial model, well-validated for bulk RNA-seq"
      - tool_id: edgeR
        validity: alternative_valid
        reason: "Also valid for larger sample sizes"
      - tool_id: limma_voom
        validity: alternative_valid
        reason: "Good for large studies"

  - step_id: sc_clustering
    step_name: Single-cell Clustering
    condition: "assay == 'scrna_seq'"
    tools:
      - tool_id: leiden
        validity: canonical
        reason: "Superior community detection; default in Scanpy"
      - tool_id: louvain
        validity: alternative_valid
        reason: "Widely used; predecessor to Leiden"
      - tool_id: kmeans
        validity: invalid
        reason: "Assumes spherical clusters; inappropriate for single-cell data"

  - step_id: sc_annotation
    step_name: Cell Type Annotation
    condition: "assay == 'scrna_seq'"
    tools:
      - tool_id: SingleR
        validity: canonical
        reason: "Reference-based automated annotation"
      - tool_id: CellTypist
        validity: alternative_valid
        reason: "Machine learning-based annotation"
```

- [ ] **Step 4: Loader 구현**

`llm_interface/llm_core/tsr/loader.py`:
```python
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .schema import DomainTSR, StepRule, ToolChoice, ToolValidity

_DOMAINS_DIR = Path(__file__).resolve().parent / "domains"


def list_domains() -> list[str]:
    return sorted(p.stem for p in _DOMAINS_DIR.glob("*.yaml"))


@lru_cache(maxsize=None)
def load_domain_tsr(domain_id: str) -> DomainTSR:
    path = _DOMAINS_DIR / f"{domain_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No TSR domain file for '{domain_id}': {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _parse_domain(data)


def _parse_domain(data: dict) -> DomainTSR:
    steps = [_parse_step(s) for s in data.get("steps", [])]
    return DomainTSR(
        domain_id=data["domain_id"],
        description=data.get("description", ""),
        steps=steps,
    )


def _parse_step(data: dict) -> StepRule:
    tools = [_parse_tool(t) for t in data.get("tools", [])]
    return StepRule(
        step_id=data["step_id"],
        step_name=data.get("step_name", data["step_id"]),
        condition=data.get("condition", "True"),
        tools=tools,
    )


def _parse_tool(data: dict) -> ToolChoice:
    return ToolChoice(
        tool_id=data["tool_id"],
        validity=ToolValidity(data["validity"]),
        reason=data.get("reason", ""),
    )
```

`llm_interface/llm_core/tsr/__init__.py` 업데이트:
```python
from .engine import TSREngine
from .loader import list_domains, load_domain_tsr
from .schema import DomainTSR, StepRule, ToolChoice, ToolValidity

__all__ = [
    "DomainTSR", "StepRule", "ToolChoice", "ToolValidity",
    "TSREngine",
    "load_domain_tsr", "list_domains",
]
```

- [ ] **Step 5: 통과 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_loader.py -v
```
Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
git add llm_interface/llm_core/tsr/loader.py \
        llm_interface/llm_core/tsr/domains/ \
        llm_interface/llm_core/tsr/__init__.py \
        tests/llm_core/test_tsr_loader.py
git commit -m "feat(tsr): add YAML loader and CS1/CS2 domain rule files"
```

---

### Task 4: Gold Criteria 데이터 모델

**Files:**
- Create: `llm_interface/llm_core/gold/__init__.py`
- Create: `llm_interface/llm_core/gold/schema.py`
- Test: `tests/llm_core/test_gold_schema.py`

**Interfaces:**
- Produces: `TieredGold`, `CanonicalGold`, `AlternativeGold`, `AdversarialOverride`, `Verdict`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/llm_core/test_gold_schema.py`:
```python
from gold.schema import AlternativeGold, CanonicalGold, TieredGold, Verdict


def test_tiered_gold_creation():
    gold = TieredGold(
        query_id="TR_006",
        family="de_analysis",
        context={"n_samples_per_group": 4},
        canonical=CanonicalGold(
            tools=["edgeR"],
            expected_output_criteria={"top10_overlap_min": 1.0},
        ),
        alternatives=AlternativeGold(
            tools=["DESeq2"],
            functional_equivalence_criteria={"top10_overlap_with_canonical": ">= 0.80"},
        ),
        invalid_tools=["kallisto", "STAR"],
    )
    assert gold.query_id == "TR_006"
    assert "edgeR" in gold.canonical.tools
    assert "DESeq2" in gold.alternatives.tools
    assert "kallisto" in gold.invalid_tools


def test_verdict_values():
    assert Verdict.CORRECT_CANONICAL != Verdict.CORRECT_ALTERNATIVE
    assert Verdict.CRITICAL_ERROR != Verdict.INCORRECT
```

- [ ] **Step 2: 실패 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_gold_schema.py -v
```
Expected: `ModuleNotFoundError: No module named 'gold'`

- [ ] **Step 3: 구현**

`llm_interface/llm_core/gold/schema.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    CORRECT_CANONICAL = "correct_canonical"
    CORRECT_ALTERNATIVE = "correct_alternative"
    INCORRECT = "incorrect"
    CRITICAL_ERROR = "critical_error"


@dataclass
class CanonicalGold:
    tools: list[str]
    expected_output_criteria: dict


@dataclass
class AlternativeGold:
    tools: list[str]
    functional_equivalence_criteria: dict


@dataclass
class AdversarialOverride:
    bad_hint_tool: str
    correct_behaviors: list[str]


@dataclass
class TieredGold:
    query_id: str
    family: str
    context: dict
    canonical: CanonicalGold
    alternatives: AlternativeGold
    invalid_tools: list[str] = field(default_factory=list)
    adversarial_override: AdversarialOverride | None = None
```

`llm_interface/llm_core/gold/__init__.py`:
```python
from .schema import (
    AdversarialOverride,
    AlternativeGold,
    CanonicalGold,
    TieredGold,
    Verdict,
)

__all__ = [
    "AdversarialOverride", "AlternativeGold", "CanonicalGold",
    "TieredGold", "Verdict",
]
```

- [ ] **Step 4: 통과 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_gold_schema.py -v
```
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add llm_interface/llm_core/gold/__init__.py \
        llm_interface/llm_core/gold/schema.py \
        tests/llm_core/test_gold_schema.py
git commit -m "feat(gold): add TieredGold schema dataclasses"
```

---

### Task 5: Gold Evaluator

**Files:**
- Create: `llm_interface/llm_core/gold/evaluator.py`
- Test: `tests/llm_core/test_gold_evaluator.py`

**Interfaces:**
- Consumes: `TieredGold`, `Verdict` (Task 4)
- Produces: `GoldEvaluator(gold: TieredGold)` — `.evaluate(generated_tools: list[str], output: dict) -> Verdict`

functional_equivalence_criteria의 `">= 0.80"` 같은 표현식은 `_eval_criterion(value, threshold_expr)` 내부 메서드로 파싱한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/llm_core/test_gold_evaluator.py`:
```python
import pytest
from gold.schema import AdversarialOverride, AlternativeGold, CanonicalGold, TieredGold
from gold.evaluator import GoldEvaluator
from gold.schema import Verdict


@pytest.fixture
def de_gold():
    return TieredGold(
        query_id="TR_006",
        family="de_analysis",
        context={"n_samples_per_group": 4},
        canonical=CanonicalGold(
            tools=["edgeR"],
            expected_output_criteria={"top10_overlap_min": 1.0},
        ),
        alternatives=AlternativeGold(
            tools=["DESeq2", "limma_voom"],
            functional_equivalence_criteria={"top10_overlap_with_canonical": ">= 0.80"},
        ),
        invalid_tools=["kallisto", "STAR", "fastp"],
        adversarial_override=AdversarialOverride(
            bad_hint_tool="DESeq2",
            correct_behaviors=["use_edgeR", "warn_sample_size"],
        ),
    )


def test_correct_canonical(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {"top10_overlap_min": 1.0}
    verdict = evaluator.evaluate(["edgeR"], output)
    assert verdict == Verdict.CORRECT_CANONICAL


def test_correct_alternative_above_threshold(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {"top10_overlap_with_canonical": 0.90}
    verdict = evaluator.evaluate(["DESeq2"], output)
    assert verdict == Verdict.CORRECT_ALTERNATIVE


def test_correct_alternative_below_threshold(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {"top10_overlap_with_canonical": 0.70}
    verdict = evaluator.evaluate(["DESeq2"], output)
    assert verdict == Verdict.INCORRECT


def test_critical_error_invalid_tool(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {}
    verdict = evaluator.evaluate(["kallisto"], output)
    assert verdict == Verdict.CRITICAL_ERROR


def test_incorrect_unknown_tool(de_gold):
    evaluator = GoldEvaluator(de_gold)
    output = {}
    verdict = evaluator.evaluate(["some_unknown_tool"], output)
    assert verdict == Verdict.INCORRECT
```

- [ ] **Step 2: 실패 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_gold_evaluator.py -v
```
Expected: `ModuleNotFoundError: No module named 'gold.evaluator'`

- [ ] **Step 3: 구현**

`llm_interface/llm_core/gold/evaluator.py`:
```python
from __future__ import annotations

import re

from .schema import TieredGold, Verdict


class GoldEvaluator:
    def __init__(self, gold: TieredGold) -> None:
        self._gold = gold

    def evaluate(self, generated_tools: list[str], output: dict) -> Verdict:
        # Invalid tool → immediate CRITICAL_ERROR
        if any(t in self._gold.invalid_tools for t in generated_tools):
            return Verdict.CRITICAL_ERROR

        # Canonical match
        if set(generated_tools) == set(self._gold.canonical.tools):
            if self._check_canonical(output):
                return Verdict.CORRECT_CANONICAL

        # Alternative match
        if any(t in self._gold.alternatives.tools for t in generated_tools):
            if self._check_functional_equivalence(output):
                return Verdict.CORRECT_ALTERNATIVE

        return Verdict.INCORRECT

    def _check_canonical(self, output: dict) -> bool:
        for key, threshold in self._gold.canonical.expected_output_criteria.items():
            if key not in output:
                return False
            if not self._eval_criterion(output[key], threshold):
                return False
        return True

    def _check_functional_equivalence(self, output: dict) -> bool:
        for key, threshold_expr in self._gold.alternatives.functional_equivalence_criteria.items():
            if key not in output:
                return False
            if not self._eval_criterion(output[key], threshold_expr):
                return False
        return True

    @staticmethod
    def _eval_criterion(value: float, threshold: float | str) -> bool:
        if isinstance(threshold, (int, float)):
            return value >= threshold
        # Parse ">= 0.80", "== 1.0", "> 0.5" etc.
        m = re.fullmatch(r"\s*(>=|<=|==|>|<)\s*([0-9.]+)\s*", str(threshold))
        if not m:
            return False
        op, rhs = m.group(1), float(m.group(2))
        return {
            ">=": value >= rhs,
            "<=": value <= rhs,
            "==": value == rhs,
            ">": value > rhs,
            "<": value < rhs,
        }[op]
```

`llm_interface/llm_core/gold/__init__.py` 업데이트:
```python
from .evaluator import GoldEvaluator
from .schema import (
    AdversarialOverride,
    AlternativeGold,
    CanonicalGold,
    TieredGold,
    Verdict,
)

__all__ = [
    "AdversarialOverride", "AlternativeGold", "CanonicalGold",
    "TieredGold", "Verdict", "GoldEvaluator",
]
```

- [ ] **Step 4: 통과 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_gold_evaluator.py -v
```
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add llm_interface/llm_core/gold/evaluator.py \
        llm_interface/llm_core/gold/__init__.py \
        tests/llm_core/test_gold_evaluator.py
git commit -m "feat(gold): add GoldEvaluator with tiered verdict logic"
```

---

### Task 6: HeldOutQuery 스키마 + DomainPlugin ABC

**Files:**
- Create: `llm_interface/llm_core/benchmark/__init__.py`
- Create: `llm_interface/llm_core/benchmark/query_schema.py`
- Create: `llm_interface/llm_core/benchmark/domain_plugin.py`
- Test: `tests/llm_core/test_query_schema.py`
- Test: `tests/llm_core/test_domain_plugin.py`

**Interfaces:**
- Consumes: `DomainTSR` (Task 1), `TieredGold` (Task 4)
- Produces: `HeldOutQuery`, `ToolSpecificity`, `Difficulty`, `DomainPlugin` ABC

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/llm_core/test_query_schema.py`:
```python
from benchmark.query_schema import Difficulty, HeldOutQuery, ToolSpecificity


def test_query_creation():
    q = HeldOutQuery(
        query_id="TR_006",
        domain_id="transcriptomics",
        family="de_analysis",
        nl_text="Use edgeR to find DEGs between treated and control groups.",
        difficulty=Difficulty.EASY,
        tool_specificity=ToolSpecificity.TOOL_SPECIFIED,
        context={"n_samples_per_group": 4, "data_type": "bulk_rna_seq"},
        fixture_path="fixtures/transcriptomics/GSE_example_counts.tsv",
    )
    assert q.query_id == "TR_006"
    assert q.tool_specificity == ToolSpecificity.TOOL_SPECIFIED
    assert q.adversarial_hint_tool is None


def test_adversarial_query():
    q = HeldOutQuery(
        query_id="TR_ADV_001",
        domain_id="transcriptomics",
        family="alignment",
        nl_text="Align these nanopore reads using STAR.",
        difficulty=Difficulty.ADVERSARIAL,
        tool_specificity=ToolSpecificity.ADVERSARIAL,
        context={"data_type": "long_read", "platform": "nanopore"},
        fixture_path="fixtures/transcriptomics/nanopore_reads.fastq",
        adversarial_hint_tool="STAR",
    )
    assert q.adversarial_hint_tool == "STAR"
    assert q.difficulty == Difficulty.ADVERSARIAL


def test_tool_specificity_values():
    assert ToolSpecificity.TOOL_SPECIFIED != ToolSpecificity.GOAL_SPECIFIED
    assert ToolSpecificity.CONTEXT_ONLY != ToolSpecificity.ADVERSARIAL
```

`tests/llm_core/test_domain_plugin.py`:
```python
import pytest
from benchmark.domain_plugin import DomainPlugin
from tsr.schema import DomainTSR
from gold.schema import TieredGold
from benchmark.query_schema import HeldOutQuery


class _ConcretePlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return "test_domain"

    @property
    def domain_description(self) -> str:
        return "Test domain for unit tests"

    def get_tsr(self) -> DomainTSR:
        return DomainTSR(domain_id="test_domain", description="test")

    def list_families(self) -> list[str]:
        return ["family_a", "family_b"]

    def load_gold(self, query_id: str) -> TieredGold:
        raise NotImplementedError

    def run_workflow(self, query: HeldOutQuery) -> dict:
        return {"tools": ["tool_a"], "output": {}}


def test_concrete_plugin_implements_abc():
    plugin = _ConcretePlugin()
    assert plugin.domain_id == "test_domain"
    assert "family_a" in plugin.list_families()


def test_abstract_plugin_cannot_be_instantiated():
    with pytest.raises(TypeError):
        DomainPlugin()  # type: ignore[abstract]
```

- [ ] **Step 2: 실패 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_query_schema.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_domain_plugin.py -v
```
Expected: `ModuleNotFoundError: No module named 'benchmark'`

- [ ] **Step 3: 구현**

`llm_interface/llm_core/benchmark/query_schema.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ToolSpecificity(str, Enum):
    TOOL_SPECIFIED = "tool_specified"
    GOAL_SPECIFIED = "goal_specified"
    CONTEXT_ONLY = "context_only"
    ADVERSARIAL = "adversarial"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADVERSARIAL = "adversarial"


@dataclass
class HeldOutQuery:
    query_id: str
    domain_id: str
    family: str
    nl_text: str
    difficulty: Difficulty
    tool_specificity: ToolSpecificity
    context: dict
    fixture_path: str
    adversarial_hint_tool: str | None = None
```

`llm_interface/llm_core/benchmark/domain_plugin.py`:
```python
from __future__ import annotations

from abc import ABC, abstractmethod

from gold.schema import TieredGold
from tsr.schema import DomainTSR

from .query_schema import HeldOutQuery


class DomainPlugin(ABC):
    @property
    @abstractmethod
    def domain_id(self) -> str: ...

    @property
    @abstractmethod
    def domain_description(self) -> str: ...

    @abstractmethod
    def get_tsr(self) -> DomainTSR: ...

    @abstractmethod
    def list_families(self) -> list[str]: ...

    @abstractmethod
    def load_gold(self, query_id: str) -> TieredGold: ...

    @abstractmethod
    def run_workflow(self, query: HeldOutQuery) -> dict:
        """Execute query and return {'tools': list[str], 'output': dict}."""
        ...
```

`llm_interface/llm_core/benchmark/__init__.py`:
```python
from .domain_plugin import DomainPlugin
from .query_schema import Difficulty, HeldOutQuery, ToolSpecificity

__all__ = ["DomainPlugin", "HeldOutQuery", "ToolSpecificity", "Difficulty"]
```

- [ ] **Step 4: 통과 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_query_schema.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_domain_plugin.py -v
```
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add llm_interface/llm_core/benchmark/ \
        tests/llm_core/test_query_schema.py \
        tests/llm_core/test_domain_plugin.py
git commit -m "feat(benchmark): add HeldOutQuery schema and DomainPlugin ABC"
```

---

### Task 7: 전체 테스트 통과 확인 및 최종 Commit

**Files:**
- Modify: (없음 — 통합 확인만)

- [ ] **Step 1: 전체 Foundation 테스트 실행**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_schema.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_engine.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_tsr_loader.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_gold_schema.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_gold_evaluator.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_query_schema.py \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_domain_plugin.py \
  -v
```
Expected: `23 passed`

- [ ] **Step 2: 기존 테스트 회귀 없음 확인**

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/ -q \
  --ignore=/home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_check_provider_readiness_script.py \
  --ignore=/home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/test_run_workflow_experiment_script.py
```
Expected: 기존 테스트 모두 PASS, 새 테스트 23개 추가.

- [ ] **Step 3: Foundation 완료 태그**

```bash
git tag foundation-v1.0
```
