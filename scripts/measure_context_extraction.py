"""Measure context extraction (Stage 1) performance across providers.

Usage:
    cd /tmp
    PYTHONPATH= python /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/scripts/measure_context_extraction.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "llm_interface"))

from llm_core.benchmark.cs3_variant_analysis_plugin import CS3VariantAnalysisPlugin
from llm_core.benchmark.cs2_transcriptomics_plugin import CS2TranscriptomicsPlugin
from llm_core.harness.context_evaluator import evaluate_context
from llm_core.harness.context_extractor import extract_context
from llm_core.llm_adapters import get_adapter


PROVIDERS = ["claude"]   # add "codex", "gemini" as needed


async def measure_one(provider: str, plugin, query_id: str):
    query = plugin.load_query(query_id)
    if not query.context:
        return None  # nothing to evaluate

    adapter = get_adapter(provider)
    ctx_result = await extract_context(
        adapter,
        nl_text=query.nl_text,
        domain_id=query.domain_id,
    )
    ctx_eval = evaluate_context(ctx_result.extracted, query.context)

    return {
        "provider": provider,
        "domain": query.domain_id,
        "query_id": query_id,
        "nl_text": query.nl_text,
        "gold_context": query.context,
        "extracted_context": ctx_result.extracted,
        "parse_error": ctx_result.parse_error,
        "exact_match": ctx_eval.exact_match,
        "recall": ctx_eval.recall,
        "precision": ctx_eval.precision,
        "field_scores": ctx_eval.field_scores,
    }


async def run_all():
    plugins = [
        CS3VariantAnalysisPlugin(),
        CS2TranscriptomicsPlugin(),
    ]

    all_results = []
    for plugin in plugins:
        query_ids = plugin.list_query_ids()
        print(f"\n[{plugin.domain_id}] {len(query_ids)} queries")
        for qid in query_ids:
            for provider in PROVIDERS:
                try:
                    r = await measure_one(provider, plugin, qid)
                    if r is None:
                        print(f"  {qid}: skipped (no context)")
                        continue
                    mark = "✓" if r["exact_match"] else "✗"
                    print(
                        f"  {mark} [{provider}] {qid}"
                        f"  recall={r['recall']:.2f}"
                        f"  extracted={r['extracted_context']}"
                        + (f"  ERR={r['parse_error']}" if r["parse_error"] else "")
                    )
                    all_results.append(r)
                except Exception as e:
                    print(f"  ! [{provider}] {qid}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for provider in PROVIDERS:
        rows = [r for r in all_results if r["provider"] == provider]
        if not rows:
            continue
        exact = sum(1 for r in rows if r["exact_match"])
        avg_recall = sum(r["recall"] for r in rows) / len(rows)
        parse_errs = sum(1 for r in rows if r["parse_error"])
        print(f"\n{provider}:")
        print(f"  총 쿼리:      {len(rows)}")
        print(f"  exact_match:  {exact}/{len(rows)} ({exact/len(rows)*100:.0f}%)")
        print(f"  avg recall:   {avg_recall:.2f}")
        print(f"  parse errors: {parse_errs}")

        # Domain breakdown
        domains = sorted({r["domain"] for r in rows})
        for domain in domains:
            d_rows = [r for r in rows if r["domain"] == domain]
            d_exact = sum(1 for r in d_rows if r["exact_match"])
            d_recall = sum(r["recall"] for r in d_rows) / len(d_rows)
            print(f"    {domain}: {d_exact}/{len(d_rows)} exact, recall={d_recall:.2f}")

        # Per-field accuracy
        all_field_scores: dict[str, list[bool]] = {}
        for r in rows:
            for field, score in r["field_scores"].items():
                all_field_scores.setdefault(field, []).append(score)
        if all_field_scores:
            print(f"\n  필드별 정확도:")
            for field, scores in sorted(all_field_scores.items()):
                acc = sum(scores) / len(scores)
                print(f"    {field}: {sum(scores)}/{len(scores)} ({acc*100:.0f}%)")

    # Save raw results
    out_path = ROOT / "results" / "context_extraction_results.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\n결과 저장: {out_path}")


if __name__ == "__main__":
    asyncio.run(run_all())
