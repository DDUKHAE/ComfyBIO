"""Build tool-selection prompts for LLM evaluation.

Each prompt gives the LLM:
  1. Domain description and step context
  2. The natural-language query
  3. Available tools per applicable step (from TSR, filtered by context)
  4. JSON output format instruction

The LLM is NOT told which tool is canonical — that would defeat the benchmark.
"""
from __future__ import annotations

from llm_core.benchmark.query_schema import HeldOutQuery
from llm_core.tsr.engine import TSREngine
from llm_core.tsr.schema import DomainTSR, ToolValidity

_SYSTEM_PREAMBLE = """\
You are a bioinformatics workflow expert. Your task is to select the best \
tool(s) for the given analysis step.

Rules:
- Choose tools that are scientifically appropriate for the data type and goal.
- Do NOT choose tools that are known to be incorrect for the context.
- Respond ONLY with a JSON object. No prose, no explanation outside the JSON.
"""

_OUTPUT_FORMAT = """\
Output format (choose one):

Single-step query (select one tool):
{"step": "<step_family>", "tool": "<tool_name>"}

Multi-step query (select one tool per step):
{"tools": {"<step_family>": "<tool_name>", ...}}
"""


def build_tool_selection_prompt(
    tsr: DomainTSR,
    query: HeldOutQuery,
) -> str:
    """Build a prompt for tool selection given a TSR and a held-out query."""
    engine = TSREngine(tsr)

    # Collect candidate tools for steps relevant to this query's family
    step_sections = _build_step_sections(engine, tsr, query)

    parts = [
        _SYSTEM_PREAMBLE,
        f"Domain: {tsr.domain_id}",
        f"Domain description: {tsr.description}",
        "",
        f"Query: {query.nl_text}",
        "",
    ]

    if query.context:
        ctx_lines = "\n".join(f"  {k}: {v}" for k, v in query.context.items())
        parts += ["Data context:", ctx_lines, ""]

    if step_sections:
        parts += ["Available tools per analysis step:", *step_sections, ""]

    parts.append(_OUTPUT_FORMAT)
    return "\n".join(parts)


def _build_step_sections(
    engine: TSREngine,
    tsr: DomainTSR,
    query: HeldOutQuery,
) -> list[str]:
    """Return formatted tool lists for each step in the domain TSR."""
    seen_steps: set[str] = set()
    lines: list[str] = []

    for rule in tsr.steps:
        if rule.step_id in seen_steps:
            continue
        # Only include tools that are NOT marked invalid (don't reveal canonical)
        visible = [
            t for t in rule.tools
            if t.validity != ToolValidity.INVALID
        ]
        if not visible:
            continue
        tool_names = ", ".join(t.tool_id for t in visible)
        lines.append(f"  {rule.step_id} ({rule.step_name}): {tool_names}")
        seen_steps.add(rule.step_id)

    return lines
