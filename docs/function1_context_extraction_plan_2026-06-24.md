# Function 1 구현 계획 — LLM Context 추출

**작성일:** 2026-06-24  
**참조:** `docs/project_direction_2026-06-24.md`

---

## 목표

`nl_text`에서 LLM이 context를 직접 추출하여 TSR 엔진에 전달한다.
gold 파일의 `context` 필드는 LLM 추출 결과의 정답(ground truth)으로 활용된다.

---

## 변경 전/후 비교

### 변경 전 (`runner.py` 현재 흐름)
```python
# query.context가 gold 파일에 미리 작성되어 있음
prompt = build_tool_selection_prompt(tsr, query)
# → query.context를 그대로 TSR에 넘김
# LLM은 nl_text를 실질적으로 해석하지 않음
```

### 변경 후
```python
# Step 1: LLM이 nl_text에서 context 추출
extracted_context = await extract_context(adapter, nl_text=query.nl_text, domain_id=query.domain_id)

# Step 2: 추출된 context로 TSR 조회 + 워크플로우 생성
query_with_extracted = replace(query, context=extracted_context)
prompt = build_tool_selection_prompt(tsr, query_with_extracted)

# Step 3: 2단계 평가
context_score = evaluate_context(extracted_context, gold_context=query.context)
# workflow 평가는 기존 GoldEvaluator 그대로
```

---

## 구현 범위

```
신규 파일:
  llm_interface/llm_core/harness/context_extractor.py
  llm_interface/llm_core/harness/context_schema.py
  llm_interface/llm_core/harness/context_evaluator.py

변경 파일:
  llm_interface/llm_core/harness/result_schema.py   (+context 평가 필드)
  llm_interface/llm_core/harness/runner.py          (추출 단계 삽입)
```

---

## 상세 설계

### 1. `context_schema.py` — Context 키 정의

각 도메인이 사용하는 context 키와 허용 값을 정의한다.
TSR의 condition 표현식(`sequencer == 'nanopore'`)에서 역으로 추출 가능한 키 목록이다.

```python
# domain → {key → allowed_values}
CONTEXT_SCHEMA: dict[str, dict[str, list[str]]] = {
    "variant_analysis": {
        "sequencer":      ["illumina", "nanopore", "pacbio"],
        "analysis_type":  ["germline", "somatic", "gwas"],
        "n_samples":      [],   # 정수, 허용 범위 별도 검증
        "organism":       ["homo_sapiens", "mus_musculus", "bacteria", "other"],
    },
    "transcriptomics": {
        "data_type":      ["short_read", "long_read", "single_cell"],
        "paired_end":     ["true", "false"],
        "organism":       ["homo_sapiens", "mus_musculus", "other"],
        "n_samples_per_group": [],
    },
    "epigenomics": {
        "assay":          ["chip_seq", "atac_seq", "bisulfite", "cut_and_run"],
        "sequencer":      ["illumina", "nanopore"],
        "paired_end":     ["true", "false"],
    },
    "metagenomics": {
        "sequencer":      ["illumina", "nanopore", "pacbio"],
        "sample_type":    ["shotgun", "amplicon"],
        "target":         ["taxonomy", "function", "assembly"],
    },
    "genome_assembly": {
        "sequencer":      ["illumina", "nanopore", "pacbio", "hifi"],
        "organism_type":  ["prokaryote", "eukaryote", "metagenome"],
        "coverage":       [],
    },
}
```

---

### 2. `context_extractor.py` — LLM 호출 및 파싱

#### 프롬프트 설계

```python
EXTRACTION_PROMPT_TEMPLATE = """\
You are a bioinformatics data analyst. Extract structured metadata from the
user's natural language description.

Domain: {domain_id}
Query: {nl_text}

Extract ONLY the fields that are explicitly or strongly implied in the query.
Do not guess values that are not mentioned or clearly implied.

Return a JSON object with any of these fields that apply:
{schema_hint}

Rules:
- Use null for fields not mentioned or unclear
- For numeric fields (n_samples, coverage), return integers
- For boolean fields (paired_end), return true or false
- Respond ONLY with a JSON object, no explanation
"""
```

#### 파싱 및 정규화

```python
@dataclass
class ContextExtractionResult:
    extracted: dict          # LLM이 추출한 context
    raw_response: str        # LLM 원문
    parse_error: str | None  # JSON 파싱 실패 시

async def extract_context(
    adapter: LLMProviderAdapter,
    nl_text: str,
    domain_id: str,
    model: str | None = None,
) -> ContextExtractionResult:
    schema = CONTEXT_SCHEMA.get(domain_id, {})
    schema_hint = _format_schema_hint(schema)
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        domain_id=domain_id,
        nl_text=nl_text,
        schema_hint=schema_hint,
    )
    raw = await adapter.generate(prompt, model=model)
    return _parse_extraction_response(raw, schema)
```

---

### 3. `context_evaluator.py` — Context 추출 정확도 평가

gold의 `context`를 정답으로 삼아 추출 결과를 비교한다.

```python
@dataclass
class ContextEvalResult:
    field_scores: dict[str, bool]  # 키별 일치 여부
    precision: float               # 추출한 키 중 맞은 비율
    recall: float                  # gold 키 중 맞게 추출한 비율
    exact_match: bool              # 모든 키가 완전 일치

def evaluate_context(
    extracted: dict,
    gold: dict,
) -> ContextEvalResult:
    """
    gold에 있는 키만 평가 대상으로 삼는다.
    gold에 없는 키를 추가로 추출하는 건 감점하지 않는다 (보수적 평가).
    """
    field_scores = {}
    for key, gold_val in gold.items():
        extracted_val = extracted.get(key)
        field_scores[key] = _values_match(extracted_val, gold_val)

    correct = sum(field_scores.values())
    gold_keys = len(gold)
    extracted_keys = len([k for k in extracted if extracted[k] is not None])

    # precision: 추출한 것 중 맞은 것 (null 제외)
    matched_in_extracted = sum(
        1 for k, v in extracted.items()
        if v is not None and k in gold and _values_match(v, gold[k])
    )
    precision = matched_in_extracted / extracted_keys if extracted_keys else 0.0
    recall = correct / gold_keys if gold_keys else 1.0

    return ContextEvalResult(
        field_scores=field_scores,
        precision=precision,
        recall=recall,
        exact_match=(recall == 1.0 and all(field_scores.values())),
    )

def _values_match(extracted, gold) -> bool:
    if extracted is None:
        return False
    # 문자열 비교: 대소문자 무시
    if isinstance(gold, str):
        return str(extracted).lower() == gold.lower()
    # 숫자 비교: 정수 범위 허용
    if isinstance(gold, (int, float)):
        try:
            return abs(float(extracted) - float(gold)) < 0.01
        except (TypeError, ValueError):
            return False
    return extracted == gold
```

---

### 4. `result_schema.py` — EvalResult 필드 추가

```python
@dataclass
class EvalResult:
    # ... 기존 필드 유지 ...

    # Context 추출 결과 (신규)
    extracted_context: dict = field(default_factory=dict)
    context_precision: float | None = None
    context_recall: float | None = None
    context_exact_match: bool | None = None
    context_field_scores: dict[str, bool] = field(default_factory=dict)
```

`to_dict()`에 추가:
```python
"extracted_context": self.extracted_context,
"context_precision": self.context_precision,
"context_recall": self.context_recall,
"context_exact_match": self.context_exact_match,
"context_field_scores": self.context_field_scores,
```

---

### 5. `runner.py` — context 추출 단계 삽입

기존 코드에서 `prompt = build_tool_selection_prompt(tsr, query)` 이전에 삽입:

```python
# --- Context 추출 (Function 1) ---
ctx_result = await extract_context(
    adapter,
    nl_text=query.nl_text,
    domain_id=query.domain_id,
    model=model,
)
ctx_eval = evaluate_context(ctx_result.extracted, gold_context=query.context)

# 추출된 context로 query 재구성
from dataclasses import replace
query_for_tsr = replace(query, context=ctx_result.extracted)

# 이하 기존 코드 — query 대신 query_for_tsr 사용
prompt = build_tool_selection_prompt(tsr, query_for_tsr)
```

EvalResult 반환 시 context 필드 채우기:
```python
return EvalResult(
    ...
    extracted_context=ctx_result.extracted,
    context_precision=ctx_eval.precision,
    context_recall=ctx_eval.recall,
    context_exact_match=ctx_eval.exact_match,
    context_field_scores=ctx_eval.field_scores,
)
```

---

## 평가 지표 체계

### Stage 1 — Context 추출 정확도

| 지표 | 의미 | 이상적 값 |
|------|------|----------|
| `context_recall` | gold 키 중 올바르게 추출한 비율 | 1.0 |
| `context_precision` | 추출한 키 중 맞은 비율 | 높을수록 좋음 |
| `context_exact_match` | 모든 키가 완전 일치 | True |

### Stage 2 — 워크플로우 정확도 (기존)

| 지표 | 의미 |
|------|------|
| `verdict` | CORRECT_CANONICAL / CORRECT_ALTERNATIVE / INCORRECT / CRITICAL_ERROR |
| `workflow_score` | ComfyUI 노드 구조 일치율 |

### 복합 분석 (두 단계 연결)

```
context_exact_match=True  + verdict=CORRECT_CANONICAL  → 완전 성공
context_exact_match=True  + verdict=INCORRECT          → TSR 또는 프롬프트 문제
context_exact_match=False + verdict=CORRECT_CANONICAL  → context 오추출이지만 우연히 정답 (불안정)
context_exact_match=False + verdict=INCORRECT          → context 추출 실패가 원인
```

---

## 구현 일정

### Day 1
- `context_schema.py` — 5개 도메인 스키마 정의
- `context_extractor.py` — 프롬프트 + 파싱 구현
- `context_evaluator.py` — 정확도 평가 로직

### Day 2
- `result_schema.py` — 필드 추가
- `runner.py` — 추출 단계 삽입
- DeterministicAdapter에서 context 추출 스킵 처리 (pass-through)

### Day 3
- 기존 테스트 통과 확인
- CS3 variant_analysis 전체 쿼리로 Claude vs Codex context 추출 정확도 측정
- 결과 CSV 출력: `query_id, context_recall, context_exact_match, verdict`

---

## 검증 기준

```python
# context 추출이 runner를 통과해야 함
result = await run_query(plugin, query, provider="claude")
assert result.extracted_context != {}
assert result.context_recall is not None

# gold context가 단순한 경우 recall == 1.0이어야 함
# ("I have Illumina WGS reads" → sequencer: illumina)
assert result.context_recall == 1.0

# context 추출 실패가 워크플로우 오답의 원인인지 식별 가능
if not result.context_exact_match and result.verdict == Verdict.INCORRECT:
    assert "sequencer" in result.context_field_scores  # 어떤 키가 틀렸는지 알 수 있음
```

---

## 주의 사항

**DeterministicAdapter 처리:**
DeterministicAdapter는 실제 LLM이 아니므로 context 추출을 건너뛰고
gold의 context를 그대로 사용한다. (기존 동작 유지)

```python
if provider == "deterministic":
    query_for_tsr = query  # gold context 그대로 사용
    ctx_result = None
else:
    ctx_result = await extract_context(...)
    query_for_tsr = replace(query, context=ctx_result.extracted)
```

**gold context가 비어 있는 경우:**
`context: {}` 이면 context 추출 평가를 스킵하고 `context_exact_match=None`으로 설정한다.
