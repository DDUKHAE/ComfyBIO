"""DomainPlugin ABC — interface each case study domain must implement.

The harness (llm_core.harness.runner) uses this interface to:
  1. Get the domain's TSR for prompt building          → get_tsr()
  2. List analysis families for query selection        → list_families()
  3. Load gold criteria for evaluation                 → load_gold(query_id)
  4. Run a workflow to get actual tool outputs         → run_workflow(query)

run_workflow() contract
-----------------------
Input : HeldOutQuery
Output: dict with two keys:
  "tools"  : list[str]   — tool names selected/executed by the workflow
  "output" : dict        — metric values used by GoldEvaluator
              (e.g. {"mapping_rate": 0.94, "n_sig_genes": 1200})

If the domain has no executable workflow, raise NotImplementedError.
The harness handles this gracefully by skipping output-criterion checks.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from llm_core.gold.schema import TieredGold
from llm_core.tsr.schema import DomainTSR

from .query_schema import HeldOutQuery


class DomainPlugin(ABC):

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """Unique domain identifier, e.g. 'transcriptomics'."""
        ...

    @property
    @abstractmethod
    def domain_description(self) -> str:
        """One-line description shown in benchmark reports."""
        ...

    @abstractmethod
    def get_tsr(self) -> DomainTSR:
        """Return the domain's Tool Selection Registry."""
        ...

    @abstractmethod
    def list_families(self) -> list[str]:
        """Return all workflow family IDs for this domain (12 per domain)."""
        ...

    @abstractmethod
    def load_gold(self, query_id: str) -> TieredGold:
        """Load tiered gold criteria for a specific query.

        Raises FileNotFoundError if gold YAML for query_id does not exist.
        """
        ...

    def run_workflow(self, query: HeldOutQuery) -> dict:
        """Execute the workflow for a query and return tools + output metrics.

        Override in concrete plugins where execution is possible.
        Default: NotImplementedError (harness will skip output checks).
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement run_workflow(). "
            "Tool-selection evaluation still works via the LLM response parser."
        )
