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


class Fastp_trim(_Base):
    """Adapter trimming and quality filtering via fastp.

    Supports single-end (r1 only) and paired-end (r1 + r2) reads.
    Use extra_args for any additional fastp flags not listed above.

    Example extra_args:
        --cut_front --cut_tail --cut_window_size 4 --cut_mean_quality 20
        --max_len1 150 --trim_poly_x
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Fastp_trim",
            display_name="fastp trim",
            category="Transcriptomics/QC",
            inputs=[
                # ── 입력 파일 ──────────────────────────────────────────
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
                # ── 주요 파라미터 ───────────────────────────────────────
                io.Int.Input("thread",
                    display_name="Threads",
                    default=4, min=1, max=32),
                io.Int.Input("quality_phred",
                    display_name="Min quality (Phred)",
                    default=20, min=0, max=40,
                    tooltip="Minimum base quality score (--qualified_quality_phred)"),
                io.Int.Input("length_required",
                    display_name="Min read length",
                    default=50, min=0, max=1000,
                    tooltip="Reads shorter than this after trimming are discarded"),
                io.Boolean.Input("detect_adapter_for_pe",
                    display_name="Auto-detect adapter (PE)",
                    default=True,
                    tooltip="Automatically detect adapters for paired-end reads"),
                io.String.Input("adapter_sequence",
                    display_name="Adapter R1 (optional)",
                    multiline=False, default="",
                    tooltip="Adapter sequence for R1. Leave empty for auto-detection."),
                io.String.Input("adapter_sequence_r2",
                    display_name="Adapter R2 (optional)",
                    multiline=False, default="",
                    tooltip="Adapter sequence for R2. Leave empty for auto-detection."),
                # ── 고급 옵션 ───────────────────────────────────────────
                io.String.Input("extra_args",
                    display_name="Extra fastp arguments",
                    multiline=True, default="",
                    tooltip="Additional fastp flags, e.g. --cut_front --trim_poly_x"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("r1_trimmed"),
                io.String.Output("r2_trimmed"),
                io.String.Output("summary_text"),
                io.String.Output("stats_json"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, output_dir, thread,
        quality_phred, length_required, detect_adapter_for_pe,
        adapter_sequence, adapter_sequence_r2, extra_args,
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
            "--thread", str(thread),
            "--qualified_quality_phred", str(quality_phred),
            "--length_required", str(length_required),
        ]
        if paired:
            cmd += ["--in2", r2_path, "--out2", r2_out]
            if detect_adapter_for_pe:
                cmd.append("--detect_adapter_for_pe")
        if adapter_sequence:
            cmd += ["--adapter_sequence", adapter_sequence]
        if adapter_sequence_r2 and paired:
            cmd += ["--adapter_sequence_r2", adapter_sequence_r2]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), r1_out, r2_out,
                                 f"ERROR:\n{err}", "{}")

        stats = json.loads(Path(json_out).read_text())
        summary = _fastp_summary(stats, paired)
        return io.NodeOutput(str(out_dir), r1_out, r2_out, summary, json.dumps(stats))


def _fastp_summary(stats: dict, paired: bool) -> str:
    bf = stats.get("summary", {}).get("before_filtering", {})
    af = stats.get("summary", {}).get("after_filtering", {})
    total_in  = bf.get("total_reads", 0)
    total_out = af.get("total_reads", 0)
    pass_rate = (total_out / total_in * 100) if total_in else 0
    lines = [
        "=== fastp QC Summary ===",
        f"Mode           : {'Paired-end' if paired else 'Single-end'}",
        f"Input reads    : {total_in:,}",
        f"Output reads   : {total_out:,}  ({pass_rate:.1f}% pass)",
        f"Q20 rate (in)  : {bf.get('q20_rate', 0)*100:.1f}%",
        f"Q30 rate (in)  : {bf.get('q30_rate', 0)*100:.1f}%",
        f"Q20 rate (out) : {af.get('q20_rate', 0)*100:.1f}%",
        f"Q30 rate (out) : {af.get('q30_rate', 0)*100:.1f}%",
        f"GC content     : {af.get('gc_content', 0)*100:.1f}%",
    ]
    return "\n".join(lines)
