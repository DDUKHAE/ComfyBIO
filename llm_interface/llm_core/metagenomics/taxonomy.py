from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path


def run_kraken2(
    r1_path: str,
    r2_path: str | None = None,
    db_path: str = "",
    output_dir: str = "",
    confidence: float = 0.0,
    threads: int = 4,
    extra_args: str = "",
) -> tuple[str, str, str]:
    """Classify reads with Kraken2.

    Returns (report_path, output_path, summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = str(out_dir / "kraken2_report.txt")
    output_path = str(out_dir / "kraken2_output.txt")

    cmd = [
        "kraken2",
        "--db", db_path,
        "--threads", str(threads),
        "--confidence", str(confidence),
        "--report", report_path,
        "--output", output_path,
    ]
    if r2_path:
        cmd += ["--paired", r1_path, r2_path]
    else:
        cmd.append(r1_path)
    if extra_args.strip():
        cmd += shlex.split(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"kraken2 failed:\n{result.stderr[:500]}")

    summary = _kraken2_summary(report_path, result.stderr)
    return report_path, output_path, summary


def run_metaphlan(
    r1_path: str,
    r2_path: str | None = None,
    output_dir: str = "",
    db_path: str = "",
    threads: int = 4,
    analysis_type: str = "rel_ab",
    extra_args: str = "",
) -> tuple[str, str, str]:
    """Profile taxonomy with MetaPhlAn4.

    Returns (profile_path, bowtie_path, summary).
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)

    profile_path = str(out_dir / "metaphlan_profile.txt")
    bowtie_path = str(out_dir / "metaphlan_bowtie2.bz2")

    input_reads = r1_path
    if r2_path:
        input_reads = f"{r1_path},{r2_path}"

    cmd = [
        "metaphlan",
        input_reads,
        "--input_type", "fastq",
        "--nproc", str(threads),
        "--analysis_type", analysis_type,
        "--output_file", profile_path,
        "--bowtie2out", bowtie_path,
    ]
    if db_path.strip():
        cmd += ["--index", db_path]
    if extra_args.strip():
        cmd += shlex.split(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"metaphlan failed:\n{result.stderr[:500]}")

    summary = _metaphlan_summary(profile_path)
    return profile_path, bowtie_path, summary


def _kraken2_summary(report_path: str, stderr: str) -> str:
    lines = ["=== Kraken2 Summary ==="]
    for line in stderr.splitlines():
        if "classified" in line.lower() or "sequences" in line.lower():
            lines.append("  " + line.strip())
    p = Path(report_path)
    if p.exists():
        species_rows = []
        for row in p.read_text().splitlines():
            parts = row.split("\t")
            if len(parts) >= 6 and parts[3].strip() == "S":
                try:
                    species_rows.append((int(parts[1]), parts[5].strip()))
                except ValueError:
                    pass
        lines.append("Top 5 species:")
        for count, name in sorted(species_rows, reverse=True)[:5]:
            lines.append(f"  {name}: {count:,} reads")
    return "\n".join(lines)


def _metaphlan_summary(profile_path: str) -> str:
    lines = ["=== MetaPhlAn4 Summary ==="]
    p = Path(profile_path)
    if not p.exists():
        return "\n".join(lines + ["  Profile not found."])
    species = []
    for row in p.read_text().splitlines():
        if row.startswith("#") or not row.strip():
            continue
        parts = row.split("\t")
        if len(parts) >= 2 and "|s__" in parts[0] and "|t__" not in parts[0]:
            try:
                species.append((float(parts[1]), parts[0].split("|s__")[-1]))
            except ValueError:
                pass
    lines.append(f"Species detected: {len(species)}")
    for abund, name in sorted(species, reverse=True)[:5]:
        lines.append(f"  {name}: {abund:.2f}%")
    return "\n".join(lines)
