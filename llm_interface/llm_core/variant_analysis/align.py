from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path


def run_bwa_mem2(
    r1_path: str,
    r2_path: str | None = None,
    reference_fa: str = "",
    output_dir: str = "",
    threads: int = 4,
    read_group: str = "@RG\tID:sample\tSM:sample\tPL:ILLUMINA",
    mark_duplicates: bool = True,
    extra_args: str = "",
) -> tuple[str, str]:
    """Align reads with BWA-MEM2, sort, index, and optionally mark duplicates.

    Returns (bam_path, flagstat_text).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)

    sorted_bam = str(out_dir / "aligned.sorted.bam")
    final_bam = str(out_dir / "aligned.markdup.bam") if mark_duplicates else sorted_bam

    bwa_cmd = ["bwa-mem2", "mem", "-t", str(threads), "-R", read_group]
    if extra_args.strip():
        bwa_cmd += shlex.split(extra_args)
    bwa_cmd += [reference_fa, r1_path]
    if r2_path:
        bwa_cmd.append(r2_path)

    sort_cmd = ["samtools", "sort", "-@", str(threads), "-o", sorted_bam]

    bwa_proc = subprocess.Popen(bwa_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sort_result = subprocess.run(sort_cmd, stdin=bwa_proc.stdout, capture_output=True, text=True)
    _, bwa_stderr = bwa_proc.communicate()

    if bwa_proc.returncode != 0:
        raise RuntimeError(f"bwa-mem2 failed: {bwa_stderr.decode()[:300]}")
    if sort_result.returncode != 0:
        raise RuntimeError(f"samtools sort failed: {sort_result.stderr[:300]}")

    if mark_duplicates:
        tmp = str(out_dir / "aligned.sorted.tmp.bam")
        os.rename(sorted_bam, tmp)
        r = subprocess.run(
            ["samtools", "markdup", "-@", str(threads), tmp, final_bam],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"samtools markdup failed: {r.stderr[:300]}")
        os.remove(tmp)

    subprocess.run(["samtools", "index", final_bam], check=True)

    flagstat = subprocess.run(
        ["samtools", "flagstat", final_bam],
        capture_output=True, text=True, check=True,
    )
    return final_bam, flagstat.stdout


def run_bowtie2(
    r1_path: str,
    r2_path: str | None = None,
    index_prefix: str = "",
    output_dir: str = "",
    threads: int = 4,
    preset: str = "sensitive-local",
    extra_args: str = "",
) -> tuple[str, str]:
    """Align reads with Bowtie2 and sort the output.

    Returns (bam_path, alignment_summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_bam = str(out_dir / "bowtie2.sorted.bam")

    bt2_cmd = ["bowtie2", "-x", index_prefix, "-p", str(threads), f"--{preset}"]
    if r2_path:
        bt2_cmd += ["-1", r1_path, "-2", r2_path]
    else:
        bt2_cmd += ["-U", r1_path]
    if extra_args.strip():
        bt2_cmd += shlex.split(extra_args)

    sort_cmd = ["samtools", "sort", "-@", str(threads), "-o", sorted_bam]

    bt2_proc = subprocess.Popen(bt2_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sort_result = subprocess.run(sort_cmd, stdin=bt2_proc.stdout, capture_output=True, text=True)
    _, bt2_stderr = bt2_proc.communicate()

    if bt2_proc.returncode != 0:
        raise RuntimeError(f"bowtie2 failed: {bt2_stderr.decode()[:300]}")
    if sort_result.returncode != 0:
        raise RuntimeError(f"samtools sort failed: {sort_result.stderr[:300]}")

    subprocess.run(["samtools", "index", sorted_bam], check=True)
    return sorted_bam, bt2_stderr.decode(errors="replace")
