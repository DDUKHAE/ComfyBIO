# Workflow Generation Experiments

이 디렉토리는 하이브리드 워크플로우 생성 연구의 실험 결과와 비교 리포트를 축적하는 위치다.

## 권장 기록 단위

- provider
- model
- mode (`free`, `normalized`, `hybrid`)
- query set / benchmark set
- valid JSON rate
- executable workflow rate
- inter-model agreement
- mean equivalence score
- repair frequency

## 데이터 소스

기본 소스는 `workflow_history.jsonl` 이다. 각 레코드는 다음 필드를 포함한다.

- `raw_workflow_spec`
- `normalized_workflow_spec`
- `final_workflow_spec`
- `intent`
- `template_id`
- `equivalence_score`
- `repair_applied`
- `repair_summary`
- `repair_actions`
- `mode`

## 비교 기준

- `free`: LLM raw spec을 그대로 사용
- `normalized`: deterministic normalization 결과 사용
- `hybrid`: normalization 후 template-guided local repair 결과 사용

## 배치 실행기

대표 benchmark 세트는 [2026-06-15-core-query-set.json](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/benchmarks/2026-06-15-core-query-set.json) 에 저장한다. 이 파일은 `query`, `expected_intent`, `expected_template_id`, `label`을 포함한다.


실험 배치 실행과 Markdown 리포트 생성은 [`workflow_experiments.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_experiments.py)에서 담당한다.

핵심 함수:

- `run_experiment_batch()`
- `run_experiment_batch_sync()`
- `summarize_mode_metrics()`
- `summarize_provider_mode_metrics()`
- `render_experiment_report_markdown()`
- `write_experiment_report()`

추가 도구:

- `scripts/run_workflow_experiment.py`: benchmark 배치 실행 CLI
- `scripts/check_provider_readiness.py`: 설치/인증 상태와 optional readiness probe를 확인하는 CLI

CLI로 바로 실행할 수도 있다.

```bash
python scripts/run_workflow_experiment.py \
  --query-json docs/superpowers/experiments/benchmarks/2026-06-15-core-query-set.json \
  --provider codex --provider claude --provider gemini \
  --mode free --mode normalized --mode hybrid \
  --model codex=gpt-5.5 \
  --model claude=claude-sonnet-4-6 \
  --model gemini=gemini-2.5-pro \
  --repeat 3 \
  --report docs/superpowers/experiments/2026-06-15-mode-comparison.md \
  --title "Mode Comparison"
```

예시:

```python
from pathlib import Path
from harness_core.workflow_experiments import run_experiment_batch_sync, write_experiment_report

records = run_experiment_batch_sync(
    queries=[
        "parse a fasta file and summarize sequence ids",
        "run blast against a nucleotide database",
    ],
    providers=["codex", "claude", "gemini"],
    modes=["free", "normalized", "hybrid"],
    models={
        "codex": "gpt-5.5",
        "claude": "claude-sonnet-4-6",
        "gemini": "gemini-2.5-pro",
    },
    repeats=3,
    persist_history=True,
)

write_experiment_report(
    Path("docs/superpowers/experiments/2026-06-15-mode-comparison.md"),
    records,
    title="Mode Comparison",
)
```

## 권장 리포트 구조

- Overall
- By Mode
- By Provider and Mode
- Record-level table

## 비고

실험 보고서는 날짜별 파일로 추가한다. 예: `2026-06-15-mode-comparison.md`

## 운영 메모

- readiness report는 설치/인증 상태를 보여주지만, provider quota/session limit까지 보장하지는 않는다.
- 실제 실행 가능성은 small smoke benchmark로 다시 확인해야 한다.
- 2026-06-15 기준 live smoke에서 `codex`는 `gpt-5.5`로 동작했고, `claude`는 인증은 되었지만 session limit에 걸려 generation이 실패했다.

## 현재 상태 메모

- provider readiness는 `scripts/check_provider_readiness.py`로 확인한다.
- 다만 readiness는 설치/인증 상태와 실제 generation 가능성을 완전히 동일시하지 않는다. probe를 켜지 않으면 특히 그렇다.
- 2026-06-15 기준 authoritative artifact는 [2026-06-15-provider-smoke-comparison.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-smoke-comparison.md) 이다.
- 같은 날짜의 [2026-06-15-provider-readiness.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-readiness.md) 는 readiness rollout 중간 산출물이라서 보조 지표로만 본다. 최종 provider 판단은 smoke comparison을 우선한다.
- 같은 날짜의 [2026-06-15-codex-failure-diagnostic.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-codex-failure-diagnostic.md) 는 `codex-mini-latest` 대신 `gpt-5.5`가 필요하다는 운영 이슈를 기록한다.

- 상태 종합 메모는 [2026-06-16-operational-status.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-16-operational-status.md) 에 정리했다.

- completion audit는 [2026-06-16-completion-audit.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-16-completion-audit.md) 에 정리했다.
