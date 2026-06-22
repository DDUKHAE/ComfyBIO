from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def run_fastp(
    r1_path: str,
    r2_path: str | None = None,
    output_dir: str | None = None,
    thread: int = 4,
) -> dict:
    out_dir = Path(output_dir or tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)

    r1_out = str(out_dir / "R1_trimmed.fastq.gz")
    json_out = str(out_dir / "fastp.json")
    html_out = str(out_dir / "fastp.html")

    cmd = [
        "fastp",
        "--in1", r1_path,
        "--out1", r1_out,
        "--json", json_out,
        "--html", html_out,
        "--thread", str(thread),
        "--disable_adapter_trimming",  # safe default for synthetic reads
    ]
    if r2_path:
        r2_out = str(out_dir / "R2_trimmed.fastq.gz")
        cmd += ["--in2", r2_path, "--out2", r2_out]

    subprocess.run(cmd, check=True, capture_output=True)
    return json.loads(Path(json_out).read_text())
