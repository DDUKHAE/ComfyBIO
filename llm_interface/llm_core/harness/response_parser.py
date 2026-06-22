"""Parse LLM tool-selection responses into a flat tool list.

Handles:
  {"step": "adapter_trimming", "tool": "fastp"}
  {"tools": {"adapter_trimming": "fastp", "alignment": "STAR"}}
  {"tools": ["fastp", "STAR"]}   (plain list)
  Free-text fallback: scans for known tool names
"""
from __future__ import annotations

import json
import re


def parse_tool_response(text: str) -> list[str]:
    """Extract tool names from an LLM response string.

    Returns an empty list if no tools can be extracted.
    """
    text = text.strip()
    if not text:
        return []

    # Try to extract JSON from the response
    json_obj = _extract_first_json(text)
    if json_obj is not None:
        tools = _tools_from_json(json_obj)
        if tools:
            return tools

    # Fallback: scan for quoted identifiers or known patterns
    return _extract_tool_names_heuristic(text)


def _extract_first_json(text: str) -> dict | list | None:
    """Extract the first valid JSON object or array from text."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)

    for match in re.finditer(r"[\[{]", text):
        candidate = text[match.start():]
        for end in range(len(candidate), 0, -1):
            try:
                obj = json.loads(candidate[:end])
                if isinstance(obj, (dict, list)):
                    return obj
            except json.JSONDecodeError:
                continue
    return None


def _tools_from_json(obj: dict | list) -> list[str]:
    """Extract tool names from a parsed JSON structure."""
    if isinstance(obj, list):
        return [str(v).strip() for v in obj if isinstance(v, str) and v.strip()]

    if isinstance(obj, dict):
        # {"tool": "fastp"}
        if "tool" in obj and isinstance(obj["tool"], str):
            return [obj["tool"].strip()]

        # {"tools": {...}} or {"tools": [...]}
        if "tools" in obj:
            inner = obj["tools"]
            if isinstance(inner, dict):
                # {"tools": {"step": "tool_name", ...}}
                return [str(v).strip() for v in inner.values() if isinstance(v, str)]
            if isinstance(inner, list):
                return [str(v).strip() for v in inner if isinstance(v, str)]

        # {"adapter_trimming": "fastp", "alignment": "STAR"}  (step→tool map at root)
        values = [v for v in obj.values() if isinstance(v, str)]
        if values and all("/" not in v for v in values):
            return [v.strip() for v in values]

    return []


def _extract_tool_names_heuristic(text: str) -> list[str]:
    """Last-resort: extract capitalized identifiers that look like tool names."""
    # Match tokens like STAR, fastp, BWA-MEM2, DeepVariant, kallisto
    candidates = re.findall(r"\b([A-Za-z][A-Za-z0-9_\-\.]+)\b", text)
    # Filter noise words
    stop = {
        "the", "a", "an", "is", "are", "for", "to", "in", "of", "and", "or",
        "with", "use", "using", "would", "should", "best", "tool", "tools",
        "step", "domain", "analysis", "workflow", "you", "I", "we", "my",
    }
    seen: list[str] = []
    seen_lower: set[str] = set()
    for tok in candidates:
        if tok.lower() in stop:
            continue
        if tok.lower() not in seen_lower:
            seen.append(tok)
            seen_lower.add(tok.lower())
    return seen[:10]  # cap to avoid noise
