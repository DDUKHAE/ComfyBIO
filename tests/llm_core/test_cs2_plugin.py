from llm_core.benchmark.cs2_transcriptomics_plugin import CS2TranscriptomicsPlugin
from llm_core.benchmark.domain_plugin import DomainPlugin


def test_cs2_plugin_is_domain_plugin():
    plugin = CS2TranscriptomicsPlugin()
    assert isinstance(plugin, DomainPlugin)


def test_cs2_plugin_domain_id():
    plugin = CS2TranscriptomicsPlugin()
    assert plugin.domain_id == "transcriptomics"


def test_cs2_plugin_lists_12_families():
    plugin = CS2TranscriptomicsPlugin()
    families = plugin.list_families()
    assert len(families) == 12
    assert "differential_expression" in families
    assert "sc_clustering" in families


def test_cs2_plugin_get_tsr_resolves_de_canonical():
    from llm_core.tsr.engine import TSREngine
    plugin = CS2TranscriptomicsPlugin()
    tsr = plugin.get_tsr()
    engine = TSREngine(tsr)
    assert engine.canonical("differential_expression", {"n_samples_per_group": 8}) == "DESeq2"


def test_cs2_plugin_load_gold_de_analysis():
    from llm_core.gold.schema import TieredGold
    plugin = CS2TranscriptomicsPlugin()
    gold = plugin.load_gold("de_analysis_001")
    assert isinstance(gold, TieredGold)
    assert gold.family == "differential_expression"
    assert "DESeq2" in gold.canonical.tools or "edgeR" in gold.canonical.tools


def test_gold_evaluator_correct_canonical_de():
    from llm_core.gold.evaluator import GoldEvaluator
    from llm_core.gold.schema import Verdict
    plugin = CS2TranscriptomicsPlugin()
    gold = plugin.load_gold("de_analysis_001")
    evaluator = GoldEvaluator(gold)
    output = {"top10_overlap_min": 1.0, "has_log2fc_column": True, "has_padj_column": True}
    verdict = evaluator.evaluate(gold.canonical.tools, output)
    assert verdict == Verdict.CORRECT_CANONICAL
