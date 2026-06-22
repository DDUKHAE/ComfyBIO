from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path


def run_humann3(
    r1_path: str,
    r2_path: str | None = None,
    metaphlan_profile: str = "",
    output_dir: str = "",
    threads: int = 4,
    nucleotide_db: str = "",
    protein_db: str = "",
    extra_args: str = "",
) -> tuple[str, str, str, str]:
    """Run HUMAnN3 functional profiling.

    Returns (genefamilies_path, pathabundance_path, pathcoverage_path, summary).
    Merges paired reads via cat before running HUMAnN3.
    """
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = r1_path
    if r2_path:
        merged = str(out_dir / "merged_reads.fastq.gz")
        with open(merged, "wb") as fout:
            for src in (r1_path, r2_path):
                with open(src, "rb") as fin:
                    fout.write(fin.read())
        input_path = merged

    genefamilies = str(out_dir / "humann_genefamilies.tsv")
    pathabundance = str(out_dir / "humann_pathabundance.tsv")
    pathcoverage = str(out_dir / "humann_pathcoverage.tsv")

    cmd = [
        "humann",
        "--input", input_path,
        "--output", str(out_dir),
        "--threads", str(threads),
    ]
    if metaphlan_profile.strip():
        cmd += ["--taxonomic-profile", metaphlan_profile]
    if nucleotide_db.strip():
        cmd += ["--nucleotide-database", nucleotide_db]
    if protein_db.strip():
        cmd += ["--protein-database", protein_db]
    if extra_args.strip():
        cmd += shlex.split(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"humann failed:\n{result.stderr[:500]}")

    summary = _humann3_summary(pathabundance, genefamilies)
    return genefamilies, pathabundance, pathcoverage, summary


def _humann3_summary(pathabundance: str, genefamilies: str) -> str:
    lines = ["=== HUMAnN3 Summary ==="]
    p_path = Path(pathabundance)
    g_path = Path(genefamilies)
    if p_path.exists():
        pathways = [
            l for l in p_path.read_text().splitlines()
            if l.strip() and not l.startswith("#") and "|" not in l
        ]
        n = len([p for p in pathways
                 if not p.startswith("UNMAPPED") and not p.startswith("UNINTEGRATED")])
        lines.append(f"Pathways detected : {n:,}")
    if g_path.exists():
        families = [
            l for l in g_path.read_text().splitlines()
            if l.strip() and not l.startswith("#") and "|" not in l
        ]
        n = len([f for f in families if not f.startswith("UNMAPPED")])
        lines.append(f"Gene families     : {n:,}")
    return "\n".join(lines)
