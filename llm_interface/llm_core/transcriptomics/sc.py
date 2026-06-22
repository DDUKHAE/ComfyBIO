from __future__ import annotations


def run_sc_preprocess(
    input_path: str,
    min_genes: int = 200,
    min_cells: int = 3,
    n_top_genes: int = 2000,
    output_path: str | None = None,
) -> str:
    raise NotImplementedError


def run_sc_cluster(
    input_path: str,
    resolution: float = 0.5,
    algorithm: str = "leiden",
    output_path: str | None = None,
) -> str:
    raise NotImplementedError


def run_sc_annotate(
    input_path: str,
    marker_genes: dict[str, list[str]],
    output_path: str | None = None,
) -> str:
    raise NotImplementedError
