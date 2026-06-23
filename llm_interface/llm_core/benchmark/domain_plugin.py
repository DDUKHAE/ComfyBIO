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
from pathlib import Path

import yaml

from llm_core.gold.schema import TieredGold
from llm_core.tsr.schema import DomainTSR

from .query_schema import Difficulty, HeldOutQuery, ToolSpecificity

_GOLD_ROOT = Path(__file__).resolve().parent.parent / "gold" / "domains"


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

    def gold_dir(self) -> Path:
        """Return the directory containing this domain's gold YAML files."""
        return _GOLD_ROOT / self.domain_id

    def load_query(self, query_id: str) -> HeldOutQuery:
        """Load a HeldOutQuery from the combined gold+query YAML file."""
        path = self.gold_dir() / f"{query_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"No query file for '{query_id}': {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return HeldOutQuery(
            query_id=data["query_id"],
            domain_id=self.domain_id,
            family=data["family"],
            nl_text=data.get("nl_text", ""),
            difficulty=Difficulty(data.get("difficulty", "medium")),
            tool_specificity=ToolSpecificity(
                data.get("tool_specificity", "goal_specified")
            ),
            context=data.get("context", {}),
            fixture_path=data.get("fixture_path", ""),
            adversarial_hint_tool=data.get("adversarial_hint_tool"),
        )

    def list_query_ids(self) -> list[str]:
        """Return all query IDs available in the gold directory."""
        d = self.gold_dir()
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.yaml"))

    def run_workflow(self, query: HeldOutQuery) -> dict:
        """Execute the workflow for a query and return tools + output metrics.

        Override in concrete plugins where execution is possible.
        Default: NotImplementedError (harness will skip output checks).
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement run_workflow(). "
            "Tool-selection evaluation still works via the LLM response parser."
        )
