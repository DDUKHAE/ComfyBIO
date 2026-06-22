from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path


def run_gatk_haplotype_caller(
    bam_path: str,
    reference_fa: str,
    output_dir: str,
    sample_name: str = "sample",
    emit_ref_confidence: str = "NONE",
    ploidy: int = 2,
    extra_args: str = "",
) -> tuple[str, str]:
    """Run GATK HaplotypeCaller for germline variant calling.

    Returns (vcf_path, stats_summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)

    ext = ".g.vcf.gz" if emit_ref_confidence == "GVCF" else ".vcf.gz"
    vcf_path = str(out_dir / f"{sample_name}{ext}")

    cmd = [
        "gatk", "HaplotypeCaller",
        "-R", reference_fa,
        "-I", bam_path,
        "-O", vcf_path,
        "--sample-name", sample_name,
        "--ploidy", str(ploidy),
        "-ERC", emit_ref_confidence,
    ]
    if extra_args.strip():
        cmd += shlex.split(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"GATK HaplotypeCaller failed: {result.stderr[:400]}")

    stats = subprocess.run(
        ["bcftools", "stats", vcf_path], capture_output=True, text=True,
    )
    return vcf_path, stats.stdout


def run_bcftools_call(
    bam_path: str,
    reference_fa: str,
    output_dir: str,
    caller: str = "multiallelic",
    min_base_quality: int = 20,
    min_mapping_quality: int = 20,
    extra_args: str = "",
) -> tuple[str, str]:
    """Run bcftools mpileup + call variant calling.

    Returns (vcf_path, stats_summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    vcf_path = str(out_dir / "bcftools.vcf.gz")

    mpileup_cmd = [
        "bcftools", "mpileup",
        "-f", reference_fa,
        "-Q", str(min_base_quality),
        "-q", str(min_mapping_quality),
        "--output-type", "u",
    ]
    if extra_args.strip():
        mpileup_cmd += shlex.split(extra_args)
    mpileup_cmd.append(bam_path)

    caller_flag = "-m" if caller == "multiallelic" else "-c"
    call_cmd = [
        "bcftools", "call", caller_flag,
        "--variants-only",
        "--output-type", "z",
        "--output", vcf_path,
    ]

    mp_proc = subprocess.Popen(mpileup_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    call_result = subprocess.run(call_cmd, stdin=mp_proc.stdout, capture_output=True, text=True)
    mp_proc.wait()

    if mp_proc.returncode != 0 or call_result.returncode != 0:
        raise RuntimeError(f"bcftools call failed: {call_result.stderr[:300]}")

    subprocess.run(["bcftools", "index", vcf_path], check=True)

    stats = subprocess.run(
        ["bcftools", "stats", vcf_path], capture_output=True, text=True,
    )
    return vcf_path, stats.stdout
