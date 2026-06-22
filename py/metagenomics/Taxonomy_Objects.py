from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Kraken2_classify(_Base):
    """Taxonomic classification of metagenomic reads with Kraken2.

    Uses exact k-mer matching against a curated database (e.g. Standard,
    PlusPF, or custom). Bracken can be run downstream for abundance
    re-estimation.

    Example extra_args:
        --minimum-hit-groups 3 --report-zero-counts
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Kraken2_classify",
            display_name="Kraken2 classify",
            category="Metagenomics/Taxonomy",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ",
                    multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (paired-end, optional)",
                    multiline=False, default=""),
                io.String.Input("db_path",
                    display_name="Kraken2 database",
                    multiline=False, default="",
                    tooltip="Path to Kraken2 database directory"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Float.Input("confidence",
                    display_name="Confidence threshold",
                    default=0.0, min=0.0, max=1.0,
                    tooltip="Confidence score threshold (0 = standard Kraken2)"),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.String.Input("extra_args",
                    display_name="Extra Kraken2 arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("report_path",
                    tooltip="Kraken2 report (tab-separated taxonomy)"),
                io.String.Output("output_path",
                    tooltip="Per-read classification output"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, db_path, output_dir,
        confidence, threads, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())
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
        if paired:
            cmd += ["--paired", r1_path, r2_path]
        else:
            cmd.append(r1_path)
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), report_path, output_path,
                                 f"ERROR:\n{err}")

        summary = _kraken2_summary(report_path, result.stderr)
        return io.NodeOutput(str(out_dir), report_path, output_path, summary)


class Bracken_abundance(_Base):
    """Bayesian abundance re-estimation from Kraken2 report with Bracken.

    Re-distributes reads from higher taxonomic levels to the target level
    for accurate abundance estimation.

    Example extra_args:
        -r 100 (if read length differs from database build)
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Bracken_abundance",
            display_name="Bracken abundance",
            category="Metagenomics/Taxonomy",
            inputs=[
                io.String.Input("kraken_report",
                    display_name="Kraken2 report",
                    multiline=False, default="",
                    tooltip="Output from Kraken2 --report"),
                io.String.Input("db_path",
                    display_name="Kraken2/Bracken database",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("read_length",
                    display_name="Read length",
                    default=150, min=50, max=300,
                    tooltip="Must match database build read length"),
                io.Combo.Input("level",
                    display_name="Taxonomic level",
                    options=["S", "G", "F", "O", "C", "P"],
                    default="S",
                    tooltip="S=Species, G=Genus, F=Family, O=Order, C=Class, P=Phylum"),
                io.Int.Input("threshold",
                    display_name="Min reads threshold",
                    default=10, min=0,
                    tooltip="Minimum reads to report a taxon"),
                io.String.Input("extra_args",
                    display_name="Extra Bracken arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("bracken_report",
                    tooltip="Bracken abundance report"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, kraken_report, db_path, output_dir,
        read_length, level, threshold, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        bracken_out = str(out_dir / f"bracken_{level}.txt")

        cmd = [
            "bracken",
            "-d", db_path,
            "-i", kraken_report,
            "-o", bracken_out,
            "-r", str(read_length),
            "-l", level,
            "-t", str(threshold),
        ]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), bracken_out, f"ERROR:\n{err}")

        summary = _bracken_summary(bracken_out, level)
        return io.NodeOutput(str(out_dir), bracken_out, summary)


class MetaPhlAn_profile(_Base):
    """Metagenomic taxonomic profiling with MetaPhlAn4.

    Uses clade-specific marker genes for highly accurate relative
    abundance estimation without a reference database alignment step.

    Example extra_args:
        --unknown_estimation --add_viruses
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="MetaPhlAn_profile",
            display_name="MetaPhlAn4 profile",
            category="Metagenomics/Taxonomy",
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
                io.String.Input("db_path",
                    display_name="MetaPhlAn4 database path",
                    multiline=False, default="",
                    tooltip="Path to MetaPhlAn4 database directory. Empty = auto-detect."),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Combo.Input("analysis_type",
                    display_name="Analysis type",
                    options=["rel_ab", "rel_ab_w_read_stats",
                             "reads_map", "clade_profiles"],
                    default="rel_ab"),
                io.String.Input("extra_args",
                    display_name="Extra MetaPhlAn arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("profile_path",
                    tooltip="MetaPhlAn abundance profile"),
                io.String.Output("bowtie_path",
                    tooltip="Bowtie2 alignment file (.bz2)"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, output_dir, db_path,
        threads, analysis_type, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())
        profile_path = str(out_dir / "metaphlan_profile.txt")
        bowtie_path = str(out_dir / "metaphlan_bowtie2.bz2")

        input_reads = [r1_path]
        if paired:
            input_reads.append(r2_path)

        cmd = [
            "metaphlan",
            ",".join(input_reads),
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
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), profile_path, bowtie_path,
                                 f"ERROR:\n{err}")

        summary = _metaphlan_summary(profile_path)
        return io.NodeOutput(str(out_dir), profile_path, bowtie_path, summary)


def _kraken2_summary(report_path: str, stderr: str) -> str:
    lines = ["=== Kraken2 Classification Summary ==="]
    for line in stderr.splitlines():
        if "sequences" in line.lower() or "classified" in line.lower():
            lines.append("  " + line.strip())

    p = Path(report_path)
    if p.exists():
        lines.append("\nTop 10 species (by read count):")
        species_rows = []
        for row in p.read_text().splitlines():
            parts = row.split("\t")
            if len(parts) >= 6 and parts[3].strip() == "S":
                try:
                    species_rows.append((int(parts[1]), parts[5].strip()))
                except ValueError:
                    pass
        for count, name in sorted(species_rows, reverse=True)[:10]:
            lines.append(f"  {name:<40}  {count:,} reads")
    return "\n".join(lines)


def _bracken_summary(report_path: str, level: str) -> str:
    level_map = {"S": "Species", "G": "Genus", "F": "Family",
                 "O": "Order", "C": "Class", "P": "Phylum"}
    lines = [f"=== Bracken Abundance ({level_map.get(level, level)}) ==="]
    p = Path(report_path)
    if not p.exists():
        lines.append("  Report file not found.")
        return "\n".join(lines)
    rows = []
    for row in p.read_text().splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) >= 7:
            try:
                rows.append((float(parts[6]), parts[0]))
            except ValueError:
                pass
    lines.append(f"Total taxa reported: {len(rows)}")
    lines.append("Top 10 by abundance:")
    for frac, name in sorted(rows, reverse=True)[:10]:
        lines.append(f"  {name:<40}  {frac*100:.2f}%")
    return "\n".join(lines)


def _metaphlan_summary(profile_path: str) -> str:
    lines = ["=== MetaPhlAn4 Profile Summary ==="]
    p = Path(profile_path)
    if not p.exists():
        lines.append("  Profile file not found.")
        return "\n".join(lines)
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
    lines.append("Top 10 by relative abundance:")
    for abund, name in sorted(species, reverse=True)[:10]:
        lines.append(f"  {name:<40}  {abund:.2f}%")
    return "\n".join(lines)
