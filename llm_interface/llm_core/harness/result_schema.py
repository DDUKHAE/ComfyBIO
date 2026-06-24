"""Result schema for harness evaluation outputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llm_core.gold.schema import Verdict


@dataclass
class EvalResult:
    """Single-query evaluation result."""
    query_id: str
    domain_id: str
    family: str
    verdict: Verdict
    generated_tools: list[str]
    elapsed_s: float
    provider: str
    model: str | None = None
    error: str | None = None
    raw_response: str = ""
    reasoning_trace: str = ""
    tool_rationale: dict[str, str] = field(default_factory=dict)
    confidence_score: float | None = None
    context: dict = field(default_factory=dict)
    tool_verdict: str = Verdict.INCORRECT.value
    support_status: str = "not_assessed"
    missing_node_classes: list[str] = field(default_factory=list)
    workflow_status: str = "not_evaluated"
    workflow_verdict: str = "not_evaluated"
    workflow_score: float | None = None
    execution_status: str = "not_evaluated"
    readiness_state: str = "untracked"
    acceptance_status: str = "not_configured"
    acceptance_checks: list[dict] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    parser_warnings: list[str] = field(default_factory=list)
    workflow_spec_present: bool = False
    template_id: str | None = None
    evidence_manifest_present: bool = False
    # Context extraction (Function 1)
    extracted_context: dict = field(default_factory=dict)
    context_precision: float | None = None
    context_recall: float | None = None
    context_exact_match: bool | None = None
    context_field_scores: dict[str, bool] = field(default_factory=dict)

    @property
    def is_correct(self) -> bool:
        return self.verdict in (Verdict.CORRECT_CANONICAL, Verdict.CORRECT_ALTERNATIVE)

    @property
    def is_critical(self) -> bool:
        return self.verdict == Verdict.CRITICAL_ERROR

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "domain_id": self.domain_id,
            "family": self.family,
            "verdict": self.verdict.value,
            "tool_verdict": self.tool_verdict,
            "generated_tools": self.generated_tools,
            "elapsed_s": round(self.elapsed_s, 3),
            "provider": self.provider,
            "model": self.model,
            "error": self.error,
            "reasoning_trace": self.reasoning_trace,
            "tool_rationale": self.tool_rationale,
            "confidence_score": self.confidence_score,
            "support_status": self.support_status,
            "missing_node_classes": self.missing_node_classes,
            "workflow_status": self.workflow_status,
            "workflow_verdict": self.workflow_verdict,
            "workflow_score": self.workflow_score,
            "execution_status": self.execution_status,
            "readiness_state": self.readiness_state,
            "acceptance_status": self.acceptance_status,
            "acceptance_checks": self.acceptance_checks,
            "validation_errors": self.validation_errors,
            "parser_warnings": self.parser_warnings,
            "workflow_spec_present": self.workflow_spec_present,
            "template_id": self.template_id,
            "evidence_manifest_present": self.evidence_manifest_present,
            "extracted_context": self.extracted_context,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "context_exact_match": self.context_exact_match,
            "context_field_scores": self.context_field_scores,
        }


@dataclass
class BenchmarkReport:
    """Aggregated report across all evaluated queries."""
    provider: str
    model: str | None
    domain_id: str
    results: list[EvalResult] = field(default_factory=list)

    @property
    def n_total(self) -> int:
        return len(self.results)

    @property
    def n_correct(self) -> int:
        return sum(1 for r in self.results if r.is_correct)

    @property
    def n_canonical(self) -> int:
        return sum(1 for r in self.results if r.verdict == Verdict.CORRECT_CANONICAL)

    @property
    def n_alternative(self) -> int:
        return sum(1 for r in self.results if r.verdict == Verdict.CORRECT_ALTERNATIVE)

    @property
    def n_critical(self) -> int:
        return sum(1 for r in self.results if r.is_critical)

    @property
    def n_errors(self) -> int:
        return sum(1 for r in self.results if r.error is not None)

    @property
    def accuracy(self) -> float:
        return self.n_correct / self.n_total if self.n_total else 0.0

    @property
    def critical_rate(self) -> float:
        return self.n_critical / self.n_total if self.n_total else 0.0

    def by_family(self) -> dict[str, list[EvalResult]]:
        out: dict[str, list[EvalResult]] = {}
        for r in self.results:
            out.setdefault(r.family, []).append(r)
        return out

    def count_by_support_status(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.support_status] = out.get(r.support_status, 0) + 1
        return out

    def count_by_tool_verdict(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.tool_verdict] = out.get(r.tool_verdict, 0) + 1
        return out

    def count_by_workflow_status(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.workflow_status] = out.get(r.workflow_status, 0) + 1
        return out

    def count_by_workflow_verdict(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.workflow_verdict] = out.get(r.workflow_verdict, 0) + 1
        return out

    def count_by_execution_status(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.execution_status] = out.get(r.execution_status, 0) + 1
        return out

    def count_by_readiness_state(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.readiness_state] = out.get(r.readiness_state, 0) + 1
        return out

    def count_by_acceptance_status(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.results:
            out[r.acceptance_status] = out.get(r.acceptance_status, 0) + 1
        return out
