# 즉시 착수 개선 계획서

**작성일:** 2026-06-24  
**참조:** `docs/github_benchmark_research_2026-06-24.md`  
**범위:** 즉시 착수 가능한 2가지 개선 항목 상세 구현 계획

---

## 개요

조사 결과 도출된 즉시 착수 항목 2개:

| # | 항목 | 예상 공수 | 효과 |
|---|------|-----------|------|
| ① | 쿼리 다양성 확대 | 2~3일 | 통계적 유의성 확보, 취약점 탐지 |
| ② | 추론 trace 캡처 | 반나절 | 오답 분석 가능, 프롬프트 개선 기반 |

항목 ②가 코드 변경량이 작고 이후 ①의 데이터 수집에도 필요하므로 **② → ① 순서로 진행**한다.

---

## 항목 ② — 추론 Trace 캡처

### 목표
LLM이 도구를 선택하는 과정(이유, 확신도, 각 도구에 대한 근거)을 `EvalResult`에 저장한다.
현재는 `generated_tools: [STAR]`만 남아 오답 분석이 불가능하다.

### 현재 코드 흐름

```
runner.py
  raw_response = await adapter.generate(prompt)   ← LLM 원문 응답
  generated_tools = parse_tool_response(raw_response)  ← 도구 목록만 추출
  verdict = evaluator.evaluate(generated_tools, output)
  → EvalResult(generated_tools=..., raw_response=raw_response, ...)
                                         ↑ raw_response는 이미 저장됨
```

`raw_response`는 이미 저장되지만 구조화된 형태로 파싱되지 않는다.

### 변경할 파일

```
llm_interface/llm_core/
├── harness/
│   ├── result_schema.py     ← EvalResult에 필드 3개 추가
│   ├── response_parser.py   ← parse_tool_response 반환값 확장
│   └── runner.py            ← 확장된 반환값을 EvalResult에 연결
```

---

### Step ②-1: `result_schema.py` — EvalResult 필드 확장

**추가할 필드:**

```python
@dataclass
class EvalResult:
    # ... 기존 필드 유지 ...
    
    # 추론 trace (신규)
    reasoning_trace: str = ""
    # LLM 응답에서 추출한 자유형 추론 텍스트
    # 예: "FastQC is the standard tool for initial quality assessment..."

    tool_rationale: dict[str, str] = field(default_factory=dict)
    # 도구별 선택 근거
    # 예: {"STAR": "splice-aware aligner required for RNA-seq", "fastp": "..."}

    confidence_score: float | None = None
    # LLM 자가 보고 확신도 (0.0~1.0), 응답에 포함된 경우만 파싱
```

`to_dict()`에도 3개 필드 추가:
```python
"reasoning_trace": self.reasoning_trace,
"tool_rationale": self.tool_rationale,
"confidence_score": self.confidence_score,
```

---

### Step ②-2: `response_parser.py` — 파싱 반환값 확장

**현재:**
```python
def parse_tool_response(raw: str) -> list[str]:
    ...
    return tools
```

**변경 후:**
```python
@dataclass
class ParsedResponse:
    tools: list[str]
    reasoning_trace: str = ""
    tool_rationale: dict[str, str] = field(default_factory=dict)
    confidence_score: float | None = None

def parse_tool_response(raw: str) -> ParsedResponse:
    ...
```

**파싱 전략:**

LLM 응답이 JSON 블록을 포함하는 경우 (구조화 응답):
```json
{
  "tools": ["STAR", "featureCounts"],
  "reasoning": "STAR is splice-aware...",
  "rationale": {"STAR": "splice-aware aligner", "featureCounts": "counts reads per gene"},
  "confidence": 0.92
}
```

자유 텍스트인 경우 (현재 방식):
- `reasoning_trace`: 전체 raw_response를 그대로 저장 (최대 2000자 트리밍)
- `tool_rationale`: 정규식으로 `"TOOLNAME: reason"` 또는 `"- TOOLNAME — reason"` 패턴 탐지
- `confidence_score`: `"confidence: 0.9"` 또는 `"I am 90% confident"` 패턴 탐지

---

### Step ②-3: `runner.py` — 연결

**현재:**
```python
generated_tools = parse_tool_response(raw_response)
```

**변경 후:**
```python
parsed = parse_tool_response(raw_response)
generated_tools = parsed.tools

# EvalResult 생성 시:
return EvalResult(
    ...
    generated_tools=generated_tools,
    reasoning_trace=parsed.reasoning_trace,
    tool_rationale=parsed.tool_rationale,
    confidence_score=parsed.confidence_score,
)
```

---

### Step ②-4: 프롬프트 보강 (선택적 — 즉시 효과 큼)

`harness/prompt_builder.py`의 프롬프트 끝에 구조화 응답 요청 추가:

```
...existing prompt...

Respond in the following JSON format:
{
  "tools": ["tool1", "tool2"],
  "reasoning": "brief explanation of the overall approach",
  "rationale": {
    "tool1": "why this tool was chosen",
    "tool2": "why this tool was chosen"
  },
  "confidence": 0.0-1.0
}
```

이 변경으로 `parse_tool_response`의 JSON 브랜치가 항상 활성화된다.

---

### ② 검증 기준

```python
# 기존 테스트가 깨지지 않아야 함
result.generated_tools  # 기존처럼 list[str] 동작

# 신규 필드가 채워져야 함
assert result.reasoning_trace != ""   # 빈 문자열 아님
assert isinstance(result.tool_rationale, dict)
# confidence_score는 None이어도 OK (LLM이 언급 안 할 수 있음)
```

---

## 항목 ① — 쿼리 다양성 확대

### 목표
각 도메인 × 패밀리에 현재 `_001` 1개뿐인 gold 파일을 **4개 난이도 레벨**로 확장한다.
이를 통해 모델별 취약점을 패밀리 단위로 정밀 측정한다.

### 난이도 레벨 정의

| 접미사 | 난이도 | 특징 | 예시 |
|--------|--------|------|------|
| `_001` | easy | 목표 명확, 기술 조건 단순 | "Illumina FASTQ QC 해줘" |
| `_002` | medium | 조건 분기 포함, 유사 도구 혼동 가능 | "nanopore long-read QC, 10x Chromium 아님" |
| `_003` | hard/adversarial | 잘못된 힌트 또는 도메인 혼동 유도 | "RNA-seq인데 WGS 도구를 언급하면서 물어봄" |
| `_004` | ambiguous | 기술 스택 미지정, LLM이 가정을 명시해야 함 | "sequencing data quality check" |

### 파일 명명 규칙

```
gold/domains/{domain}/{family}_{NNN}.yaml

예:
  transcriptomics/raw_qc_001.yaml  ← 기존
  transcriptomics/raw_qc_002.yaml  ← medium (신규)
  transcriptomics/raw_qc_003.yaml  ← hard (신규)
  transcriptomics/raw_qc_004.yaml  ← ambiguous (신규)
```

---

### 도메인별 확장 범위

**1차 타깃 도메인: CS2 Transcriptomics** (가장 복잡, 패밀리 12개)

| 패밀리 | _001 (기존) | _002 추가 포인트 | _003 adversarial |
|--------|------------|-----------------|-----------------|
| raw_qc | Illumina QC | Nanopore QC (NanoPlot 필요) | "BWA로 QC 하면 되지 않나요?" 힌트 |
| adapter_trimming | paired-end TruSeq | single-end + quality filtering | Trimmomatic 대신 fastp을 틀린 설정으로 언급 |
| genome_alignment | hg38 STAR | mm10 mouse genome | "TopHat2 써도 되나요?" (deprecated 도구) |
| pseudo_alignment | kallisto | salmon + decoy-aware index | "STAR도 pseudo-alignment 됩니다" 힌트 |
| read_quantification | featureCounts | HTSeq-count with strand info | "RSEM은 alignment-based입니다" 오개념 |
| differential_expression | edgeR | DESeq2 for unpaired samples | "t-test로 DE 분석하면 안 되나요?" |
| pathway_enrichment | clusterProfiler | fgsea (pre-ranked) | "DAVID는 최신 DB 아닌가요?" |
| sc_preprocessing | scanpy | Seurat (R) | "bulk RNA-seq pipeline 그대로 쓰면 됩니다" |
| sc_clustering | Leiden | Louvain | "k-means clustering이 표준입니다" |
| sc_annotation | SingleR | CellTypist | "수동 marker 기반 annotation이 항상 최선" |
| sc_trajectory | scVelo | Monocle3 | "PCA로 trajectory 분석 됩니다" |
| visualization | scanpy.pl | Seurat DimPlot | "matplotlib scatter plot이면 충분합니다" |

**2차 타깃: CS3 Variant Analysis** (이미 일부 _002 존재, _003/_004 추가)

---

### Gold YAML 작성 기준 (레벨별)

#### `_002` medium 템플릿
```yaml
query_id: {family}_002
family: {family}
nl_text: "..."          # _001보다 구체적 조건 포함
difficulty: medium
tool_specificity: goal_specified
context:
  data_type: ...
  condition_key: value  # 분기 조건 명시

gold:
  tier_1_canonical:
    tools: [...]        # 조건에 맞는 정답
    expected_output_criteria:
      ...
  tier_2_alternative:
    tools: [...]
    functional_equivalence_criteria:
      ...
  tier_3_invalid:
    tools: [deprecated_tool, wrong_domain_tool]  # _001보다 invalid 목록 풍부
```

#### `_003` adversarial 템플릿
```yaml
query_id: {family}_003
family: {family}
nl_text: "..."          # 잘못된 정보/힌트 포함
difficulty: hard
tool_specificity: misleading_hint

gold:
  tier_1_canonical:
    tools: [...]        # 힌트를 무시하고 올바른 도구
    ...
  tier_3_invalid:
    tools: [hint_tool]  # nl_text에서 언급한 잘못된 도구
  adversarial_override:
    bad_hint_tool: hint_tool
    correct_behaviors:
      - "Recognize that hint_tool is inappropriate because ..."
      - "Select canonical_tool instead"
```

#### `_004` ambiguous 템플릿
```yaml
query_id: {family}_004
family: {family}
nl_text: "..."          # 최소한의 정보만 제공
difficulty: medium
tool_specificity: underspecified

gold:
  tier_1_canonical:
    tools: [most_common_default_tool]
    expected_output_criteria:
      ...
  tier_2_alternative:
    tools: [reasonable_alternatives]  # 가정에 따라 여러 답 허용
    functional_equivalence_criteria:
      ...
  # tier_3_invalid는 도메인 밖 도구만 포함
```

---

### 확장 우선순위 및 일정

#### Day 1 — ② 추론 trace 캡처 (코드)
- `result_schema.py` 필드 확장
- `response_parser.py` `ParsedResponse` 반환값 설계
- `runner.py` 연결
- `prompt_builder.py` 구조화 응답 요청 추가
- 기존 테스트 통과 확인

#### Day 2 — ① CS2 Transcriptomics _002 (medium) 12개
- raw_qc, adapter_trimming, genome_alignment, pseudo_alignment, read_quantification
- differential_expression, pathway_enrichment (각 _002)
- sc_preprocessing, sc_clustering, sc_annotation, sc_trajectory, visualization (각 _002)

#### Day 3 — ① CS2 Transcriptomics _003 (adversarial) 선별 6개
- 가장 혼동 가능성 높은 패밀리 우선: genome_alignment, differential_expression, sc_clustering, pseudo_alignment, sc_annotation, adapter_trimming
- adversarial_override 필드 포함

#### Day 4 — ① CS3 Variant Analysis _003/_004 및 CS4 Epigenomics _002
- variant_analysis: read_alignment_003, variant_calling_003, gwas_association_003
- epigenomics: 주요 패밀리 _002 추가

#### Day 5 — 검증 및 소규모 벤치마크 실행
- 전체 확장된 gold 파일로 Claude vs Codex 비교 실행
- 패밀리별 accuracy 히트맵 생성 (CSV 출력)
- `_003` adversarial에서 두 모델의 CRITICAL_ERROR 비율 분석

---

### ① 검증 기준

```python
# 도메인별 쿼리 수
plugin = CS2TranscriptomicsPlugin()
queries = plugin.list_query_ids()
assert len(queries) >= 36   # 12 families × 3 levels (_001~_003)

# adversarial gold 로드
gold = plugin.load_gold("genome_alignment_003")
assert gold.adversarial_override is not None
assert gold.adversarial_override.bad_hint_tool in gold.invalid_tools

# medium 쿼리의 invalid_tools가 _001보다 풍부
gold_001 = plugin.load_gold("genome_alignment_001")
gold_002 = plugin.load_gold("genome_alignment_002")
assert len(gold_002.invalid_tools) >= len(gold_001.invalid_tools)
```

---

## 완료 후 기대 효과

| 지표 | 현재 | 완료 후 |
|------|------|---------|
| CS2 총 gold 쿼리 수 | 12개 | 36~48개 |
| 전체 도메인 gold 쿼리 수 | ~72개 | ~200개 |
| 오답 원인 분석 가능 여부 | 불가 | `reasoning_trace` 기반 분석 가능 |
| Adversarial 내성 측정 | 불가 | 패밀리별 adversarial 성공률 |
| 모델간 비교 신뢰도 | 낮음 (샘플 수 부족) | 통계적으로 유의미한 비교 가능 |

---

## 파일 영향 범위 요약

```
변경:
  llm_interface/llm_core/harness/result_schema.py     (+3 필드)
  llm_interface/llm_core/harness/response_parser.py   (반환 타입 변경)
  llm_interface/llm_core/harness/runner.py            (ParsedResponse 연결)
  llm_interface/llm_core/harness/prompt_builder.py    (JSON 응답 형식 요청)

신규 (gold 파일):
  llm_interface/llm_core/gold/domains/transcriptomics/*_002.yaml  (12개)
  llm_interface/llm_core/gold/domains/transcriptomics/*_003.yaml  (6개)
  llm_interface/llm_core/gold/domains/variant_analysis/*_003.yaml (3개)
  llm_interface/llm_core/gold/domains/epigenomics/*_002.yaml      (6개)

영향 없음:
  py/ (ComfyUI 노드)
  tsr/ (TSR YAML)
  benchmark/ (DomainPlugin — list_query_ids()로 자동 인식)
```
