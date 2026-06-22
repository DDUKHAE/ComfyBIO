from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def run_kallisto_quant(
    r1_path: str,
    index_path: str,
    output_dir: str | None = None,
    single_end: bool = True,
    fragment_length: float = 200.0,
    sd: float = 20.0,
    threads: int = 4,
) -> str:
    out_dir = str(output_dir or tempfile.mkdtemp())
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    cmd = [
        "kallisto", "quant",
        "--index", index_path,
        "--output-dir", out_dir,
        "--threads", str(threads),
    ]
    if single_end:
        cmd += ["--single", "--fragment-length", str(fragment_length), "--sd", str(sd)]
    cmd.append(r1_path)

    subprocess.run(cmd, check=True, capture_output=True)
    return out_dir


def run_star_align(
    r1_path: str,
    genome_dir: str,
    output_dir: str | None = None,
    r2_path: str | None = None,
    threads: int = 4,
) -> str:
    out_dir = str(output_dir or tempfile.mkdtemp())
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    prefix = str(Path(out_dir)) + "/"

    cmd = [
        "STAR",
        "--runThreadN", str(threads),
        "--genomeDir", genome_dir,
        "--readFilesIn", r1_path,
        "--outFileNamePrefix", prefix,
        "--outSAMtype", "BAM", "SortedByCoordinate",
        "--outSAMattributes", "NH", "HI", "AS", "NM",
    ]
    if r2_path:
        cmd.append(r2_path)

    subprocess.run(cmd, check=True, capture_output=True)
    return out_dir
