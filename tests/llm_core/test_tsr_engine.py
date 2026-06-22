import pytest
from llm_core.tsr.schema import DomainTSR, StepRule, ToolChoice, ToolValidity
from llm_core.tsr.engine import TSREngine


@pytest.fixture
def rna_tsr():
    return DomainTSR(
        domain_id="transcriptomics",
        description="test",
        steps=[
            StepRule(
                step_id="alignment",
                step_name="Genome Alignment",
                condition="data_type == 'short_read' and read_length >= 75",
                tools=[
                    ToolChoice("STAR", ToolValidity.CANONICAL, "splice-aware"),
                    ToolChoice("HISAT2", ToolValidity.ALTERNATIVE_VALID, "memory efficient"),
                    ToolChoice("minimap2", ToolValidity.INVALID, "long-read only"),
                ],
            ),
            StepRule(
                step_id="alignment",
                step_name="Genome Alignment",
                condition="data_type == 'long_read'",
                tools=[
                    ToolChoice("minimap2", ToolValidity.CANONICAL, "long-read specialist"),
                    ToolChoice("STAR", ToolValidity.INVALID, "short-read only"),
                ],
            ),
            StepRule(
                step_id="de_analysis",
                step_name="Differential Expression",
                condition="n_samples_per_group < 6",
                tools=[
                    ToolChoice("edgeR", ToolValidity.CANONICAL, "small sample"),
                    ToolChoice("DESeq2", ToolValidity.ALTERNATIVE_VALID, "general"),
                ],
            ),
            StepRule(
                step_id="de_analysis",
                step_name="Differential Expression",
                condition="n_samples_per_group >= 6",
                tools=[
                    ToolChoice("DESeq2", ToolValidity.CANONICAL, "large sample"),
                    ToolChoice("edgeR", ToolValidity.ALTERNATIVE_VALID, "general"),
                    ToolChoice("limma_voom", ToolValidity.ALTERNATIVE_VALID, "large study"),
                ],
            ),
        ],
    )


def test_canonical_short_read(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.canonical("alignment", ctx) == "STAR"


def test_canonical_long_read(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "long_read"}
    assert engine.canonical("alignment", ctx) == "minimap2"


def test_is_valid_invalid_tool(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.is_valid("alignment", "minimap2", ctx) == ToolValidity.INVALID


def test_is_valid_alternative(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.is_valid("alignment", "HISAT2", ctx) == ToolValidity.ALTERNATIVE_VALID


def test_canonical_de_small_sample(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"n_samples_per_group": 3}
    assert engine.canonical("de_analysis", ctx) == "edgeR"


def test_canonical_de_large_sample(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"n_samples_per_group": 8}
    assert engine.canonical("de_analysis", ctx) == "DESeq2"


def test_unknown_step_returns_none(rna_tsr):
    engine = TSREngine(rna_tsr)
    assert engine.canonical("nonexistent_step", {}) is None


def test_unknown_tool_returns_invalid(rna_tsr):
    engine = TSREngine(rna_tsr)
    ctx = {"data_type": "short_read", "read_length": 150}
    assert engine.is_valid("alignment", "bowtie2", ctx) == ToolValidity.INVALID
