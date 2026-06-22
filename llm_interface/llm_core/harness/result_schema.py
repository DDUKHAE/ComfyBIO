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
    context: dict = field(default_factory=dict)

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
            "generated_tools": self.generated_tools,
            "elapsed_s": round(self.elapsed_s, 3),
            "provider": self.provider,
            "model": self.model,
            "error": self.error,
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
