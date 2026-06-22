# ComfyBIO Node Design Guide

> **대상**: 새 노드를 작성하는 LLM 또는 개발자.
> 이 문서를 읽으면 개별 노드 설계 규칙과 **캔버스에서 읽히는 워크플로우** 설계 규칙을 모두 파악할 수 있다.
> 참조 구현: `py/transcriptomics/` 아래 노드들.

---

## 1. 워크플로우 시각 문법 (캔버스 레벨)

노드 하나보다 **연결된 흐름**이 먼저다. 노드를 추가하기 전에 워크플로우 레이아웃을 결정한다.

### 1-1. 좌→우 단계 배치 (필수)

```
[입력/로드] ──► [QC/전처리] ──► [정렬/정량] ──► [분석] ──► [출력/시각화]
```

- 데이터 흐름 방향은 항상 **왼쪽→오른쪽**.
- 같은 단계 노드는 **수직 정렬**. 단계 간 간격은 최소 120px.
- 역방향(오른→왼) 연결은 금지. 루프가 필요하면 설계를 재검토한다.

### 1-2. 단계별 Group Box (필수)

각 분석 단계를 Group Box로 묶는다. 레이블은 단계 이름.

```
┌─── QC ────────┐   ┌─── Alignment ─────┐   ┌─── DE Analysis ──┐
│  Fastp_trim   │──►│  STAR_align       │──►│  DESeq2_run      │
└───────────────┘   └───────────────────┘   └──────────────────┘
```

Group Box 색상 규칙:

| 단계 | 색상 |
|------|------|
| 입력/로드 | 회색 (`#555`) |
| QC/전처리 | 녹색 (`#2a5`) |
| 정렬/정량 | 파란색 (`#25a`) |
| 분석 (DE, clustering) | 보라 (`#62a`) |
| 출력/시각화 | 주황 (`#a62`) |

추가 가독성 규칙:
- 같은 단계는 항상 같은 Group Box 색을 사용한다.
- Group Box 제목 텍스트는 배경과 충분한 대비가 나도록 밝은 색으로 유지한다.
- 장식용 색 추가를 금지하고 단계 의미 전달에만 색을 사용한다.

### 1-3. Branch 최소화

- 한 노드에서 나가는 연결 수: **최대 3개**.
- 같은 노드 출력을 4개 이상의 하류 노드가 받아야 한다면 **Reroute 노드** 하나를 경유점으로 사용.
- 평행 branch(예: 두 개의 aligner 비교)는 같은 수직 위치에 배치하고, 공통 입력 노드에서 분기한다.

### 1-4. Reroute 사용 기준

- 케이블 길이가 노드 3개 폭(약 360px)을 초과할 때 Reroute를 중간에 배치한다.
- Reroute는 직각 꺾임점에 놓는다(대각선 케이블 방지).
- 교차(crossing) 케이블이 생기면 Reroute로 해소한다.

### 1-5. 시작/종료 노드 형태

- **시작 노드**: 연결 입력 소켓은 없고, 파일/메타데이터 위젯만 있는 source node. 캔버스 가장 왼쪽.
- **종료 노드**: 최종 결과 파일 또는 시각화 아티팩트를 생성하는 노드. 캔버스 가장 오른쪽.
- **실행 가능성 규칙**: 모든 노드는 `OUTPUT_NODE = True`를 가진다. 이는 단독 실행을 위한 엔진 설정이며, 시각적 종료 노드 여부와는 별개다.
- 워크플로우 하나에 시작 노드는 1~2개, 종료 노드는 1개를 권장.

---

## 2. 의미적 소켓 타입 (포트 시각화)

**모든 포트가 STRING이면 GUI에서 어떤 연결도 막지 못한다.**
도메인 객체 또는 pipeline 파일을 전달하는 포트는 의미적 타입을 사용한다.

### 2-1. 타입 분류 원칙

| 포트 종류 | 타입 | 이유 |
|---------|------|------|
| 사용자가 직접 입력하는 경로/옵션 | `STRING` (유지) | 위젯으로 입력 |
| **노드 사이를 흐르는 파일/객체** | 의미적 타입 | GUI 연결 제어 |

**판별 질문**: "이 포트의 값을 사용자가 직접 타이핑하나, 아니면 다른 노드 출력에서 받나?"
- 직접 타이핑 → `STRING`/`INT`/`FLOAT`/`COMBO` 유지
- 노드 출력에서 받음 → 의미적 타입 사용

### 2-2. 타입 정의표

**Biopython (CS1)**

| 타입 | 의미 | 예시 포트명 |
|------|------|-----------|
| `BIO_SEQRECORD_LIST` | SeqRecord 목록 | `records` |
| `BIO_SEQRECORD` | 단일 SeqRecord | `record` |
| `BIO_ALIGNMENT` | 다중 정렬 | `alignment` |
| `BIO_TREE` | 계통수 | `tree` |
| `BIO_BLAST_RESULT` | BLAST 결과 | `blast_result` |
| `BIO_STRUCTURE` | PDB 구조 | `structure` |
| `BIO_MOTIF` | 서열 모티프 | `motif` |

**Transcriptomics (CS2)**

| 타입 | 의미 | 예시 포트명 |
|------|------|-----------|
| `RNASEQ_FASTQ` | FASTQ 파일 경로(trimming 결과) | `r1_trimmed`, `r2_trimmed` |
| `RNASEQ_BAM` | BAM 파일 경로 | `bam_path` |
| `RNASEQ_QUANT_DIR` | kallisto/salmon 출력 디렉터리 | `quant_dir` |
| `RNASEQ_COUNTS` | 유전자 카운트 매트릭스 TSV | `counts_path` |
| `RNASEQ_DE_RESULT` | DESeq2/edgeR 결과 TSV | `results_path`, `significant_path` |
| `SC_H5AD` | AnnData .h5ad 파일 | `output_path` (SC_* 노드 간) |

**도메인 추가 시**: `도메인약어_객체명` 패턴으로 정의. 예: `CHEM_MOL` (CS3), `PROT_SPECTRUM` (CS4).

### 2-3. 코드 적용 방법

```python
# ✅ 노드 사이를 흐르는 파일/객체 → 의미적 타입
outputs=[
    io.Custom("RNASEQ_FASTQ").Output("r1_trimmed",
        tooltip="Trimmed R1 FASTQ path"),
    io.Custom("RNASEQ_FASTQ").Output("r2_trimmed",
        tooltip="Trimmed R2 FASTQ path (empty for single-end)"),
    io.String.Output("stats_json"),
],

# ✅ 사용자가 직접 입력하는 값 → STRING/COMBO 유지
inputs=[
    io.String.Input("genome_dir", ...),
    io.Combo.Input("out_sam_type", ...),
    io.Int.Input("threads", ...),
],

# ✅ 다른 노드 출력을 받는 포트 → 의미적 타입
inputs=[
    io.Custom("RNASEQ_FASTQ").Input("r1_path",
        tooltip="Connect from Fastp_trim r1_trimmed"),
],
```

> **AST 파서 주의**: `io.Custom("타입명")` 형태로만 쓴다.
> `MY_TYPE = io.Custom("RNASEQ_FASTQ")` 별칭을 만들어 사용하면 `build_registry.py`가 타입을 인식하지 못한다.

### 2-4. STRING 포트 제한 규칙

출력 포트에서 `io.String.Output`을 사용할 수 있는 경우:
- `stats_json` — 통계 JSON 문자열
- `annotation_json` — 클러스터 주석 JSON
- `report_md` — 사람이 읽는 마크다운 리포트
- `log_final_path` — 실행 로그 파일 경로를 보조 정보로 노출할 때

그 외 **파일 경로나 객체를 전달하는 출력에는 반드시 의미적 타입을 사용**한다.

---

## 3. display_name 명명 규칙

캔버스에서 노드 제목만 보고 역할을 즉시 파악할 수 있어야 한다.

### 3-1. 길이 규칙

- **최대 20자** (영문 기준). 20자 초과 시 약어 사용.
- 공백 포함 측정. 예: `"SC preprocess"` = 13자 ✅, `"Single cell preprocessing QC"` = 29자 ❌

### 3-2. 패턴: `동사+명사` 또는 `도구명 동작`

```
✅ 좋은 예              ❌ 나쁜 예
fastp trim              Adapter Trimming and Quality Control Node
STAR align              Spliced Transcripts Alignment to a Reference
DESeq2 run              Differential Gene Expression Analysis
SC preprocess           Single-Cell RNA-seq Quality Control Preprocessing
SC cluster              Cell Clustering with Leiden Algorithm
SC find markers         Find Marker Genes for Each Cluster
```

### 3-3. 도메인 접두어 규칙

같은 도메인의 노드는 접두어를 통일해서 ComfyUI 메뉴에서 그룹이 보이도록 한다.

| 도메인 | 접두어 패턴 | 예시 |
|--------|-----------|------|
| 시퀀스 (CS1) | 도구명 | `SeqIO parse`, `BLAST search` |
| 전사체 QC | `fastp`, `FastQC` 등 도구명 | `fastp trim` |
| 정렬 | `STAR`, `kallisto`, `salmon` | `STAR align`, `kallisto quant` |
| DE 분석 | 도구명 | `DESeq2 run` |
| 단일세포 | `SC` 접두어 | `SC load`, `SC preprocess`, `SC cluster` |
| 화학정보 (CS3) | `Mol` 접두어 | `Mol parse`, `Mol dock` |

### 3-4. 유사 노드 접미어 정렬

같은 작업의 기본/고급 변형:

```python
node_id="Fastp_trim"            display_name="fastp trim"
node_id="Fastp_trim_Advanced"   display_name="fastp trim +"
```

입력/출력이 다른 변형:

```python
node_id="DESeq2_run"            display_name="DESeq2 run"
node_id="DESeq2_run_paired"     display_name="DESeq2 run (paired)"
```

---

## 4. 기본 노드 / 고급 노드 분리 규칙

**모든 파라미터를 한 노드에 넣으면 노드가 길어져 워크플로우 흐름이 묻힌다.**

### 4-1. 분리 기준

| 포함 대상 | 노드 유형 |
|---------|---------|
| 파일 입력 + 가장 중요한 파라미터 2~3개 | 기본 노드 (`Node_name`) |
| 기본 파라미터 전부 + `extra_args` | 고급 노드 (`Node_name_Advanced`) |

입력 포트 수 가이드:
- 기본 노드: **최대 6개** (파일 2~3 + 파라미터 2~3)
- 고급 노드: 제한 없음 (단, 논리적 그룹화 유지)

### 4-2. 기본 노드 예시

```python
class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Fastp_trim(_Base):
    """기본 어댑터 트리밍. 고급 옵션은 Fastp_trim_Advanced 사용."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Fastp_trim",
            display_name="fastp trim",
            category="Transcriptomics/QC",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ", multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (optional)", multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output dir", multiline=False, default=""),
                io.Int.Input("thread",
                    display_name="Threads", default=4, min=1, max=32),
                io.Int.Input("quality_phred",
                    display_name="Min quality (Phred)", default=20, min=0, max=40),
            ],
            outputs=[
                io.Custom("RNASEQ_FASTQ").Output("r1_trimmed"),
                io.Custom("RNASEQ_FASTQ").Output("r2_trimmed"),
            ],
        )
```

### 4-3. 고급 노드 예시

```python
class Fastp_trim_Advanced(_Base):
    """어댑터 트리밍 — 전체 옵션 및 extra_args 포함."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Fastp_trim_Advanced",
            display_name="fastp trim +",
            category="Transcriptomics/QC",
            inputs=[
                io.String.Input("r1_path", display_name="R1 FASTQ",
                    multiline=False, default=""),
                io.String.Input("r2_path", display_name="R2 FASTQ (optional)",
                    multiline=False, default=""),
                io.String.Input("output_dir", display_name="Output dir",
                    multiline=False, default=""),
                io.Int.Input("thread", display_name="Threads",
                    default=4, min=1, max=32),
                io.Int.Input("quality_phred", display_name="Min quality (Phred)",
                    default=20, min=0, max=40),
                io.Int.Input("length_required", display_name="Min read length",
                    default=50, min=0, max=1000),
                io.Boolean.Input("detect_adapter_for_pe",
                    display_name="Auto-detect adapter (PE)", default=True),
                io.String.Input("adapter_sequence", display_name="Adapter R1",
                    multiline=False, default=""),
                io.String.Input("adapter_sequence_r2", display_name="Adapter R2",
                    multiline=False, default=""),
                io.String.Input("extra_args", display_name="Extra fastp args",
                    multiline=True, default="",
                    tooltip="e.g. --cut_front --trim_poly_x"),
            ],
            outputs=[
                io.Custom("RNASEQ_FASTQ").Output("r1_trimmed"),
                io.Custom("RNASEQ_FASTQ").Output("r2_trimmed"),
                io.String.Output("stats_json"),
            ],
        )
```

> **같은 파일에 함께 정의**: `RNASeq_QC_Objects.py`에 `Fastp_trim`과 `Fastp_trim_Advanced`를 모두 넣는다.
> `__init__.py`의 `rglob`이 자동으로 두 클래스를 모두 등록한다.

---

## 5. 출력 우선순위 규칙

### 5-1. 출력 순서

```
1. 주 결과 (다음 노드 입력으로 연결되는 것)  ← 최상단, 의미적 타입
2. 보조 결과 (실험적으로 중요한 것)        ← 0~1개 권장
3. 구조화된 보조 텍스트/JSON              ← 필요 시만 추가
```

기본 노드는 **주 결과 1~2개**, 정말 필요한 경우에만 보조 결과 1개를 추가한다.
기본 노드 출력은 **최대 3개**를 넘기지 않는다.

```python
# 기본 노드 출력 (권장: 2개)
outputs=[
    io.Custom("RNASEQ_BAM").Output("bam_path"),
    io.Float.Output("mapping_rate"),
]

# 고급 노드 출력 (4개 이하 권장)
outputs=[
    io.Custom("RNASEQ_BAM").Output("bam_path"),
    io.String.Output("log_final_path"),
    io.Float.Output("mapping_rate"),
    io.String.Output("stats_json"),
]
```

### 5-2. 출력 선택 기준

```python
outputs=[
    io.Custom("RNASEQ_COUNTS").Output("counts_path"),
    io.Int.Output("n_genes_detected"),
    io.String.Output("stats_json"),
]
```

- 다음 분석 단계에서 직접 소비하는 결과를 우선 출력한다.
- 사람이 빠르게 확인해야 하는 핵심 수치만 보조 출력으로 둔다.
- 긴 설명문 대신 구조화된 파일/수치/JSON을 우선한다.

### 5-3. 오류 처리 — 예외를 즉시 raise한다

```python
@classmethod
def execute(cls, ...) -> io.NodeOutput:
    from llm_core.domain.module import run_tool

    result_path, mapping_rate = run_tool(...)
    if not result_path:
        raise RuntimeError("STAR_align produced no BAM output")
    return io.NodeOutput(result_path, mapping_rate)
```

---

## 6. extra_args 처리 규칙

### 6-1. CLI 도구 → shlex.split()

```python
import shlex

cmd = ["fastp", "--in1", r1_path, ...]
if extra_args.strip():
    cmd += shlex.split(extra_args)
```

사용자 입력 예:
```
--cut_front --cut_tail --cut_window_size 4 --cut_mean_quality 20
```

### 6-2. Python 라이브러리 → JSON kwargs

```python
import json

try:
    extra_kwargs = json.loads(extra_args) if extra_args.strip() else {}
except json.JSONDecodeError as e:
    raise ValueError(f"extra_args는 JSON 형식이어야 합니다: {e}")

result = some_python_function(param1=val1, **extra_kwargs)
```

사용자 입력 예:
```json
{"alpha": 0.01, "cooks_filter": false, "independent_filter": true}
```

---

## 7. 입력 설계 세부 규칙

### 7-1. 입력 타입별 선택 기준

| 상황 | 타입 | 예 |
|------|------|----|
| 사용자 타이핑 경로 | `io.String.Input(multiline=False)` | `genome_dir`, `output_dir` |
| 파이프라인 연결 경로 | `io.Custom("TYPE").Input(...)` | `r1_trimmed` |
| 정수 | `io.Int.Input(min=, max=)` | `threads`, `min_genes` |
| 실수 | `io.Float.Input(min=)` | `resolution`, `alpha` |
| 고정 선택지 | `io.Combo.Input(options=[...])` | `algorithm`, `lib_type` |
| 참/거짓 | `io.Boolean.Input` | `compute_umap`, `gc_bias` |
| CLI 추가 옵션 | `io.String.Input(multiline=True)` | `extra_args` |
| Python 추가 kwargs | `io.String.Input(multiline=True)` | `extra_args` (JSON 형식) |

### 7-2. tooltip 필수 항목

다음 항목에는 반드시 `tooltip` 매개변수를 추가한다:
- 파일 형식 설명이 필요한 경로 입력
- 기본값이 직관적이지 않은 파라미터 (예: `quality_phred=20`)
- `extra_args` — 예시 포함

```python
io.Int.Input("quality_phred",
    display_name="Min quality (Phred)",
    default=20, min=0, max=40,
    tooltip="기본값 20 = Phred Q20 (오류율 1%). RNA-seq 표준은 20~30."),
```

### 7-3. Paired-end 자동 감지

`r2_path`를 별도로 단독 입력받아, 비어있으면 single-end로 처리한다.

```python
paired = bool(r2_path and r2_path.strip())
```

`single_end: bool` 별도 입력을 추가하지 않는다. `r2_path` 유무로 판단한다.

### 7-4. output_dir 기본값

```python
from pathlib import Path
import tempfile

out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
out_dir.mkdir(parents=True, exist_ok=True)
```

---

## 8. 카테고리 명명 규칙

```
도메인/기능그룹
```

| 도메인 | 카테고리 예시 |
|--------|------------|
| Biopython | `Biopython/SeqIO`, `Biopython/Alignment`, `Biopython/BLAST` |
| 전사체 (CS2) | `Transcriptomics/QC`, `Transcriptomics/Alignment`, `Transcriptomics/DifferentialExpression`, `Transcriptomics/SingleCell` |
| 화학정보 (CS3) | `Cheminformatics/Molecule`, `Cheminformatics/Docking`, `Cheminformatics/ADMET` |
| 단백체 (CS4) | `Proteomics/DatabaseSearch`, `Proteomics/Quantification`, `Proteomics/Statistics` |
| 후성유전 (CS5) | `Epigenomics/PeakCalling`, `Epigenomics/Motif`, `Epigenomics/Methylation` |

---

## 9. 디렉터리 및 파일 구조

```
py/
  도메인/                   # ComfyUI 노드 파일
    RNASeq_QC_Objects.py   # Fastp_trim, Fastp_trim_Advanced
    RNASeq_Align_Objects.py
    RNASeq_DE_Objects.py
    SingleCell_Objects.py
llm_interface/llm_core/
  도메인/                   # 실제 분석 로직 (노드에서 import)
    de.py                  # run_deseq2(), ...
    sc.py                  # run_sc_preprocess(), ...
    qc.py                  # run_fastp(), ...
    align.py               # run_star_align(), ...
```

**py/ 파일 규칙:**
- `comfy_api` 이외 라이브러리는 모듈 레벨이 아닌 `execute()` 내부에서 지연 import한다.
- 분석 로직은 `llm_core/도메인/*.py`의 독립 함수로 분리한다.
- 모든 노드의 공통 base class는 `OUTPUT_NODE = True`를 포함해야 한다.

**llm_core/ 함수 규칙:**
- `from comfy_api.latest import io` 금지 — ComfyUI 없이 단독 실행 가능해야 한다.
- 반환 타입을 명시한다 (예: `-> tuple[str, int]`).
- `output_path=None`이면 내부에서 tempfile을 생성한다.

---

## 10. 금지 사항 (체크리스트)

- [ ] `py/` 파일에서 모듈 레벨 `import pandas`, `import scanpy` — **금지** (지연 import로)
- [ ] `llm_core/` 파일에서 `from comfy_api.latest import io` — **금지**
- [ ] `execute()`에서 오류를 숨기고 빈 결과를 반환 — **금지** (즉시 raise)
- [ ] output_path 빈 문자열을 경로로 사용 — **금지** (tempfile 생성)
- [ ] 노드 사이를 흐르는 파일/객체에 `io.String.Output` 사용 — **금지** (의미적 타입 사용)
- [ ] 기본 노드 입력 포트 7개 초과 — **금지** (고급 노드로 분리)
- [ ] 기본 노드 출력 포트 4개 이상 — **금지** (최대 3개)
- [ ] display_name 21자 초과 — **금지** (약어 사용)
- [ ] `io.Custom("타입명")` 별칭 변수 사용 — **금지** (build_registry AST 파서가 인식 못함)
- [ ] 출력 포트 5개 초과 — **권장 안 함** (보조 출력 최소화)

---

## 11. 새 도메인 추가 체크리스트

CS3 (Cheminformatics) 예시:

- [ ] `py/cheminformatics/` 폴더 생성
- [ ] `llm_interface/llm_core/cheminformatics/__init__.py` 생성
- [ ] 로직 함수 `llm_core/cheminformatics/*.py` 작성
- [ ] **의미적 소켓 타입 결정** (`CHEM_MOL`, `CHEM_FINGERPRINT`, `CHEM_DOCKING_RESULT` 등)
- [ ] 노드 파일 `py/cheminformatics/*.py` 작성 (이 가이드 규칙 준수)
  - 기본 노드 + Advanced 노드 쌍으로 작성
  - 의미적 타입 포트 적용
  - display_name 20자 이내
- [ ] `llm_interface/llm_core/tsr/domains/cheminformatics.yaml` 작성
- [ ] `llm_interface/llm_core/benchmark/cs3_cheminformatics_plugin.py` 작성
- [ ] `llm_interface/llm_core/gold/domains/cheminformatics/*.yaml` 작성
- [ ] `__init__.py`의 `rglob("*.py")`가 자동으로 새 노드를 탐색함 (별도 등록 불필요)
