from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path


def run_bcftools_filter(
    vcf_path: str,
    output_dir: str,
    include_expr: str = "QUAL>=30 && DP>=10",
    extra_args: str = "",
) -> tuple[str, int, str]:
    """Hard-filter VCF with a bcftools include expression.

    Returns (filtered_vcf, n_variants, summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    filtered_vcf = str(out_dir / "filtered.vcf.gz")

    cmd = [
        "bcftools", "filter",
        "--include", include_expr,
        "--output-type", "z",
        "--output", filtered_vcf,
    ]
    if extra_args.strip():
        cmd += shlex.split(extra_args)
    cmd.append(vcf_path)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"bcftools filter failed: {result.stderr[:300]}")

    subprocess.run(["bcftools", "index", filtered_vcf], check=True)

    count = subprocess.run(
        ["bcftools", "view", "--no-header", "-c", "1", filtered_vcf],
        capture_output=True, text=True,
    )
    n_variants = count.stdout.count("\n")

    summary = "\n".join([
        "=== bcftools filter Summary ===",
        f"  Filter expression : {include_expr}",
        f"  Variants passing  : {n_variants:,}",
    ])
    return filtered_vcf, n_variants, summary


def run_vep(
    vcf_path: str,
    output_dir: str,
    species: str = "homo_sapiens",
    assembly: str = "GRCh38",
    cache_dir: str = "",
    extra_args: str = "",
) -> tuple[str, str]:
    """Annotate variants with Ensembl VEP (offline cache mode).

    Returns (annotated_vcf, summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    annotated_vcf = str(out_dir / "vep_annotated.vcf.gz")
    stats_file = str(out_dir / "vep_stats.txt")

    cmd = [
        "vep",
        "--input_file", vcf_path,
        "--output_file", annotated_vcf,
        "--vcf", "--compress_output", "bgzip",
        "--species", species,
        "--assembly", assembly,
        "--cache", "--offline",
        "--stats_file", stats_file,
        "--fork", "4",
    ]
    if cache_dir and cache_dir.strip():
        cmd += ["--dir_cache", cache_dir]
    if extra_args.strip():
        cmd += shlex.split(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"VEP failed: {result.stderr[:400]}")

    lines = [
        "=== VEP Annotation Summary ===",
        f"  Species  : {species}",
        f"  Assembly : {assembly}",
    ]
    stats_p = Path(stats_file)
    if stats_p.exists():
        for line in stats_p.read_text().splitlines():
            if "Variants processed" in line or "Variants remaining" in line:
                lines.append("  " + line.strip())

    return annotated_vcf, "\n".join(lines)
