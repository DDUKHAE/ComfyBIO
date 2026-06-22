from __future__ import annotations

import json
import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Fastp_meta(_Base):
    """Adapter trimming and quality filtering for metagenomic reads via fastp.

    Supports single-end and paired-end reads. The --dedup flag removes
    exact duplicates common in metagenomic sequencing.

    Example extra_args:
        --cut_front --cut_tail --trim_poly_x --max_len1 150
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Fastp_meta",
            display_name="fastp meta trim",
            category="Metagenomics/QC",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default="",
                    tooltip="Read 1 FASTQ path (.fastq / .fastq.gz)"),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default="",
                    tooltip="Read 2 FASTQ path. Leave empty for single-end."),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default="",
                    tooltip="Output directory. Auto-created if empty."),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=32),
                io.Int.Input("quality_phred",
                    display_name="Min quality (Phred)",
                    default=20, min=0, max=40,
                    tooltip="Minimum base quality score"),
                io.Int.Input("length_required",
                    display_name="Min read length",
                    default=50, min=0, max=1000,
                    tooltip="Reads shorter than this after trimming are discarded"),
                io.Boolean.Input("dedup",
                    display_name="Remove duplicates",
                    default=True,
                    tooltip="Remove exact duplicate reads (--dedup)"),
                io.String.Input("extra_args",
                    display_name="Extra fastp arguments",
                    multiline=True, default="",
                    tooltip="Additional fastp flags"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("r1_trimmed"),
                io.String.Output("r2_trimmed"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, output_dir, threads,
        quality_phred, length_required, dedup, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())
        r1_out = str(out_dir / "R1_trimmed.fastq.gz")
        r2_out = str(out_dir / "R2_trimmed.fastq.gz") if paired else ""
        json_out = str(out_dir / "fastp.json")
        html_out = str(out_dir / "fastp.html")

        cmd = [
            "fastp",
            "--in1", r1_path,
            "--out1", r1_out,
            "--json", json_out,
            "--html", html_out,
            "--thread", str(threads),
            "--qualified_quality_phred", str(quality_phred),
            "--length_required", str(length_required),
        ]
        if paired:
            cmd += ["--in2", r2_path, "--out2", r2_out,
                    "--detect_adapter_for_pe"]
        if dedup:
            cmd.append("--dedup")
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), r1_out, r2_out,
                                 f"ERROR:\n{err}")

        try:
            stats = json.loads(Path(json_out).read_text())
            summary = _fastp_meta_summary(stats, paired, dedup)
        except Exception as e:
            summary = f"Completed (summary parse error: {e})"

        return io.NodeOutput(str(out_dir), r1_out, r2_out, summary)


class Kneaddata_qc(_Base):
    """Host contamination removal and QC with KneadData.

    Removes reads mapping to the host genome (e.g. human hg38),
    retaining clean metagenomic reads for downstream analysis.

    Example extra_args:
        --trimmomatic-options "SLIDINGWINDOW:4:20" --bypass-trf
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Kneaddata_qc",
            display_name="KneadData host remove",
            category="Metagenomics/QC",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default=""),
                io.String.Input("reference_db",
                    display_name="Host genome DB",
                    multiline=False, default="",
                    tooltip="Path to KneadData host genome database directory"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=32),
                io.String.Input("extra_args",
                    display_name="Extra KneadData arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("r1_clean"),
                io.String.Output("r2_clean"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, reference_db, output_dir, threads, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())

        cmd = [
            "kneaddata",
            "--input", r1_path,
            "--reference-db", reference_db,
            "--output", str(out_dir),
            "--threads", str(threads),
        ]
        if paired:
            cmd += ["--input", r2_path, "--paired"]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        r1_stem = Path(r1_path).stem.replace(".fastq", "")
        if paired:
            r1_clean = str(out_dir / f"{r1_stem}_kneaddata_paired_1.fastq")
            r2_clean = str(out_dir / f"{r1_stem}_kneaddata_paired_2.fastq")
        else:
            r1_clean = str(out_dir / f"{r1_stem}_kneaddata.fastq")
            r2_clean = ""

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), r1_clean, r2_clean,
                                 f"ERROR:\n{err}")

        summary = _kneaddata_summary(result.stderr, paired)
        return io.NodeOutput(str(out_dir), r1_clean, r2_clean, summary)


def _fastp_meta_summary(stats: dict, paired: bool, dedup: bool) -> str:
    bf = stats.get("summary", {}).get("before_filtering", {})
    af = stats.get("summary", {}).get("after_filtering", {})
    total_in = bf.get("total_reads", 0)
    total_out = af.get("total_reads", 0)
    pass_rate = (total_out / total_in * 100) if total_in else 0
    lines = [
        "=== fastp Meta QC Summary ===",
        f"Mode           : {'Paired-end' if paired else 'Single-end'}",
        f"Dedup          : {'on' if dedup else 'off'}",
        f"Input reads    : {total_in:,}",
        f"Output reads   : {total_out:,}  ({pass_rate:.1f}% pass)",
        f"Q20 rate (out) : {af.get('q20_rate', 0)*100:.1f}%",
        f"Q30 rate (out) : {af.get('q30_rate', 0)*100:.1f}%",
        f"GC content     : {af.get('gc_content', 0)*100:.1f}%",
    ]
    return "\n".join(lines)


def _kneaddata_summary(stderr: str, paired: bool) -> str:
    lines = ["=== KneadData Summary ===",
             f"Mode : {'Paired-end' if paired else 'Single-end'}"]
    for line in stderr.splitlines():
        if "reads" in line.lower() and any(
            kw in line.lower() for kw in ["final", "contaminated", "kept", "removed"]
        ):
            lines.append("  " + line.strip())
    if len(lines) == 2:
        lines.append("  (see kneaddata log for details)")
    return "\n".join(lines)
