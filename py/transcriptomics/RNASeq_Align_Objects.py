from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class STAR_align(_Base):
    """Splice-aware genome alignment with STAR.

    Requires a pre-built STAR genome index (star --runMode genomeGenerate).
    Outputs sorted BAM and alignment statistics.

    Example extra_args:
        --outFilterMultimapNmax 20 --alignSJoverhangMin 8
        --outSAMattributes NH HI AS NM MD
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="STAR_align",
            display_name="STAR align",
            category="Transcriptomics/Alignment",
            inputs=[
                # ── 입력 파일 ──────────────────────────────────────────
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default="",
                    tooltip="Read 1 FASTQ (.fastq / .fastq.gz)"),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default="",
                    tooltip="Read 2 path. Leave empty for single-end."),
                io.String.Input("genome_dir",
                    display_name="STAR genome index directory",
                    multiline=False, default="",
                    tooltip="Directory with STAR genome index files"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                # ── 주요 파라미터 ───────────────────────────────────────
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Combo.Input("out_sam_type",
                    display_name="Output BAM type",
                    options=["BAM SortedByCoordinate", "BAM Unsorted", "SAM"],
                    default="BAM SortedByCoordinate"),
                io.String.Input("read_files_command",
                    display_name="ReadFilesCommand (.gz → zcat)",
                    multiline=False, default="zcat",
                    tooltip="Command to decompress reads. Use 'zcat' for .gz, '-' for plain FASTQ"),
                io.Int.Input("out_filter_mismatch_nmax",
                    display_name="Max mismatches",
                    default=10, min=0, max=30,
                    tooltip="Maximum number of mismatches per read (--outFilterMismatchNmax)"),
                io.Int.Input("align_sj_db_overhang_min",
                    display_name="SJ overhang min",
                    default=100, min=1, max=150,
                    tooltip="Minimum overhang for unannotated junctions (--alignSJDBoverhangMin)"),
                # ── 고급 옵션 ───────────────────────────────────────────
                io.String.Input("extra_args",
                    display_name="Extra STAR arguments",
                    multiline=True, default="",
                    tooltip="Additional STAR flags, e.g. --outFilterMultimapNmax 20"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("bam_path"),
                io.String.Output("log_final_path"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, genome_dir, output_dir, threads,
        out_sam_type, read_files_command,
        out_filter_mismatch_nmax, align_sj_db_overhang_min,
        extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = str(out_dir) + "/"

        paired = bool(r2_path and r2_path.strip())
        read_files = [r1_path] + ([r2_path] if paired else [])

        sam_type_parts = out_sam_type.split()  # ["BAM", "SortedByCoordinate"]

        cmd = [
            "STAR",
            "--runThreadN", str(threads),
            "--genomeDir", genome_dir,
            "--readFilesIn", *read_files,
            "--readFilesCommand", read_files_command,
            "--outFileNamePrefix", prefix,
            "--outSAMtype", *sam_type_parts,
            "--outFilterMismatchNmax", str(out_filter_mismatch_nmax),
            "--alignSJDBoverhangMin", str(align_sj_db_overhang_min),
            "--outSAMattributes", "NH", "HI", "AS", "NM",
        ]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        bam_path = prefix + "Aligned.sortedByCoord.out.bam"
        log_path = prefix + "Log.final.out"

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), bam_path, log_path,
                                 f"ERROR:\n{err}")

        summary = _star_summary(log_path)
        return io.NodeOutput(str(out_dir), bam_path, log_path, summary)


class Kallisto_quant(_Base):
    """Pseudo-alignment and quantification with kallisto.

    Requires a kallisto index (kallisto index -i index.idx transcriptome.fa).
    Supports both single-end and paired-end reads.

    Example extra_args:
        --bias --bootstrap-samples 100 --pseudobam
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Kallisto_quant",
            display_name="kallisto quant",
            category="Transcriptomics/Alignment",
            inputs=[
                # ── 입력 파일 ──────────────────────────────────────────
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default="",
                    tooltip="Read 1 FASTQ path"),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default="",
                    tooltip="Read 2 path. Leave empty for single-end."),
                io.String.Input("index_path",
                    display_name="Kallisto index (.idx)",
                    multiline=False, default="",
                    tooltip="Path to kallisto index file"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                # ── 주요 파라미터 ───────────────────────────────────────
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Float.Input("fragment_length",
                    display_name="Fragment length (single-end only)",
                    default=200.0, min=1.0,
                    tooltip="Estimated average fragment length (single-end only)"),
                io.Float.Input("sd",
                    display_name="Fragment length SD (single-end only)",
                    default=20.0, min=0.1,
                    tooltip="Estimated standard deviation of fragment length (single-end only)"),
                io.Int.Input("bootstrap_samples",
                    display_name="Bootstrap samples",
                    default=0, min=0, max=1000,
                    tooltip="Number of bootstrap samples (0 = no bootstrapping)"),
                io.Boolean.Input("bias",
                    display_name="Sequence-based bias correction",
                    default=False,
                    tooltip="Perform sequence-based bias correction"),
                # ── 고급 옵션 ───────────────────────────────────────────
                io.String.Input("extra_args",
                    display_name="Extra kallisto arguments",
                    multiline=True, default="",
                    tooltip="Additional kallisto flags"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("abundance_tsv"),
                io.String.Output("run_info_json"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, index_path, output_dir, threads,
        fragment_length, sd, bootstrap_samples, bias, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())

        cmd = [
            "kallisto", "quant",
            "--index", index_path,
            "--output-dir", str(out_dir),
            "--threads", str(threads),
        ]
        if not paired:
            cmd += [
                "--single",
                "--fragment-length", str(fragment_length),
                "--sd", str(sd),
            ]
        if bootstrap_samples > 0:
            cmd += ["--bootstrap-samples", str(bootstrap_samples)]
        if bias:
            cmd.append("--bias")
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        cmd.append(r1_path)
        if paired:
            cmd.append(r2_path)

        result = subprocess.run(cmd, capture_output=True, text=True)

        abundance = str(out_dir / "abundance.tsv")
        run_info  = str(out_dir / "run_info.json")

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), abundance, run_info,
                                 f"ERROR:\n{err}")

        summary = _kallisto_summary(run_info, paired)
        return io.NodeOutput(str(out_dir), abundance, run_info, summary)


class Salmon_quant(_Base):
    """Quasi-mapping quantification with salmon.

    Requires a salmon index (salmon index -t transcriptome.fa -i index/).
    Includes GC and sequence-based bias correction options.

    Example extra_args:
        --gcBias --seqBias --numBootstraps 100
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Salmon_quant",
            display_name="salmon quant",
            category="Transcriptomics/Alignment",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default=""),
                io.String.Input("index_dir",
                    display_name="Salmon index directory",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Combo.Input("lib_type",
                    display_name="Library type",
                    options=["A", "ISR", "ISF", "OSR", "OSF", "MSR", "MSF", "SR", "SF"],
                    default="A",
                    tooltip="Library type. 'A' = auto-detect (recommended)"),
                io.Boolean.Input("gc_bias",
                    display_name="GC bias correction",
                    default=False),
                io.Boolean.Input("seq_bias",
                    display_name="Sequence bias correction",
                    default=False),
                io.String.Input("extra_args",
                    display_name="Extra salmon arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("quant_sf"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, index_dir, output_dir, threads,
        lib_type, gc_bias, seq_bias, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())

        cmd = [
            "salmon", "quant",
            "--index", index_dir,
            "--libType", lib_type,
            "--output", str(out_dir),
            "--threads", str(threads),
        ]
        if paired:
            cmd += ["--mates1", r1_path, "--mates2", r2_path]
        else:
            cmd += ["--unmatedReads", r1_path]

        if gc_bias:
            cmd.append("--gcBias")
        if seq_bias:
            cmd.append("--seqBias")
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        quant_sf = str(out_dir / "quant.sf")

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), quant_sf, f"ERROR:\n{err}")

        summary = _salmon_summary(quant_sf)
        return io.NodeOutput(str(out_dir), quant_sf, summary)


# ── 요약 헬퍼 ───────────────────────────────────────────────────────────────

def _star_summary(log_path: str) -> str:
    p = Path(log_path)
    if not p.exists():
        return "Log file not found."
    text = p.read_text()
    lines = ["=== STAR Alignment Summary ==="]
    for keyword in [
        "Number of input reads",
        "Uniquely mapped reads number",
        "Uniquely mapped reads %",
        "Number of reads mapped to multiple loci",
        "% of reads mapped to multiple loci",
        "Number of reads unmapped: too many mismatches",
        "Number of reads unmapped: too short",
    ]:
        for line in text.splitlines():
            if keyword in line:
                lines.append("  " + line.strip())
                break
    return "\n".join(lines)


def _kallisto_summary(run_info_path: str, paired: bool) -> str:
    import json as _json
    p = Path(run_info_path)
    if not p.exists():
        return "run_info.json not found."
    info = _json.loads(p.read_text())
    n_processed = info.get("n_processed", 0)
    n_pseudoaligned = info.get("n_pseudoaligned", 0)
    rate = (n_pseudoaligned / n_processed * 100) if n_processed else 0
    lines = [
        "=== kallisto Summary ===",
        f"Mode             : {'Paired-end' if paired else 'Single-end'}",
        f"Reads processed  : {n_processed:,}",
        f"Pseudo-aligned   : {n_pseudoaligned:,}  ({rate:.1f}%)",
        f"Index version    : {info.get('index_version', 'N/A')}",
    ]
    return "\n".join(lines)


def _salmon_summary(quant_sf: str) -> str:
    p = Path(quant_sf)
    if not p.exists():
        return "quant.sf not found."
    try:
        lines_data = p.read_text().splitlines()
        n_targets = len(lines_data) - 1  # subtract header
        total_tpm = sum(
            float(l.split("\t")[3])
            for l in lines_data[1:]
            if l.strip()
        )
        return "\n".join([
            "=== salmon Summary ===",
            f"Quantified targets : {n_targets:,}",
            f"Total TPM          : {total_tpm:,.1f}",
        ])
    except Exception as e:
        return f"Summary parse error: {e}"
