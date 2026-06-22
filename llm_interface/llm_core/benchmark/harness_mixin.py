"""HarnessMixin — wires harness runner into any DomainPlugin.

Concrete plugins inherit DomainPlugin + HarnessMixin to get a working
run_workflow() that drives the full harness loop:

    prompt_builder → LLM adapter → response_parser → return tools

Usage in a plugin:
    class CS2TranscriptomicsPlugin(DomainPlugin, HarnessMixin):
        _default_provider = "claude"
        _default_model = None
        ...
"""
from __future__ import annotations

import asyncio

from .query_schema import HeldOutQuery


class HarnessMixin:
    """Provides run_workflow() via the harness runner for DomainPlugin subclasses."""

    _default_provider: str = "claude"
    _default_model: str | None = None

    def run_workflow(self, query: HeldOutQuery) -> dict:
        """Run a query through the LLM harness and return tool selections.

        Calls harness.runner.run_query() synchronously (blocking).
        Override this for domains with actual executable pipelines.
        """
        from llm_core.harness.runner import run_query

        result = asyncio.get_event_loop().run_until_complete(
            run_query(
                plugin=self,          # type: ignore[arg-type]
                query=query,
                provider=self._default_provider,
                model=self._default_model,
            )
        )
        return {
            "tools": result.generated_tools,
            "output": {},
            "verdict": result.verdict,
            "error": result.error,
        }
