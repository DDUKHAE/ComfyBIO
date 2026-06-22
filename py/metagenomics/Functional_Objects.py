from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class HUMAnN3_profile(_Base):
    """Functional profiling of metagenomic reads with HUMAnN3.

    Maps reads to UniRef90 gene families and MetaCyc pathways.
    Accepts a pre-computed MetaPhlAn4 profile to speed up taxonomy
    screening. Paired-end reads are merged before analysis.

    Example extra_args:
        --bypass-nucleotide-search --taxonomic-profile-align
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="HUMAnN3_profile",
            display_name="HUMAnN3 profile",
            category="Metagenomics/Functional",
            inputs=[
                io.String.Input("r1_path",
                    display_name="R1 FASTQ (or merged)",
                    multiline=False, default=""),
                io.String.Input("r2_path",
                    display_name="R2 FASTQ (merged before analysis)",
                    multiline=False, default="",
                    tooltip="If provided, reads are merged via cat before HUMAnN3"),
                io.String.Input("metaphlan_profile",
                    display_name="MetaPhlAn4 profile (optional)",
                    multiline=False, default="",
                    tooltip="Pre-computed MetaPhlAn4 profile to skip taxonomy screening"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.String.Input("nucleotide_db",
                    display_name="Nucleotide database",
                    multiline=False, default="",
                    tooltip="Path to ChocoPhlAn nucleotide database. Empty = HUMAnN3 default."),
                io.String.Input("protein_db",
                    display_name="Protein database",
                    multiline=False, default="",
                    tooltip="Path to UniRef protein database. Empty = HUMAnN3 default."),
                io.String.Input("extra_args",
                    display_name="Extra HUMAnN3 arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("genefamilies_path",
                    tooltip="UniRef90 gene family abundances"),
                io.String.Output("pathabundance_path",
                    tooltip="MetaCyc pathway abundances"),
                io.String.Output("pathcoverage_path",
                    tooltip="MetaCyc pathway coverage"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, r1_path, r2_path, metaphlan_profile, output_dir,
        threads, nucleotide_db, protein_db, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        paired = bool(r2_path and r2_path.strip())
        input_path = r1_path

        if paired:
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
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), genefamilies, pathabundance,
                                 pathcoverage, f"ERROR:\n{err}")

        summary = _humann3_summary(pathabundance, genefamilies)
        return io.NodeOutput(str(out_dir), genefamilies, pathabundance,
                             pathcoverage, summary)


class Diamond_blastp(_Base):
    """Protein sequence alignment with DIAMOND blastp.

    Up to 20,000x faster than BLAST with comparable sensitivity.
    Suitable for large-scale metagenomic protein annotation against
    NR, UniRef, or custom databases.

    Example extra_args:
        --id 50 --query-cover 80 --subject-cover 50
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Diamond_blastp",
            display_name="DIAMOND blastp",
            category="Metagenomics/Functional",
            inputs=[
                io.String.Input("query_fasta",
                    display_name="Query protein FASTA",
                    multiline=False, default="",
                    tooltip="Input protein sequences (.faa)"),
                io.String.Input("db_path",
                    display_name="DIAMOND database (.dmnd)",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Int.Input("threads",
                    display_name="Threads",
                    default=4, min=1, max=64),
                io.Combo.Input("sensitivity",
                    display_name="Sensitivity mode",
                    options=["fast", "mid-sensitive", "sensitive",
                             "more-sensitive", "very-sensitive", "ultra-sensitive"],
                    default="sensitive"),
                io.Int.Input("max_target_seqs",
                    display_name="Max target seqs",
                    default=25, min=1, max=500,
                    tooltip="Maximum number of hits per query"),
                io.Float.Input("evalue",
                    display_name="E-value cutoff",
                    default=0.001, min=0.0,
                    tooltip="Maximum e-value for reporting hits"),
                io.String.Input("extra_args",
                    display_name="Extra DIAMOND arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("results_path",
                    tooltip="DIAMOND tabular output (BLAST format 6)"),
                io.Int.Output("n_hits",
                    tooltip="Number of hits reported"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, query_fasta, db_path, output_dir, threads,
        sensitivity, max_target_seqs, evalue, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        results_path = str(out_dir / "diamond_results.tsv")

        cmd = [
            "diamond", "blastp",
            "--query", query_fasta,
            "--db", db_path,
            "--out", results_path,
            "--threads", str(threads),
            f"--{sensitivity}",
            "--max-target-seqs", str(max_target_seqs),
            "--evalue", str(evalue),
            "--outfmt", "6",
        ]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), results_path, 0,
                                 f"ERROR:\n{err}")

        n_hits = 0
        p = Path(results_path)
        if p.exists():
            n_hits = sum(1 for line in p.read_text().splitlines() if line.strip())

        summary = _diamond_summary(results_path, n_hits, sensitivity, evalue)
        return io.NodeOutput(str(out_dir), results_path, n_hits, summary)


def _humann3_summary(pathabundance: str, genefamilies: str) -> str:
    lines = ["=== HUMAnN3 Functional Profile Summary ==="]
    p_path = Path(pathabundance)
    g_path = Path(genefamilies)
    if p_path.exists():
        pathways = [
            l for l in p_path.read_text().splitlines()
            if l.strip() and not l.startswith("#") and "|" not in l
        ]
        n_pathways = len([p for p in pathways if not p.startswith("UNMAPPED")
                          and not p.startswith("UNINTEGRATED")])
        lines.append(f"Pathways detected      : {n_pathways:,}")
    if g_path.exists():
        gene_rows = [
            l for l in g_path.read_text().splitlines()
            if l.strip() and not l.startswith("#") and "|" not in l
        ]
        n_families = len([g for g in gene_rows if not g.startswith("UNMAPPED")])
        lines.append(f"Gene families detected : {n_families:,}")
    lines.append("(Downstream: humann_renorm_table, humann_join_tables)")
    return "\n".join(lines)


def _diamond_summary(results_path: str, n_hits: int,
                     sensitivity: str, evalue: float) -> str:
    lines = [
        "=== DIAMOND blastp Summary ===",
        f"Sensitivity    : {sensitivity}",
        f"E-value cutoff : {evalue}",
        f"Total hits     : {n_hits:,}",
    ]
    p = Path(results_path)
    if p.exists() and n_hits > 0:
        queries = set()
        evalues = []
        for line in p.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) >= 11:
                queries.add(parts[0])
                try:
                    evalues.append(float(parts[10]))
                except ValueError:
                    pass
        lines.append(f"Unique queries : {len(queries):,}")
        if evalues:
            lines.append(f"Median e-value : {sorted(evalues)[len(evalues)//2]:.2e}")
    return "\n".join(lines)
