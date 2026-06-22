from __future__ import annotations


def run_kallisto_quant(
    r1_path: str,
    index_path: str,
    output_dir: str | None = None,
    single_end: bool = True,
    fragment_length: float = 200.0,
    sd: float = 20.0,
    threads: int = 4,
) -> str:
    raise NotImplementedError


def run_star_align(
    r1_path: str,
    genome_dir: str,
    output_dir: str | None = None,
    r2_path: str | None = None,
    threads: int = 4,
) -> str:
    raise NotImplementedError
