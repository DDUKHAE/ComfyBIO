"""
harness — evaluation harness for ComfyBIO multi-domain benchmark.

Flow:
    HeldOutQuery
        → prompt_builder.build_tool_selection_prompt()
        → LLM adapter (claude / codex / gemini)
        → response_parser.parse_tool_response()
        → GoldEvaluator.evaluate()
        → EvalResult

Entry points:
    runner.run_query()          single query evaluation
    runner.run_domain()         all queries in a domain
    reporter.print_report()     human-readable summary
    reporter.export_jsonl()     machine-readable results
"""
from .result_schema import EvalResult, BenchmarkReport
from .runner import run_query, run_domain
from .reporter import print_report, export_jsonl

__all__ = [
    "EvalResult",
    "BenchmarkReport",
    "run_query",
    "run_domain",
    "print_report",
    "export_jsonl",
]
