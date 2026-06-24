"""LLM-based context extraction from natural language queries."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from llm_core.llm_adapters import LLMProviderAdapter

from .context_schema import format_schema_hint, get_schema

_EXTRACTION_PROMPT_TEMPLATE = """\
You are a bioinformatics data analyst. Extract structured metadata from the user's \
natural language description.

Domain: {domain_id}
Query: {nl_text}

Extract ONLY the fields that are explicitly stated or strongly implied in the query.
Do not guess values that are not mentioned or clearly implied.

Available fields for this domain:
{schema_hint}

Rules:
- Use null for any field not mentioned or unclear
- For integer fields (n_samples, n_samples_per_group), return a number
- Respond ONLY with a JSON object — no explanation, no prose

Example output:
{{"sequencer": "illumina", "analysis_type": "germline", "n_samples": null}}
"""


@dataclass
class ContextExtractionResult:
    extracted: dict                          # structured context LLM produced
    raw_response: str                        # raw LLM output
    parse_error: str | None = None           # set if JSON parsing failed
    skipped: bool = False                    # True for deterministic/no-op providers


async def extract_context(
    adapter: LLMProviderAdapter,
    nl_text: str,
    domain_id: str,
    model: str | None = None,
) -> ContextExtractionResult:
    """Ask the LLM to extract structured context from nl_text.

    Returns a ContextExtractionResult. On parse failure, extracted is {} and
    parse_error describes what went wrong.
    """
    schema = get_schema(domain_id)
    if not schema:
        return ContextExtractionResult(extracted={}, raw_response="", skipped=True)

    prompt = _EXTRACTION_PROMPT_TEMPLATE.format(
        domain_id=domain_id,
        nl_text=nl_text,
        schema_hint=format_schema_hint(domain_id),
    )

    try:
        import inspect
        sig = inspect.signature(adapter.generate)
        if "model" in sig.parameters or any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        ):
            raw = await adapter.generate(prompt, model=model)
        else:
            raw = await adapter.generate(prompt)
    except Exception as exc:
        return ContextExtractionResult(
            extracted={},
            raw_response="",
            parse_error=f"adapter_error:{exc}",
        )

    return _parse_extraction_response(raw, schema)


def _parse_extraction_response(raw: str, schema: dict[str, list[str]]) -> ContextExtractionResult:
    """Parse LLM response into a validated context dict."""
    # Try to find a JSON object in the response
    json_str = _extract_json_block(raw)
    if json_str is None:
        return ContextExtractionResult(
            extracted={},
            raw_response=raw,
            parse_error="no_json_found",
        )

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        return ContextExtractionResult(
            extracted={},
            raw_response=raw,
            parse_error=f"json_decode_error:{exc}",
        )

    if not isinstance(data, dict):
        return ContextExtractionResult(
            extracted={},
            raw_response=raw,
            parse_error="response_not_a_dict",
        )

    extracted = _normalize(data, schema)
    return ContextExtractionResult(extracted=extracted, raw_response=raw)


def _extract_json_block(text: str) -> str | None:
    """Return the first JSON object found in text, handling markdown code fences."""
    # Strip markdown fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)

    # Bare JSON object
    bare = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if bare:
        return bare.group(0)

    return None


def _normalize(data: dict, schema: dict[str, list[str] | None]) -> dict:
    """Keep only schema keys; coerce types; drop null values."""
    out: dict = {}
    for key, allowed in schema.items():
        if key not in data:
            continue
        val = data[key]
        if val is None:
            continue

        if allowed is None:
            # Bool field
            if isinstance(val, bool):
                out[key] = val
            elif str(val).lower() in ("true", "1", "yes"):
                out[key] = True
            elif str(val).lower() in ("false", "0", "no"):
                out[key] = False
            # Silently drop unrecognized bool values
        elif allowed:
            # String enum — normalize to lowercase
            normalized = str(val).lower().strip()
            if normalized in [v.lower() for v in allowed]:
                # Return the canonical casing from schema
                out[key] = next(v for v in allowed if v.lower() == normalized)
            # Silently drop unrecognized values
        else:
            # Integer field
            try:
                out[key] = int(val)
            except (TypeError, ValueError):
                pass

    return out
