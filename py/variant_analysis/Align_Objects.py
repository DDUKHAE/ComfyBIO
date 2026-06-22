from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class BWA_mem2(_Base):
    """Short-read alignment with BWA-MEM2.

    Requires a BWA-MEM2 index (bwa-mem2 index reference.fa).
    Outputs a sorted, indexed BAM file. Optionally marks PCR duplicates.

    Example extra_args:
        -Y -K 100000000 -v 3
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BWA_mem2",
            display_name="BWA-MEM2 align",
            category="VariantAnalysis/Alignment",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default="",
                    tooltip="Read 1 FASTQ path (.fastq / .fastq.gz)"),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default="",
                    tooltip="Read 2 path. Leave empty for single-end."),
                io.String.Input("reference_fa",
                    display_name="Reference FASTA",
                    multiline=False, default="",
                    tooltip="Path to reference genome FASTA (must be indexed with bwa-mem2 index)"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.String.Input("read_group",
                    display_name="Read group header",
                    multiline=False,
                    default="@RG\tID:sample\tSM:sample\tPL:ILLUMINA",
                    tooltip="SAM read group string (required for GATK)"),
                io.Boolean.Input("mark_duplicates",
                    display_name="Mark duplicates",
                    default=True,
                    tooltip="Run samtools markdup after alignment"),
                io.String.Input("extra_args",
                    display_name="Extra BWA-MEM2 arguments",
                    multiline=True, default="",
                    tooltip="Additional bwa-mem2 mem flags, e.g. -Y -K 100000000"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("bam_path"),
                io.String.Output("bai_path"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, reference_fa, output_dir, threads,
        read_group, mark_duplicates, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())
        sorted_bam = str(out_dir / "aligned.sorted.bam")
        final_bam = str(out_dir / "aligned.markdup.bam") if mark_duplicates else sorted_bam

        # bwa-mem2 mem | samtools sort
        bwa_cmd = [
            "bwa-mem2", "mem",
            "-t", str(threads),
            "-R", read_group,
        ]
        if extra_args.strip():
            bwa_cmd += shlex.split(extra_args)
        bwa_cmd += [reference_fa, r1_path]
        if paired:
            bwa_cmd.append(r2_path)

        sort_cmd = ["samtools", "sort", "-@", str(threads), "-o", sorted_bam]

        bwa_proc = subprocess.Popen(bwa_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sort_result = subprocess.run(sort_cmd, stdin=bwa_proc.stdout,
                                     capture_output=True, text=True)
        bwa_proc.wait()

        if bwa_proc.returncode != 0 or sort_result.returncode != 0:
            err = bwa_proc.stderr.read().decode(errors="replace")[:300]
            return io.NodeOutput(str(out_dir), sorted_bam, "", f"ERROR:\n{err}")

        if mark_duplicates:
            tmp_bam = str(out_dir / "aligned.sorted.tmp.bam")
            import os
            os.rename(sorted_bam, tmp_bam)
            markdup_result = subprocess.run(
                ["samtools", "markdup", "-@", str(threads), tmp_bam, final_bam],
                capture_output=True, text=True,
            )
            if markdup_result.returncode != 0:
                return io.NodeOutput(str(out_dir), tmp_bam, "",
                                     f"markdup ERROR:\n{markdup_result.stderr[:300]}")
            os.remove(tmp_bam)

        index_result = subprocess.run(
            ["samtools", "index", final_bam],
            capture_output=True, text=True,
        )
        bai_path = final_bam + ".bai"

        flagstat = subprocess.run(
            ["samtools", "flagstat", final_bam],
            capture_output=True, text=True,
        )
        summary = _flagstat_summary(flagstat.stdout, mark_duplicates)
        return io.NodeOutput(str(out_dir), final_bam, bai_path, summary)


class Bowtie2_align(_Base):
    """Short-read alignment with Bowtie2.

    Requires a Bowtie2 index (bowtie2-build reference.fa index_prefix).
    Outputs a coordinate-sorted BAM file.

    Example extra_args:
        --no-mixed --no-discordant --dovetail
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Bowtie2_align",
            display_name="Bowtie2 align",
            category="VariantAnalysis/Alignment",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default=""),
                io.String.Input("index_prefix",
                    display_name="Bowtie2 index prefix",
                    multiline=False, default="",
                    tooltip="Path prefix of Bowtie2 index (without .bt2 extension)"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Combo.Input("preset",
                    display_name="Alignment preset",
                    options=["sensitive-local", "sensitive", "very-sensitive", "very-sensitive-local"],
                    default="sensitive-local"),
                io.String.Input("extra_args",
                    display_name="Extra Bowtie2 arguments",
                    multiline=True, default="",
                    tooltip="Additional bowtie2 flags"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("bam_path"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, index_prefix, output_dir, threads, preset, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())
        sorted_bam = str(out_dir / "bowtie2.sorted.bam")

        bt2_cmd = [
            "bowtie2",
            "-x", index_prefix,
            "-p", str(threads),
            f"--{preset}",
        ]
        if paired:
            bt2_cmd += ["-1", r1_path, "-2", r2_path]
        else:
            bt2_cmd += ["-U", r1_path]
        if extra_args.strip():
            bt2_cmd += shlex.split(extra_args)

        sort_cmd = ["samtools", "sort", "-@", str(threads), "-o", sorted_bam]

        bt2_proc = subprocess.Popen(bt2_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sort_result = subprocess.run(sort_cmd, stdin=bt2_proc.stdout,
                                     capture_output=True, text=True)
        _, bt2_stderr = bt2_proc.communicate()
        bt2_proc.wait()

        if bt2_proc.returncode != 0 or sort_result.returncode != 0:
            err = bt2_stderr.decode(errors="replace")[:300]
            return io.NodeOutput(str(out_dir), sorted_bam, f"ERROR:\n{err}")

        subprocess.run(["samtools", "index", sorted_bam], capture_output=True)

        summary = _bowtie2_summary(bt2_stderr.decode(errors="replace"), preset, paired)
        return io.NodeOutput(str(out_dir), sorted_bam, summary)


# ── 요약 헬퍼 ───────────────────────────────────────────────────────────────

def _flagstat_summary(flagstat_text: str, mark_dup: bool) -> str:
    lines = ["=== BWA-MEM2 Alignment Summary ==="]
    if mark_dup:
        lines.append("  (duplicates marked)")
    for line in flagstat_text.splitlines():
        for kw in ["in total", "mapped (", "properly paired", "duplicates"]:
            if kw in line:
                lines.append("  " + line.strip())
                break
    return "\n".join(lines)


def _bowtie2_summary(stderr_text: str, preset: str, paired: bool) -> str:
    lines = [
        "=== Bowtie2 Alignment Summary ===",
        f"  Preset   : {preset}",
        f"  Mode     : {'Paired-end' if paired else 'Single-end'}",
    ]
    for line in stderr_text.splitlines():
        line = line.strip()
        if any(kw in line for kw in ["reads;", "aligned", "overall alignment"]):
            lines.append("  " + line)
    return "\n".join(lines)
