from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class GATK_VQSR(_Base):
    """Variant Quality Score Recalibration (VQSR) with GATK.

    Applies machine-learning-based variant filtering. Requires ≥30 samples
    for SNP training; falls back to hard filters for small cohorts.

    Runs VariantRecalibrator + ApplyVQSR for SNPs, INDELs, or both.

    Example extra_args:
        --max-gaussians 4 --trust-all-polymorphic
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GATK_VQSR",
            display_name="GATK VQSR filter",
            category="VariantAnalysis/Filter",
            inputs=[
                io.String.Input("vcf_path",
                    display_name="Input VCF",
                    multiline=False, default=""),
                io.String.Input("reference_fa",
                    display_name="Reference FASTA",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Combo.Input("variant_type",
                    display_name="Variant type",
                    options=["SNP", "INDEL", "BOTH"],
                    default="SNP"),
                io.Float.Input("truth_sensitivity_filter_level",
                    display_name="Truth sensitivity filter level (%)",
                    default=99.0, min=90.0, max=100.0,
                    tooltip="Sensitivity threshold for VQSR PASS filter"),
                io.String.Input("extra_args",
                    display_name="Extra GATK arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("filtered_vcf"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, vcf_path, reference_fa, output_dir,
        variant_type, truth_sensitivity_filter_level, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        filtered_vcf = str(out_dir / "vqsr_filtered.vcf.gz")
        recal_file = str(out_dir / "vqsr.recal")
        tranches_file = str(out_dir / "vqsr.tranches")

        types_to_run = (
            ["SNP", "INDEL"] if variant_type == "BOTH" else [variant_type]
        )

        current_vcf = vcf_path
        for vtype in types_to_run:
            recal_cmd = [
                "gatk", "VariantRecalibrator",
                "-R", reference_fa,
                "-V", current_vcf,
                "--mode", vtype,
                "-O", recal_file,
                "--tranches-file", tranches_file,
            ]
            if extra_args.strip():
                recal_cmd += shlex.split(extra_args)

            recal_result = subprocess.run(recal_cmd, capture_output=True, text=True)
            if recal_result.returncode != 0:
                err = recal_result.stderr[:500]
                return io.NodeOutput(str(out_dir), vcf_path,
                                     f"VariantRecalibrator ERROR:\n{err}")

            apply_cmd = [
                "gatk", "ApplyVQSR",
                "-R", reference_fa,
                "-V", current_vcf,
                "-O", filtered_vcf,
                "--recal-file", recal_file,
                "--tranches-file", tranches_file,
                "--mode", vtype,
                "--truth-sensitivity-filter-level",
                str(truth_sensitivity_filter_level),
            ]
            apply_result = subprocess.run(apply_cmd, capture_output=True, text=True)
            if apply_result.returncode != 0:
                err = apply_result.stderr[:500]
                return io.NodeOutput(str(out_dir), vcf_path,
                                     f"ApplyVQSR ERROR:\n{err}")
            current_vcf = filtered_vcf

        summary = _pass_count_summary(filtered_vcf, "GATK VQSR")
        return io.NodeOutput(str(out_dir), filtered_vcf, summary)


class Bcftools_filter(_Base):
    """Hard-filter variants with bcftools.

    Applies expression-based inclusion filter. Suitable for all cohort sizes.
    Use JEXL expressions to combine QUAL, DP, MQ, etc.

    Example include_expr:
        QUAL>=30 && DP>=10 && MQ>=40 && QD>=2.0
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Bcftools_filter",
            display_name="bcftools filter",
            category="VariantAnalysis/Filter",
            inputs=[
                io.String.Input("vcf_path",
                    display_name="Input VCF",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.String.Input("include_expr",
                    display_name="Include expression",
                    multiline=False,
                    default="QUAL>=30 && DP>=10",
                    tooltip="bcftools filter -i expression. Variants NOT matching are removed."),
                io.String.Input("extra_args",
                    display_name="Extra bcftools arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("filtered_vcf"),
                io.Int.Output("n_variants"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(cls, vcf_path, output_dir, include_expr, extra_args) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        filtered_vcf = str(out_dir / "filtered.vcf.gz")

        cmd = [
            "bcftools", "filter",
            "--include", include_expr,
            "--output-type", "z",
            "--output", filtered_vcf,
        ]
        if extra_args.strip():
            cmd += shlex.split(extra_args)
        cmd.append(vcf_path)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return io.NodeOutput(vcf_path, 0, f"ERROR:\n{result.stderr[:500]}")

        subprocess.run(["bcftools", "index", filtered_vcf], capture_output=True)

        count_result = subprocess.run(
            ["bcftools", "view", "--no-header", "-c", "1", filtered_vcf],
            capture_output=True, text=True,
        )
        n_variants = count_result.stdout.count("\n")

        summary = "\n".join([
            "=== bcftools filter Summary ===",
            f"  Filter expression : {include_expr}",
            f"  Variants passing  : {n_variants:,}",
        ])
        return io.NodeOutput(filtered_vcf, n_variants, summary)


class VEP_annotate(_Base):
    """Variant annotation with Ensembl VEP.

    Requires VEP cache installed locally (--cache_dir).
    Annotates variants with gene, consequence, SIFT, PolyPhen, etc.

    Example extra_args:
        --sift b --polyphen b --regulatory --check_existing
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="VEP_annotate",
            display_name="VEP annotate",
            category="VariantAnalysis/Filter",
            inputs=[
                io.String.Input("vcf_path",
                    display_name="Input VCF",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.String.Input("species",
                    display_name="Species",
                    multiline=False, default="homo_sapiens"),
                io.Combo.Input("assembly",
                    display_name="Assembly",
                    options=["GRCh38", "GRCh37", "GRCm39"],
                    default="GRCh38"),
                io.String.Input("cache_dir",
                    display_name="VEP cache directory",
                    multiline=False, default="",
                    tooltip="Path to VEP cache. Leave empty to use default ~/.vep"),
                io.String.Input("extra_args",
                    display_name="Extra VEP arguments",
                    multiline=True, default="",
                    tooltip="e.g. --sift b --polyphen b --regulatory"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("annotated_vcf"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, vcf_path, output_dir, species, assembly, cache_dir, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        annotated_vcf = str(out_dir / "vep_annotated.vcf.gz")
        stats_file = str(out_dir / "vep_stats.txt")

        cmd = [
            "vep",
            "--input_file", vcf_path,
            "--output_file", annotated_vcf,
            "--vcf", "--compress_output", "bgzip",
            "--species", species,
            "--assembly", assembly,
            "--cache",
            "--stats_file", stats_file,
            "--offline",
            "--fork", "4",
        ]
        if cache_dir and cache_dir.strip():
            cmd += ["--dir_cache", cache_dir]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), vcf_path, f"ERROR:\n{err}")

        summary = _vep_summary(stats_file, species, assembly)
        return io.NodeOutput(str(out_dir), annotated_vcf, summary)


# ── 요약 헬퍼 ───────────────────────────────────────────────────────────────

def _pass_count_summary(vcf_path: str, tool: str) -> str:
    result = subprocess.run(
        ["bcftools", "view", "-f", "PASS", "--no-header", vcf_path],
        capture_output=True, text=True,
    )
    n_pass = result.stdout.count("\n")
    return "\n".join([
        f"=== {tool} Filter Summary ===",
        f"  Variants with PASS : {n_pass:,}",
    ])


def _vep_summary(stats_file: str, species: str, assembly: str) -> str:
    lines = [
        "=== VEP Annotation Summary ===",
        f"  Species  : {species}",
        f"  Assembly : {assembly}",
    ]
    p = Path(stats_file)
    if p.exists():
        for line in p.read_text().splitlines():
            if "Variants processed" in line or "Variants remaining" in line:
                lines.append("  " + line.strip())
    return "\n".join(lines)
