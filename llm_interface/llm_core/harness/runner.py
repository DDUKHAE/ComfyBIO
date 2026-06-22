"""Harness runner — connects query → LLM → evaluation → EvalResult.

Usage:
    result = await run_query(plugin, query, provider="claude")
    report = await run_domain(plugin, queries, provider="claude")
"""
from __future__ import annotations

import asyncio
import time

from llm_core.benchmark.domain_plugin import DomainPlugin
from llm_core.benchmark.query_schema import HeldOutQuery
from llm_core.gold.evaluator import GoldEvaluator
from llm_core.gold.schema import Verdict
from llm_core.llm_adapters import get_adapter

from .prompt_builder import build_tool_selection_prompt
from .response_parser import parse_tool_response
from .result_schema import BenchmarkReport, EvalResult


async def run_query(
    plugin: DomainPlugin,
    query: HeldOutQuery,
    provider: str,
    model: str | None = None,
    timeout_s: float = 60.0,
) -> EvalResult:
    """Evaluate a single HeldOutQuery against an LLM provider.

    Steps:
      1. Build domain-aware tool-selection prompt
      2. Call LLM adapter
      3. Parse tool list from response
      4. Evaluate against gold criteria
      5. Return EvalResult
    """
    tsr = plugin.get_tsr()
    prompt = build_tool_selection_prompt(tsr, query)
    adapter = get_adapter(provider)

    raw_response = ""
    error: str | None = None
    generated_tools: list[str] = []
    verdict = Verdict.INCORRECT

    t0 = time.monotonic()
    try:
        raw_response = await asyncio.wait_for(
            adapter.generate(prompt, model=model) if _accepts_model(adapter) else adapter.generate(prompt),
            timeout=timeout_s,
        )
        generated_tools = parse_tool_response(raw_response)

        try:
            gold = plugin.load_gold(query.query_id)
            evaluator = GoldEvaluator(gold)
            verdict = evaluator.evaluate(generated_tools, {})
        except FileNotFoundError:
            # Gold criteria not yet written for this query
            verdict = Verdict.INCORRECT
            error = f"no_gold_criteria:{query.query_id}"

    except asyncio.TimeoutError:
        error = f"timeout:{timeout_s}s"
        verdict = Verdict.INCORRECT
    except Exception as exc:
        error = f"{type(exc).__name__}:{exc}"
        verdict = Verdict.INCORRECT

    elapsed = time.monotonic() - t0

    return EvalResult(
        query_id=query.query_id,
        domain_id=query.domain_id,
        family=query.family,
        verdict=verdict,
        generated_tools=generated_tools,
        elapsed_s=elapsed,
        provider=provider,
        model=model,
        error=error,
        raw_response=raw_response,
        context=query.context,
    )


async def run_domain(
    plugin: DomainPlugin,
    queries: list[HeldOutQuery],
    provider: str,
    model: str | None = None,
    concurrency: int = 4,
    timeout_s: float = 60.0,
) -> BenchmarkReport:
    """Evaluate all queries for a domain with bounded concurrency.

    Args:
        plugin: Domain plugin (CS2–CS6).
        queries: List of HeldOutQuery to evaluate.
        provider: LLM provider name ("claude", "codex", "gemini").
        model: Optional model override.
        concurrency: Max parallel LLM calls.
        timeout_s: Per-query timeout.

    Returns:
        BenchmarkReport with all EvalResults.
    """
    report = BenchmarkReport(
        provider=provider,
        model=model,
        domain_id=plugin.domain_id,
    )
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(q: HeldOutQuery) -> EvalResult:
        async with sem:
            return await run_query(plugin, q, provider, model, timeout_s)

    results = await asyncio.gather(*(_bounded(q) for q in queries))
    report.results = list(results)
    return report


def _accepts_model(adapter) -> bool:
    """Check if the adapter's generate() accepts a `model` keyword."""
    import inspect
    sig = inspect.signature(adapter.generate)
    return "model" in sig.parameters or any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in sig.parameters.values()
    )
