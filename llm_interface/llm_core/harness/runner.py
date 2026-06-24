"""Harness runner — connects query → LLM → evaluation → EvalResult.

Usage:
    result = await run_query(plugin, query, provider="claude")
    report = await run_domain(plugin, queries, provider="claude")
"""
from __future__ import annotations

import asyncio
import time

from llm_core.benchmark.domain_plugin import DomainPlugin
from pathlib import Path

from llm_core.benchmark.query_schema import HeldOutQuery
from llm_core.evidence.readiness import (
    load_acceptance_fixture_for_workflow,
    load_workflow_evidence,
    summarize_readiness,
)
from llm_core.gold.evaluator import GoldEvaluator
from llm_core.gold.schema import Verdict
from llm_core.harness.static_validator import validate_repository_state
from llm_core.llm_adapters import get_adapter
from llm_core.workflow_guidance.support_assessment import (
    assess_family_support,
    assess_prompt_support,
    load_node_registry,
)
from llm_core.workflow_guidance.template_registry import get_template_for_domain_family

from .candidate_parser import parse_candidate_workflow
from .context_evaluator import ContextEvalResult, evaluate_context
from .context_extractor import ContextExtractionResult, extract_context
from .execution_router import resolve_output_metrics
from .prompt_builder import build_tool_selection_prompt
from .result_schema import BenchmarkReport, EvalResult
from .workflow_validator import validate_candidate_workflow


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
    adapter = get_adapter(provider)

    # --- Stage 1: Context extraction (Function 1) ---
    # Deterministic provider skips extraction and uses gold context directly.
    ctx_extraction: ContextExtractionResult | None = None
    ctx_eval: ContextEvalResult | None = None
    query_for_tsr = query

    if provider != "deterministic":
        ctx_extraction = await extract_context(
            adapter,
            nl_text=query.nl_text,
            domain_id=query.domain_id,
            model=model,
        )
        if not ctx_extraction.skipped and not ctx_extraction.parse_error:
            from dataclasses import replace as _replace
            query_for_tsr = _replace(query, context=ctx_extraction.extracted)
        ctx_eval = evaluate_context(
            ctx_extraction.extracted,
            query.context,
        )

    prompt = build_tool_selection_prompt(tsr, query_for_tsr)

    raw_response = ""
    error: str | None = None
    generated_tools: list[str] = []
    reasoning_trace = ""
    tool_rationale: dict[str, str] = {}
    confidence_score: float | None = None
    verdict = Verdict.INCORRECT
    tool_verdict = Verdict.INCORRECT
    support_status = "supported"
    workflow_status = "not_evaluated"
    workflow_verdict = "not_evaluated"
    workflow_score: float | None = None
    execution_status = "not_evaluated"
    readiness_state = "untracked"
    acceptance_status = "not_configured"
    acceptance_checks: list[dict] = []
    validation_errors: list[str] = []
    parser_warnings: list[str] = []
    workflow_spec_present = False
    template_id: str | None = None
    evidence_manifest_present = False
    workflow_registry = None
    missing_node_classes: list[str] = []

    repo_root = Path(__file__).resolve().parents[3]
    evidence = load_workflow_evidence(repo_root, plugin.domain_id, query.family)
    evidence_manifest_present = evidence is not None
    fixture_manifest = load_acceptance_fixture_for_workflow(repo_root, plugin.domain_id, query.family)
    execution_summary = resolve_output_metrics(plugin, query, repo_root)
    output_metrics = execution_summary["metrics"] if isinstance(execution_summary.get("metrics"), dict) else {}
    readiness_summary = summarize_readiness(
        evidence,
        output_metrics,
        fixture_manifest,
    )
    readiness_state = readiness_summary["readiness"]
    acceptance_status = readiness_summary["acceptance_status"]
    acceptance_checks = readiness_summary["acceptance_checks"]
    execution_status = readiness_summary["evidence_source"]

    static_report = validate_repository_state()
    if static_report.has_errors:
        support_status = "static_validation_failed"
        return EvalResult(
            query_id=query.query_id,
            domain_id=query.domain_id,
            family=query.family,
            verdict=Verdict.INCORRECT,
            tool_verdict=Verdict.INCORRECT.value,
            generated_tools=[],
            elapsed_s=0.0,
            provider=provider,
            model=model,
            error="static_validation_failed",
            raw_response="",
            context=query.context,
            support_status=support_status,
            workflow_status=workflow_status,
            workflow_verdict=workflow_verdict,
            workflow_score=workflow_score,
            execution_status=execution_status,
            missing_node_classes=missing_node_classes,
            readiness_state=readiness_state,
            acceptance_status=acceptance_status,
            acceptance_checks=acceptance_checks,
            validation_errors=validation_errors,
            parser_warnings=parser_warnings,
            workflow_spec_present=workflow_spec_present,
            template_id=template_id,
            evidence_manifest_present=evidence_manifest_present,
        )

    if plugin.domain_id == "bioinformatics":
        support = assess_prompt_support(query.nl_text)
        support_status = support["status"]
        template_id = support.get("template_id")
        missing_node_classes = list(support.get("missing_node_classes", []))
        workflow_registry = load_node_registry() if template_id else None
        if support["status"] == "research_required":
            return EvalResult(
                query_id=query.query_id,
                domain_id=query.domain_id,
                family=query.family,
                verdict=Verdict.INCORRECT,
                tool_verdict=Verdict.INCORRECT.value,
                generated_tools=[],
                elapsed_s=0.0,
                provider=provider,
                model=model,
                error=f"research_required:{support['intent']}",
                raw_response="",
                context=query.context,
                support_status=support_status,
                workflow_status="research_required",
                workflow_verdict=workflow_verdict,
                workflow_score=workflow_score,
                execution_status=execution_status,
                missing_node_classes=missing_node_classes,
                readiness_state=readiness_state,
                acceptance_status=acceptance_status,
                acceptance_checks=acceptance_checks,
                validation_errors=validation_errors,
                parser_warnings=parser_warnings,
                workflow_spec_present=workflow_spec_present,
                template_id=template_id,
                evidence_manifest_present=evidence_manifest_present,
            )

    if template_id is None:
        fallback_template = get_template_for_domain_family(plugin.domain_id, query.family)
        if fallback_template is not None:
            template_id = fallback_template.get("template_id")

    if template_id is not None:
        workflow_registry = load_node_registry()
        if plugin.domain_id != "bioinformatics":
            support = assess_family_support(plugin.domain_id, query.family, registry=workflow_registry)
            support_status = support["status"]
            missing_node_classes = list(support.get("missing_node_classes", []))
            if support_status == "supported" and workflow_status == "not_evaluated":
                workflow_status = "template_registered"
            elif support_status == "implementation_required":
                workflow_status = "implementation_required"

    t0 = time.monotonic()
    try:
        raw_response = await asyncio.wait_for(
            adapter.generate(prompt, model=model) if _accepts_model(adapter) else adapter.generate(prompt),
            timeout=timeout_s,
        )
        candidate = parse_candidate_workflow(
            raw_response,
            domain_id=plugin.domain_id,
            family=query.family,
            registry=workflow_registry,
        )
        generated_tools = candidate.selected_tools
        reasoning_trace = candidate.reasoning_trace
        tool_rationale = candidate.tool_rationale
        confidence_score = candidate.confidence_score
        parser_warnings = candidate.parser_warnings
        workflow_spec_present = candidate.workflow_spec is not None

        workflow_validation = validate_candidate_workflow(
            candidate.workflow_spec,
            template_id=template_id,
        )
        workflow_status = workflow_validation["workflow_status"]
        workflow_verdict = workflow_validation["workflow_verdict"]
        workflow_score = workflow_validation["workflow_score"]
        validation_errors = workflow_validation["validation_errors"]

        try:
            gold = plugin.load_gold(query.query_id)
            evaluator = GoldEvaluator(gold)
            tool_verdict = evaluator.evaluate(
                generated_tools,
                output_metrics if _supports_output_validation(gold, output_metrics) else {},
            )
            verdict = _compose_final_verdict(
                tool_verdict=tool_verdict,
                workflow_verdict=workflow_verdict,
                workflow_score=workflow_score,
                template_id=template_id,
                support_status=support_status,
                readiness_state=readiness_state,
                acceptance_status=acceptance_status,
                evidence_manifest_present=evidence_manifest_present,
            )
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
        tool_verdict=tool_verdict.value,
        generated_tools=generated_tools,
        elapsed_s=elapsed,
        provider=provider,
        model=model,
        error=error,
        raw_response=raw_response,
        reasoning_trace=reasoning_trace,
        tool_rationale=tool_rationale,
        confidence_score=confidence_score,
        context=query.context,
        support_status=support_status,
        workflow_status=workflow_status,
        workflow_verdict=workflow_verdict,
        workflow_score=workflow_score,
        execution_status=execution_status,
        missing_node_classes=missing_node_classes,
        readiness_state=readiness_state,
        acceptance_status=acceptance_status,
        acceptance_checks=acceptance_checks,
        validation_errors=validation_errors,
        parser_warnings=parser_warnings,
        workflow_spec_present=workflow_spec_present,
        template_id=template_id,
        evidence_manifest_present=evidence_manifest_present,
        **_context_eval_kwargs(ctx_extraction, ctx_eval),
    )


def _context_eval_kwargs(
    extraction: "ContextExtractionResult | None",
    evaluation: "ContextEvalResult | None",
) -> dict:
    """Build context-extraction keyword args for EvalResult."""
    if extraction is None or evaluation is None:
        return {}
    return {
        "extracted_context": extraction.extracted,
        "context_precision": evaluation.precision,
        "context_recall": evaluation.recall,
        "context_exact_match": evaluation.exact_match,
        "context_field_scores": evaluation.field_scores,
    }


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



def _supports_output_validation(gold, output_metrics: dict[str, object]) -> bool:
    """Return True when runtime or fixture metrics can validate gold output criteria."""
    if not output_metrics:
        return False

    criterion_keys = set(gold.canonical.expected_output_criteria)
    criterion_keys.update(gold.alternatives.functional_equivalence_criteria)
    return bool(criterion_keys) and criterion_keys.issubset(output_metrics)


def _compose_final_verdict(
    *,
    tool_verdict: Verdict,
    workflow_verdict: str,
    workflow_score: float | None,
    template_id: str | None,
    support_status: str,
    readiness_state: str,
    acceptance_status: str,
    evidence_manifest_present: bool,
) -> Verdict:
    """Compose a conservative final verdict from tool, structure, and readiness checks."""
    if tool_verdict == Verdict.CRITICAL_ERROR or workflow_verdict == Verdict.CRITICAL_ERROR.value:
        return Verdict.CRITICAL_ERROR

    if tool_verdict not in (Verdict.CORRECT_CANONICAL, Verdict.CORRECT_ALTERNATIVE):
        return tool_verdict

    if support_status in {"implementation_required", "research_required", "static_validation_failed"}:
        return Verdict.INCORRECT

    if template_id and workflow_verdict != Verdict.CORRECT_CANONICAL.value:
        return Verdict.INCORRECT

    if template_id and (workflow_score is None or workflow_score < 0.95):
        return Verdict.INCORRECT

    if acceptance_status == "failed":
        return Verdict.INCORRECT

    if evidence_manifest_present and readiness_state not in {"harness_validated", "analysis_ready"}:
        return Verdict.INCORRECT

    if template_id and readiness_state in {"research_candidate", "domain_validated"} and acceptance_status != "passed":
        return Verdict.INCORRECT

    return tool_verdict
