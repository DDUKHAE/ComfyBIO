# ComfyBIO — Agent Orientation Guide

## Project Goal

ComfyUI를 **자연어 기반 생명정보학 워크플로우 생성 플랫폼**으로 활용하는 연구 프로젝트.
LLM이 사용자의 자연어 쿼리를 받아 올바른 분석 도구를 선택하고 ComfyUI 노드 워크플로우를 생성하는 능력을 6개 생물정보학 도메인에서 벤치마크한다.

---

## Domain Structure (CS1–CS6)

| ID  | Domain            | Key Tools                              | Status |
|-----|-------------------|----------------------------------------|--------|
| CS1 | Biopython         | BioPython 전체 라이브러리               | ✅ 완료 |
| CS2 | Transcriptomics   | fastp, STAR, kallisto, DESeq2, scanpy  | ✅ 완료 |
| CS3 | Variant Analysis  | BWA-MEM2, GATK, bcftools, PLINK        | ✅ 완료 |
| CS4 | Epigenomics       | Bowtie2, MACS3, Bismark, deeptools     | ✅ 완료 |
| CS5 | Metagenomics      | Kraken2, MetaPhlAn4, HUMAnN3, MEGAHIT | ✅ 완료 |
| CS6 | Genome Assembly   | SPAdes, Flye, QUAST, Prokka            | ✅ 완료 |

각 도메인은 12개 워크플로우 패밀리 × 도메인당 쿼리셋으로 구성된다.

---

## Directory Layout

```
ComfyBIO_biopython/
├── py/{domain}/               # ComfyUI 노드 (사용자가 드래그하는 박스)
├── llm_interface/llm_core/
│   ├── harness/               # 평가 하네스 핵심 (아래 참고)
│   ├── benchmark/             # DomainPlugin ABC + CS2-CS6 플러그인
│   ├── tsr/domains/{domain}.yaml  # Tool Selection Registry (도구 선택 규칙)
│   ├── gold/                  # Gold criteria (정답 기준)
│   ├── llm_adapters/          # claude_cli, codex_cli, gemini_cli
│   └── {domain}/              # 도메인별 Python 실행 라이브러리
└── docs/node-design-guide.md  # 노드 설계 규칙 (LLM이 새 노드 만들 때 참고)
```

---

## Evaluation Harness Flow

```
HeldOutQuery (자연어 쿼리 + 컨텍스트)
  ↓ prompt_builder.build_tool_selection_prompt(tsr, query)
  ↓ LLM adapter (claude / codex / gemini)
  ↓ response_parser.parse_tool_response(raw) → list[str]
  ↓ GoldEvaluator.evaluate(tools, output)   → Verdict
  ↓ EvalResult → BenchmarkReport
  ↓ reporter.print_report() / export_jsonl()
```

**Verdict 종류:** `CORRECT_CANONICAL` / `CORRECT_ALTERNATIVE` / `INCORRECT` / `CRITICAL_ERROR`

---

## Key Concepts

**TSR (Tool Selection Registry)** — `tsr/domains/{domain}.yaml`
각 분석 스텝별로 canonical / alternative_valid / invalid 도구를 데이터 컨텍스트 조건과 함께 등록. AST-safe 조건 평가로 재현성 보장.

**Multi-path Gold Criteria** — `gold/domains/{domain}/{query_id}.yaml`
- Tier 1 (canonical): 정확히 이 도구여야 함
- Tier 2 (alternative): 기능적으로 동등한 대안
- Tier 3 (invalid): 사용 시 즉시 CRITICAL_ERROR

**DomainPlugin** — `benchmark/cs{N}_{domain}_plugin.py`
`get_tsr()` / `list_families()` / `load_gold()` 구현. `HarnessMixin` 상속으로 `run_workflow()` 자동 연결.

**ComfyUI 노드 규칙** — `docs/node-design-guide.md` 필독
- Basic 노드: ≤6 입력, 핵심 파라미터만
- Advanced 노드: 전체 파라미터 + `extra_args` (JSON/CLI 문자열)
- `summary_text` 출력은 항상 마지막

---

## How to Add a New Domain

1. `py/{domain}/` — ComfyUI 노드 파일 작성 (`docs/node-design-guide.md` 준수)
2. `llm_interface/llm_core/{domain}/` — 실행 라이브러리 작성
3. `llm_interface/llm_core/tsr/domains/{domain}.yaml` — 12개 step_id TSR 작성
4. `llm_interface/llm_core/benchmark/cs{N}_{domain}_plugin.py` — DomainPlugin + HarnessMixin 상속
5. `benchmark/__init__.py`의 `_REGISTRY`에 등록

---

## Running the Harness

```python
import asyncio
from llm_core.benchmark import get_plugin
from llm_core.harness import run_domain, print_report

plugin = get_plugin("transcriptomics")  # or any domain_id
# queries: list[HeldOutQuery] — loaded from gold YAML or fixture
report = asyncio.run(run_domain(plugin, queries, provider="claude"))
print_report(report)
```
