"""Report generation for benchmark results.

Provides:
  print_report()   — human-readable table to stdout
  export_jsonl()   — one JSON line per EvalResult to a file
  to_dataframe()   — pandas DataFrame (optional, if pandas available)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from llm_core.gold.schema import Verdict

from .result_schema import BenchmarkReport, EvalResult


def print_report(report: BenchmarkReport, file=None) -> None:
    """Print a human-readable benchmark report to stdout (or `file`)."""
    out = file or sys.stdout

    header = (
        f"\n{'='*60}\n"
        f"  ComfyBIO Benchmark — {report.domain_id}\n"
        f"  Provider : {report.provider}"
        + (f" / {report.model}" if report.model else "")
        + f"\n{'='*60}"
    )
    print(header, file=out)

    if not report.results:
        print("  (no results)", file=out)
        return

    print(
        f"\n  Total queries : {report.n_total}\n"
        f"  Correct       : {report.n_correct} ({report.accuracy*100:.1f}%)\n"
        f"    Canonical   : {report.n_canonical}\n"
        f"    Alternative : {report.n_alternative}\n"
        f"  Critical error: {report.n_critical}\n"
        f"  LLM errors    : {report.n_errors}\n",
        file=out,
    )

    # Per-family breakdown
    print("  By family:", file=out)
    for family, results in sorted(report.by_family().items()):
        n = len(results)
        correct = sum(1 for r in results if r.is_correct)
        critical = sum(1 for r in results if r.is_critical)
        flag = " ⚠" if critical else ""
        print(f"    {family:<30} {correct}/{n}{flag}", file=out)

    # First 5 failures
    failures = [r for r in report.results if not r.is_correct]
    if failures:
        print("\n  Sample failures:", file=out)
        for r in failures[:5]:
            print(
                f"    [{r.verdict.value}] {r.query_id} "
                f"→ tools={r.generated_tools}",
                file=out,
            )

    print("=" * 60, file=out)


def export_jsonl(report: BenchmarkReport, path: str | Path) -> Path:
    """Write one JSON line per EvalResult to `path`.

    Format is compatible with pandas.read_json(lines=True).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        for result in report.results:
            f.write(json.dumps(result.to_dict()) + "\n")
    return dest


def to_dataframe(report: BenchmarkReport):
    """Return a pandas DataFrame of results (requires pandas)."""
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for to_dataframe()") from e

    rows = [r.to_dict() for r in report.results]
    return pd.DataFrame(rows)


def summary_dict(report: BenchmarkReport) -> dict:
    """Return a compact summary dict suitable for JSON serialization."""
    return {
        "domain_id": report.domain_id,
        "provider": report.provider,
        "model": report.model,
        "n_total": report.n_total,
        "n_correct": report.n_correct,
        "n_canonical": report.n_canonical,
        "n_alternative": report.n_alternative,
        "n_critical": report.n_critical,
        "n_errors": report.n_errors,
        "accuracy": round(report.accuracy, 4),
        "critical_rate": round(report.critical_rate, 4),
        "by_family": {
            family: {
                "n": len(results),
                "correct": sum(1 for r in results if r.is_correct),
            }
            for family, results in report.by_family().items()
        },
    }
