import pytest


def test_transcriptomics_package_importable():
    from llm_core.transcriptomics import de, sc, qc, align
    assert de is not None
    assert sc is not None
    assert qc is not None
    assert align is not None


def test_fixtures_exist():
    from pathlib import Path
    base = Path("/home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/fixtures/transcriptomics")
    assert (base / "counts_small.tsv").exists()
    assert (base / "metadata.tsv").exists()
    assert (base / "reads_R1.fastq").exists()
