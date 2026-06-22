from __future__ import annotations

import re
import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Megahit_assemble(_Base):
    """De novo metagenomic assembly with MEGAHIT.

    Memory-efficient assembler using succinct de Bruijn graphs.
    Suitable for complex environmental samples.

    Example extra_args:
        --k-min 27 --k-max 127 --k-step 10
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Megahit_assemble",
            display_name="MEGAHIT assemble",
            category="Metagenomics/Assembly",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Int.Input("min_contig_len",
                    display_name="Min contig length (bp)",
                    default=500, min=100, max=10000),
                io.Float.Input("memory_fraction",
                    display_name="Memory fraction",
                    default=0.8, min=0.1, max=0.99,
                    tooltip="Fraction of available RAM to use"),
                io.Combo.Input("preset",
                    display_name="Assembly preset",
                    options=["meta-sensitive", "meta-large", "default"],
                    default="meta-sensitive"),
                io.String.Input("extra_args",
                    display_name="Extra MEGAHIT arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("contigs_path",
                    tooltip="Final assembled contigs FASTA"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, output_dir, threads,
        min_contig_len, memory_fraction, preset, extra_args,
    ) -> io.NodeOutput:
        import shutil
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        megahit_out = out_dir / "megahit_output"

        if megahit_out.exists():
            shutil.rmtree(megahit_out)

        paired = bool(r2_path and r2_path.strip())

        cmd = [
            "megahit",
            "--num-cpu-threads", str(threads),
            "--min-contig-len", str(min_contig_len),
            "--memory", str(memory_fraction),
            "--out-dir", str(megahit_out),
        ]
        if preset != "default":
            cmd.append(f"--presets {preset}")
        if paired:
            cmd += ["-1", r1_path, "-2", r2_path]
        else:
            cmd += ["-r", r1_path]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        contigs_path = str(megahit_out / "final.contigs.fa")

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(megahit_out), contigs_path,
                                 f"ERROR:\n{err}")

        summary = _megahit_summary(contigs_path, result.stderr + result.stdout)
        return io.NodeOutput(str(megahit_out), contigs_path, summary)


class Prodigal_predict(_Base):
    """Prokaryotic gene prediction with Prodigal.

    Predicts coding sequences in metagenomic contigs.
    Use 'meta' mode for environmental samples with mixed organisms.

    Example extra_args:
        -c (closed ends) -n (bypass Shine-Dalgarno trainer)
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Prodigal_predict",
            display_name="Prodigal gene predict",
            category="Metagenomics/Assembly",
            inputs=[
                io.String.Input("contigs_path",
                    display_name="Contigs FASTA",
                    multiline=False, default="",
                    tooltip="Assembled contigs from MEGAHIT or metaSPAdes"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Combo.Input("mode",
                    display_name="Prediction mode",
                    options=["meta", "single", "train"],
                    default="meta",
                    tooltip="meta=metagenomes, single=isolate genome"),
                io.Combo.Input("output_format",
                    display_name="Gene annotation format",
                    options=["gff", "gbk", "sco"],
                    default="gff"),
                io.String.Input("extra_args",
                    display_name="Extra Prodigal arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("genes_path",
                    tooltip="Gene annotations (GFF/GBK/SCO)"),
                io.String.Output("proteins_path",
                    tooltip="Predicted protein sequences (FAA)"),
                io.Int.Output("n_genes",
                    tooltip="Number of predicted genes"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, contigs_path, output_dir, mode, output_format, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        genes_path = str(out_dir / f"genes.{output_format}")
        proteins_path = str(out_dir / "proteins.faa")

        cmd = [
            "prodigal",
            "-i", contigs_path,
            "-p", mode,
            "-f", output_format,
            "-o", genes_path,
            "-a", proteins_path,
        ]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), genes_path, proteins_path, 0,
                                 f"ERROR:\n{err}")

        n_genes = _count_prodigal_genes(proteins_path)
        summary = _prodigal_summary(n_genes, mode, output_format)
        return io.NodeOutput(str(out_dir), genes_path, proteins_path,
                             n_genes, summary)


def _megahit_summary(contigs_path: str, log_text: str) -> str:
    lines = ["=== MEGAHIT Assembly Summary ==="]
    p = Path(contigs_path)
    if p.exists():
        seqs = []
        current_len = 0
        for line in p.read_text().splitlines():
            if line.startswith(">"):
                if current_len > 0:
                    seqs.append(current_len)
                current_len = 0
            else:
                current_len += len(line.strip())
        if current_len > 0:
            seqs.append(current_len)
        seqs.sort(reverse=True)
        total_len = sum(seqs)
        n_contigs = len(seqs)
        n50 = 0
        cumulative = 0
        for s in seqs:
            cumulative += s
            if cumulative >= total_len / 2:
                n50 = s
                break
        lines += [
            f"Contigs        : {n_contigs:,}",
            f"Total length   : {total_len:,} bp",
            f"N50            : {n50:,} bp",
            f"Longest contig : {seqs[0]:,} bp" if seqs else "",
        ]
    else:
        for line in log_text.splitlines():
            if "contigs" in line.lower() or "N50" in line:
                lines.append("  " + line.strip())
    return "\n".join(l for l in lines if l)


def _count_prodigal_genes(proteins_path: str) -> int:
    p = Path(proteins_path)
    if not p.exists():
        return 0
    return sum(1 for line in p.read_text().splitlines() if line.startswith(">"))


def _prodigal_summary(n_genes: int, mode: str, fmt: str) -> str:
    return "\n".join([
        "=== Prodigal Gene Prediction Summary ===",
        f"Mode           : {mode}",
        f"Output format  : {fmt}",
        f"Genes predicted: {n_genes:,}",
    ])
