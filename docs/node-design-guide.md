# ComfyBIO Node Design Guide

이 문서는 ComfyBIO 프로젝트에서 ComfyUI 노드를 새로 작성하거나 수정할 때
반드시 따라야 하는 설계 규칙을 정의합니다. 다른 세션의 LLM 또는 개발자가
이 규칙을 읽고 일관된 노드를 작성할 수 있도록 구체적인 코드 예시를 포함합니다.

---

## 1. 디렉터리 구조 규칙

```
ComfyBIO_biopython/
  py/                          # ComfyUI 노드 파일 위치
    biopython/                 # 도메인별 하위 폴더
    transcriptomics/
    cheminformatics/           # CS3 예정
    proteomics/                # CS4 예정
    epigenomics/               # CS5 예정
  llm_interface/
    llm_core/                  # 실제 분석 로직 (노드에서 import)
      transcriptomics/         # 도메인별 로직 패키지
        de.py                  # 함수: run_deseq2()
        sc.py                  # 함수: run_sc_preprocess(), run_sc_cluster(), ...
        qc.py                  # 함수: run_fastp()
        align.py               # 함수: run_star_align(), run_kallisto_quant(), ...
```

**규칙:**
- 노드 파일(`py/도메인/*.py`)에는 ComfyUI 래퍼만 작성한다.
- 실제 분석 로직은 `llm_interface/llm_core/도메인/*.py`에 독립 함수로 작성한다.
- `py/` 파일에서 `comfy_api` 외 분석 라이브러리를 직접 import하지 않는다.
  대신 `execute()` 메서드 내부에서 `from llm_core.도메인.모듈 import 함수` 형태로 사용한다.

---

## 2. 노드 파일 구조

각 도메인의 노드 파일은 `py/도메인/` 아래에 기능 단위로 분리한다.

| 파일명 패턴 | 포함 노드 예시 |
|-----------|-------------|
| `RNASeq_QC_Objects.py` | `Fastp_trim` |
| `RNASeq_Align_Objects.py` | `STAR_align`, `Kallisto_quant`, `Salmon_quant` |
| `RNASeq_DE_Objects.py` | `DESeq2_run` |
| `SingleCell_Objects.py` | `SC_load`, `SC_preprocess`, `SC_cluster`, `SC_annotate`, `SC_markers` |

### 파일 기본 템플릿

```python
from __future__ import annotations

# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class 노드명(_Base):
    """한 줄 설명.

    더 긴 설명 (사용 방법, 필요한 사전 조건, extra_args 예시).

    Example extra_args:
        --flag1 value1 --flag2
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="노드명",              # 고유 ID, 클래스명과 동일
            display_name="표시 이름",      # ComfyUI UI에 표시되는 이름
            category="도메인/카테고리",    # 예: "Transcriptomics/QC"
            inputs=[...],
            outputs=[...],
        )

    @classmethod
    def execute(cls, ...) -> io.NodeOutput:
        from llm_core.도메인.모듈 import 함수
        ...
        return io.NodeOutput(...)
```

---

## 3. 입력 그룹 구성 규칙 (필수)

노드의 입력은 **3개 그룹**으로 구성하며, 순서를 지킨다.

```
[1] 입력 파일 그룹     — 처리할 데이터 파일 경로들
[2] 주요 파라미터 그룹  — 초보자가 기본값으로 사용할 수 있는 핵심 옵션
[3] 고급 옵션 그룹     — extra_args (CLI 플래그 또는 JSON kwargs)
```

### 코드 예시

```python
inputs=[
    # ── 입력 파일 ──────────────────────────────────────────
    io.String.Input("r1_path",
        display_name="R1 FASTQ",
        multiline=False, default="",
        tooltip="Read 1 FASTQ path (.fastq / .fastq.gz)"),
    io.String.Input("r2_path",
        display_name="R2 FASTQ (paired-end, optional)",
        multiline=False, default="",
        tooltip="Leave empty for single-end"),
    io.String.Input("output_dir",
        display_name="Output directory",
        multiline=False, default="",
        tooltip="Auto-created temp dir if empty"),
    # ── 주요 파라미터 ──────────────────────────────────────
    io.Int.Input("thread",
        display_name="Threads",
        default=4, min=1, max=32),
    io.Int.Input("quality_phred",
        display_name="Min quality (Phred)",
        default=20, min=0, max=40,
        tooltip="Minimum base quality score"),
    # ── 고급 옵션 ──────────────────────────────────────────
    io.String.Input("extra_args",
        display_name="Extra fastp arguments",
        multiline=True, default="",
        tooltip="Additional fastp flags, e.g. --cut_front --trim_poly_x"),
],
```

### 입력 타입 선택 기준

| 상황 | 사용 타입 | 예시 |
|------|---------|-----|
| 파일/디렉터리 경로 | `io.String.Input(multiline=False)` | `r1_path`, `genome_dir` |
| 정수 파라미터 | `io.Int.Input(min=..., max=...)` | `threads`, `min_genes` |
| 실수 파라미터 | `io.Float.Input(min=...)` | `resolution`, `alpha` |
| 선택지 (고정 목록) | `io.Combo.Input(options=[...])` | `algorithm`, `lib_type` |
| 참/거짓 플래그 | `io.Boolean.Input` | `compute_umap`, `gc_bias` |
| 여러 줄 텍스트 | `io.String.Input(multiline=True)` | `extra_args`, JSON 입력 |

---

## 4. extra_args 처리 규칙

노드 종류에 따라 두 가지 방식으로 처리한다.

### 4-1. CLI 도구 (fastp, STAR, kallisto 등)

`shlex.split()`으로 파싱 후 커맨드 리스트에 append한다.

```python
import shlex

if extra_args.strip():
    cmd += shlex.split(extra_args)
```

**사용자 입력 예시:**
```
--cut_front --cut_tail --cut_window_size 4
```

### 4-2. Python 라이브러리 (pydeseq2, scanpy 등)

JSON 형식으로 입력받아 `**kwargs`로 전달한다.

```python
import json

try:
    extra_kwargs = json.loads(extra_args) if extra_args.strip() else {}
except json.JSONDecodeError as e:
    return io.NodeOutput(..., f"ERROR: extra_args not valid JSON — {e}")

# 함수 호출 시 병합
result = some_function(param1=val1, **extra_kwargs)
```

**사용자 입력 예시:**
```json
{"alpha": 0.01, "cooks_filter": false}
```

---

## 5. 출력 구성 규칙 (필수)

모든 노드는 다음 출력 원칙을 따른다.

### 기본 출력 패턴

```python
outputs=[
    io.String.Output("output_path"),       # 결과 파일/디렉터리 경로 (항상 포함)
    io.Int.Output("n_significant"),        # 핵심 수치 (도구에 따라)
    io.String.Output("summary_text"),      # 사람이 읽을 수 있는 요약 (항상 포함)
],
```

**규칙:**
- `summary_text`는 **항상** 마지막 출력으로 포함한다.
- 오류 발생 시 `summary_text`에 `"ERROR: 메시지"` 형식으로 반환한다. 예외를 raise하지 않는다.
- 출력 경로가 없어도 `summary_text`는 반환한다.

### 오류 처리 패턴

```python
@classmethod
def execute(cls, ...) -> io.NodeOutput:
    try:
        # 분석 실행
        ...
        return io.NodeOutput(output_path, n_result, summary)
    except Exception as e:
        return io.NodeOutput("", 0, f"ERROR: {e}")
```

### summary_text 작성 규칙

```python
def _fastp_summary(stats: dict, paired: bool) -> str:
    lines = [
        "=== fastp QC Summary ===",          # 항상 "=== 도구명 설명 ===" 헤더
        f"Mode  : {'Paired-end' if paired else 'Single-end'}",
        f"Input : {total_in:,} reads",
        f"Output: {total_out:,} reads ({pass_rate:.1f}% pass)",
    ]
    return "\n".join(lines)
```

---

## 6. Paired-end 자동 감지 패턴

r2_path 입력 여부로 single-end / paired-end를 자동 구분한다.

```python
paired = bool(r2_path and r2_path.strip())

if not paired:
    # single-end 처리
    cmd += ["--single", "--fragment-length", str(fragment_length)]
else:
    # paired-end 처리
    cmd += ["--in2", r2_path, "--out2", r2_out]
```

---

## 7. Output 경로 기본값 처리

output_path/output_dir이 비어있으면 tempfile로 자동 생성한다.

```python
import tempfile
from pathlib import Path

out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
out_dir.mkdir(parents=True, exist_ok=True)
```

---

## 8. ComfyUI 카테고리 명명 규칙

```
도메인/기능그룹

예:
  Transcriptomics/QC
  Transcriptomics/Alignment
  Transcriptomics/DifferentialExpression
  Transcriptomics/SingleCell
  Biopython/SeqIO
  Biopython/Alignment
  Cheminformatics/Docking        (CS3 예정)
  Proteomics/DatabaseSearch      (CS4 예정)
  Epigenomics/PeakCalling        (CS5 예정)
```

---

## 9. 로직 함수 설계 규칙 (llm_core/도메인/*.py)

노드에서 호출하는 로직 함수는 다음 규칙을 따른다.

```python
# llm_interface/llm_core/transcriptomics/de.py

def run_deseq2(
    counts_path: str,
    metadata_path: str,
    condition_col: str = "condition",
    reference_level: str = "control",
    alpha: float = 0.05,
    output_path: str | None = None,     # None이면 tempfile 자동 생성
) -> tuple[str, int]:                  # (결과 경로, 유의 유전자 수) 등 반환
    """한 줄 설명.

    Returns:
        results_path: TSV 결과 파일 경로
        n_significant: 유의한 유전자 수
    """
    ...
```

**규칙:**
- `output_path=None`이면 내부에서 `tempfile.mkdtemp()`로 처리한다.
- `comfy_api`를 import하지 않는다 — 이 함수는 ComfyUI 없이도 실행 가능해야 한다.
- 반환 타입을 tuple로 명시한다.

---

## 10. 새 도메인 추가 체크리스트

새 도메인(예: CS3 Cheminformatics)을 추가할 때 확인할 항목:

- [ ] `py/cheminformatics/` 폴더 생성
- [ ] `llm_interface/llm_core/cheminformatics/` 폴더 + `__init__.py` 생성
- [ ] 로직 함수를 `llm_core/cheminformatics/*.py`에 작성
- [ ] 노드 파일을 `py/cheminformatics/*.py`에 작성 (이 가이드 규칙 준수)
- [ ] `llm_interface/llm_core/tsr/domains/cheminformatics.yaml` 작성
- [ ] `llm_interface/llm_core/benchmark/cs3_cheminformatics_plugin.py` 작성
- [ ] `llm_interface/llm_core/gold/domains/cheminformatics/*.yaml` 작성
- [ ] `__init__.py`의 `rglob("*.py")`가 자동으로 새 노드를 탐색함 (별도 등록 불필요)

---

## 11. 금지 사항

- `py/` 파일 내에서 `import pandas`, `import scanpy` 등 분석 라이브러리를 모듈 수준에서 import하지 않는다.
  → ComfyUI 로딩 시 불필요한 import 오류를 방지하기 위해 `execute()` 내부에서 지연 import한다.
- `llm_core/` 파일 내에서 `from comfy_api.latest import io`를 import하지 않는다.
- `execute()` 메서드에서 예외를 raise하지 않는다. 모든 오류는 `summary_text`에 담아 반환한다.
- `output_path`가 비어 있을 때 빈 문자열을 그대로 파일 경로로 사용하지 않는다. 반드시 tempfile을 생성한다.
