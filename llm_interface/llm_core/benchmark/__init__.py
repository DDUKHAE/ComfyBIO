"""benchmark — domain plugin registry for ComfyBIO evaluation harness.

All case-study plugins are registered here. Import the registry
to look up a plugin by domain_id without knowing the class name.

Usage:
    from llm_core.benchmark import get_plugin, list_domain_ids

    plugin = get_plugin("transcriptomics")
    report = await run_domain(plugin, queries, provider="claude")
"""
from __future__ import annotations

from .cs2_transcriptomics_plugin import CS2TranscriptomicsPlugin
from .cs3_variant_analysis_plugin import CS3VariantAnalysisPlugin
from .cs4_epigenomics_plugin import CS4EpigenomicsPlugin
from .cs5_metagenomics_plugin import CS5MetagenomicsPlugin
from .cs6_genome_assembly_plugin import CS6GenomeAssemblyPlugin
from .domain_plugin import DomainPlugin
from .harness_mixin import HarnessMixin
from .query_schema import Difficulty, HeldOutQuery, ToolSpecificity

# Registry: domain_id → plugin instance
_REGISTRY: dict[str, DomainPlugin] = {
    "transcriptomics": CS2TranscriptomicsPlugin(),
    "variant_analysis": CS3VariantAnalysisPlugin(),
    "epigenomics": CS4EpigenomicsPlugin(),
    "metagenomics": CS5MetagenomicsPlugin(),
    "genome_assembly": CS6GenomeAssemblyPlugin(),
}


def get_plugin(domain_id: str) -> DomainPlugin:
    """Return the plugin for a domain. Raises KeyError if not found."""
    if domain_id not in _REGISTRY:
        raise KeyError(
            f"Unknown domain '{domain_id}'. "
            f"Available: {list(_REGISTRY)}"
        )
    return _REGISTRY[domain_id]


def list_domain_ids() -> list[str]:
    """Return all registered domain IDs."""
    return list(_REGISTRY)


__all__ = [
    "DomainPlugin",
    "HarnessMixin",
    "HeldOutQuery",
    "ToolSpecificity",
    "Difficulty",
    "get_plugin",
    "list_domain_ids",
    "CS2TranscriptomicsPlugin",
    "CS3VariantAnalysisPlugin",
    "CS4EpigenomicsPlugin",
    "CS5MetagenomicsPlugin",
    "CS6GenomeAssemblyPlugin",
]
