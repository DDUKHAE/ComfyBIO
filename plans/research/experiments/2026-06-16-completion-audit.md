# Completion Audit

## Scope

이 문서는 2026-06-16 기준으로 아래 두 계획 문서의 구현 완료 여부와 남은 운영 이슈를 현재 작업트리 기준으로 정리한다.

- [2026-06-15-hybrid-workflow-generation-plan.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/plans/2026-06-15-hybrid-workflow-generation-plan.md)
- [2026-06-15-template-workflow-strengthening-plan.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/plans/2026-06-15-template-workflow-strengthening-plan.md)

## Audit Summary

| Area | Status | Evidence |
|---|---|---|
| hybrid architecture code path | implemented | `llm_interface/harness_core/workflow_guidance/*`, `llm_runner.py`, `workflow_history.py`, `harness_nodes/__init__.py` |
| template strengthening | implemented | template files, equivalence/repair logic, template benchmark report |
| experiment runner and reporting | implemented | `workflow_experiments.py`, `scripts/run_workflow_experiment.py`, benchmark JSON sets, dated markdown reports |
| provider readiness tooling | implemented | `scripts/check_provider_readiness.py` |
| multi-provider operational completeness | incomplete | provider-specific external constraints remain |

## Hybrid Plan Mapping

### Implemented

- guidance package and canonical template registry
- deterministic intent classification
- workflow normalization
- equivalence scoring
- local repair with structured repair actions
- `free` / `normalized` / `hybrid` modes
- API/history metadata persistence
- experiment runner CLI and benchmark reporting

Primary evidence:

- [`llm_interface/harness_core/workflow_guidance/__init__.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/__init__.py)
- [`intent_classifier.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/intent_classifier.py)
- [`template_registry.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/template_registry.py)
- [`workflow_normalizer.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/workflow_normalizer.py)
- [`workflow_equivalence.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/workflow_equivalence.py)
- [`workflow_repair.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/workflow_repair.py)
- [`llm_runner.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/llm_runner.py)
- [`workflow_history.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_history.py)
- [`__init__.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_nodes/__init__.py)
- [`workflow_experiments.py`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_experiments.py)
- [`run_workflow_experiment.py`](/home/ydj/main/ComfyBIO_biopython/scripts/run_workflow_experiment.py)

### Not Proven Complete

- provider-environment completeness across all intended LLMs
- stable live execution on every installed/authenticated provider at the same time

Current blockers are external-state/operational rather than missing local architecture.

## Template Plan Mapping

### Implemented

- canonical `required_edges` for representative template families
- expanded intent coverage beyond the original 5 families
- edge-sensitive equivalence scoring
- structured repair actions
- fixture-driven template quality checks
- template coverage and benchmark documentation

Primary evidence:

- template directory:
  - [`templates/`](/home/ydj/main/ComfyBIO_biopython/llm_interface/harness_core/workflow_guidance/templates)
- benchmark report:
  - [2026-06-15-template-coverage-benchmark.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-template-coverage-benchmark.md)

### Not Proven Complete

- no claim is made here that every domain family is exhaustively covered
- no claim is made here that provider outputs are stable independent of provider operational state

## Provider Status Snapshot

Authoritative interpretation order:

1. [2026-06-15-provider-smoke-comparison.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-smoke-comparison.md)
2. [2026-06-15-codex-failure-diagnostic.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-codex-failure-diagnostic.md)
3. [2026-06-15-provider-readiness.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-readiness.md)

Snapshot:

- `deterministic`: usable
- `codex`: usable with `gpt-5.5`
- `claude`: authenticated, but live generation was blocked by session limit in the recorded smoke run
- `gemini`: not ready in this environment

## Remaining Work

The remaining work in this thread is mostly operational:

1. rerun the live provider smoke benchmark when `claude` session limit is no longer active
2. install/authenticate `gemini` and add it to the same benchmark matrix
3. optionally regenerate the readiness artifact after the probe rollout stabilizes

## Conclusion

As of 2026-06-16, the local implementation requested by the two plans is substantially complete. What remains is not core code-path construction but provider-environment convergence and refreshed live experiment artifacts.
