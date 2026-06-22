from __future__ import annotations


def run_deseq2(
    counts_path: str,
    metadata_path: str,
    condition_col: str = "condition",
    reference_level: str = "control",
    output_path: str | None = None,
) -> str:
    raise NotImplementedError
