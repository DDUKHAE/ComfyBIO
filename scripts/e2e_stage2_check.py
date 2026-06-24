"""Stage 2 end-to-end check: extracted_context → TSR → tool selection → gold verdict.

Usage:
    cd /tmp
    PYTHONPATH= python /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/scripts/e2e_stage2_check.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "llm_interface"))

from llm_core.benchmark.cs3_variant_analysis_plugin import CS3VariantAnalysisPlugin
from llm_core.benchmark.cs2_transcriptomics_plugin import CS2TranscriptomicsPlugin
from llm_core.gold.schema import Verdict
from llm_core.harness.runner import run_query


async def run_e2e(provider: str, plugins: list):
    results = []
    for plugin in plugins:
        for qid in plugin.list_query_ids():
            try:
                query = plugin.load_query(qid)
                result = await run_query(plugin, query, provider=provider)
                results.append(result)
            except Exception as e:
                print(f"  ERROR [{provider}] {qid}: {e}")
    return results


def print_summary(label: str, results):
    total = len(results)
    if total == 0:
        print(f"{label}: no results")
        return

    # tool_verdict (biological tool selection accuracy)
    tv_correct = sum(1 for r in results if r.tool_verdict in ("correct_canonical", "correct_alternative"))
    tv_critical = sum(1 for r in results if r.tool_verdict == "critical_error")
    tv_incorrect = sum(1 for r in results if r.tool_verdict == "incorrect")

    # final verdict (tool + workflow + node implementation)
    final_correct = sum(1 for r in results if r.is_correct)
    final_critical = sum(1 for r in results if r.is_critical)
    final_incorrect = sum(1 for r in results if r.verdict == Verdict.INCORRECT and not r.is_critical)

    # support_status breakdown
    impl_required = sum(1 for r in results if r.support_status == "implementation_required")
    supported = sum(1 for r in results if r.support_status == "supported")

    # context extraction stats
    ctx_results = [r for r in results if r.context_exact_match is not None]
    ctx_exact = sum(1 for r in ctx_results if r.context_exact_match)

    print(f"\n{'='*64}")
    print(f"{label} — {total} queries")
    print(f"{'='*64}")
    if ctx_results:
        print(f"  Stage 1 — Context extraction:")
        print(f"    exact_match:           {ctx_exact}/{len(ctx_results)} ({ctx_exact/len(ctx_results)*100:.0f}%)")
    print(f"  Stage 2 — Tool selection (tool_verdict):")
    print(f"    CORRECT:               {tv_correct}/{total} ({tv_correct/total*100:.0f}%)")
    print(f"    INCORRECT:             {tv_incorrect}/{total}")
    print(f"    CRITICAL_ERROR:        {tv_critical}/{total}")
    print(f"  Final verdict (tool + workflow + node):")
    print(f"    CORRECT:               {final_correct}/{total} ({final_correct/total*100:.0f}%)")
    print(f"    INCORRECT:             {final_incorrect}/{total}")
    print(f"    CRITICAL_ERROR:        {final_critical}/{total}")
    print(f"  Node implementation:")
    print(f"    supported:             {supported}/{total}")
    print(f"    implementation_required: {impl_required}/{total}")

    # Show tool-correct but final-incorrect (node gap)
    node_gap = [r for r in results
                if r.tool_verdict in ("correct_canonical", "correct_alternative")
                and not r.is_correct]
    if node_gap:
        print(f"\n  Tool correct but final INCORRECT ({len(node_gap)} — node/template gap):")
        for r in node_gap:
            print(f"    {r.query_id:<40} support={r.support_status} workflow={r.workflow_verdict}")

    # Show critical errors
    crits = [r for r in results if r.is_critical or r.tool_verdict == "critical_error"]
    if crits:
        print(f"\n  CRITICAL_ERROR:")
        for r in crits:
            print(f"    {r.query_id:<40} tools={r.generated_tools}")

    # Show stage-1 failures
    s1_fail = [r for r in results if r.context_exact_match is False]
    if s1_fail:
        print(f"\n  Stage 1 failures:")
        for r in s1_fail:
            print(f"    {r.query_id:<40} recall={r.context_recall:.2f} extracted={r.extracted_context}")


async def main():
    plugins = [CS3VariantAnalysisPlugin(), CS2TranscriptomicsPlugin()]

    print("Running full pipeline (Claude — Stage 1 + Stage 2)...")
    claude_results = await run_e2e("claude", plugins)
    print_summary("CLAUDE (Stage 1 + Stage 2)", claude_results)


if __name__ == "__main__":
    asyncio.run(main())
