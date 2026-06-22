from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class GATK_haplotype_caller(_Base):
    """Germline variant calling with GATK HaplotypeCaller.

    Requires indexed BAM and reference FASTA (.fai + .dict).
    Supports GVCF mode for joint genotyping across multiple samples.

    Example extra_args:
        --min-base-quality-score 20 --standard-min-confidence-threshold-for-calling 30
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GATK_haplotype_caller",
            display_name="GATK HaplotypeCaller",
            category="VariantAnalysis/Calling",
            inputs=[
                io.String.Input("bam_path",
                    display_name="Input BAM",
                    multiline=False, default="",
                    tooltip="Sorted, indexed BAM file"),
                io.String.Input("reference_fa",
                    display_name="Reference FASTA",
                    multiline=False, default="",
                    tooltip="Reference genome FASTA (must have .fai and .dict)"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.String.Input("sample_name",
                    display_name="Sample name",
                    multiline=False, default="sample"),
                io.Combo.Input("emit_ref_confidence",
                    display_name="ERC mode",
                    options=["NONE", "GVCF"],
                    default="NONE",
                    tooltip="GVCF: emit reference blocks for joint genotyping"),
                io.String.Input("dbsnp_vcf",
                    display_name="dbSNP VCF (optional)",
                    multiline=False, default="",
                    tooltip="Known variants for annotation. Leave empty to skip."),
                io.Int.Input("ploidy",
                    display_name="Sample ploidy",
                    default=2, min=1, max=8,
                    tooltip="Ploidy of the sample (default 2 for diploid)"),
                io.String.Input("extra_args",
                    display_name="Extra GATK arguments",
                    multiline=True, default="",
                    tooltip="Additional HaplotypeCaller flags"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("vcf_path"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, bam_path, reference_fa, output_dir, sample_name,
        emit_ref_confidence, dbsnp_vcf, ploidy, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        ext = ".g.vcf.gz" if emit_ref_confidence == "GVCF" else ".vcf.gz"
        vcf_path = str(out_dir / f"{sample_name}{ext}")

        cmd = [
            "gatk", "HaplotypeCaller",
            "-R", reference_fa,
            "-I", bam_path,
            "-O", vcf_path,
            "--sample-name", sample_name,
            "--ploidy", str(ploidy),
            "-ERC", emit_ref_confidence,
        ]
        if dbsnp_vcf and dbsnp_vcf.strip():
            cmd += ["--dbsnp", dbsnp_vcf]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr[:500]
            return io.NodeOutput(str(out_dir), vcf_path, f"ERROR:\n{err}")

        summary = _vcf_stats_summary(vcf_path, "GATK HaplotypeCaller")
        return io.NodeOutput(str(out_dir), vcf_path, summary)


class Bcftools_call(_Base):
    """Variant calling with bcftools mpileup + call.

    Suitable for small cohorts or when GATK is unavailable.
    Uses the multiallelic or consensus caller model.

    Example extra_args (mpileup part):
        --min-BQ 20 --min-MQ 20 --max-depth 500
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Bcftools_call",
            display_name="bcftools call",
            category="VariantAnalysis/Calling",
            inputs=[
                io.String.Input("bam_path",
                    display_name="Input BAM",
                    multiline=False, default="",
                    tooltip="Sorted, indexed BAM file"),
                io.String.Input("reference_fa",
                    display_name="Reference FASTA",
                    multiline=False, default=""),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Combo.Input("caller",
                    display_name="Caller model",
                    options=["multiallelic", "consensus"],
                    default="multiallelic",
                    tooltip="multiallelic (-m): recommended for most uses; consensus (-c): legacy"),
                io.Int.Input("min_base_quality",
                    display_name="Min base quality",
                    default=20, min=0, max=40),
                io.Int.Input("min_mapping_quality",
                    display_name="Min mapping quality",
                    default=20, min=0, max=60),
                io.String.Input("extra_args",
                    display_name="Extra mpileup arguments",
                    multiline=True, default="",
                    tooltip="Additional bcftools mpileup flags"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("vcf_path"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, bam_path, reference_fa, output_dir, caller,
        min_base_quality, min_mapping_quality, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        vcf_path = str(out_dir / "bcftools.vcf.gz")

        mpileup_cmd = [
            "bcftools", "mpileup",
            "-f", reference_fa,
            "-Q", str(min_base_quality),
            "-q", str(min_mapping_quality),
            "--output-type", "u",
        ]
        if extra_args.strip():
            mpileup_cmd += shlex.split(extra_args)
        mpileup_cmd.append(bam_path)

        caller_flag = "-m" if caller == "multiallelic" else "-c"
        call_cmd = [
            "bcftools", "call",
            caller_flag,
            "--variants-only",
            "--output-type", "z",
            "--output", vcf_path,
        ]

        mpileup_proc = subprocess.Popen(mpileup_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        call_result = subprocess.run(call_cmd, stdin=mpileup_proc.stdout,
                                     capture_output=True, text=True)
        mpileup_proc.wait()

        if mpileup_proc.returncode != 0 or call_result.returncode != 0:
            err = call_result.stderr[:300]
            return io.NodeOutput(str(out_dir), vcf_path, f"ERROR:\n{err}")

        subprocess.run(["bcftools", "index", vcf_path], capture_output=True)
        summary = _vcf_stats_summary(vcf_path, "bcftools call")
        return io.NodeOutput(str(out_dir), vcf_path, summary)


# ── 요약 헬퍼 ───────────────────────────────────────────────────────────────

def _vcf_stats_summary(vcf_path: str, tool: str) -> str:
    result = subprocess.run(
        ["bcftools", "stats", vcf_path],
        capture_output=True, text=True,
    )
    lines = [f"=== {tool} Variant Summary ==="]
    for line in result.stdout.splitlines():
        if line.startswith("SN"):
            parts = line.split("\t")
            if len(parts) >= 4:
                lines.append(f"  {parts[2].rstrip(':'):<30} {parts[3]}")
    if not lines[1:]:
        lines.append("  (bcftools stats not available or VCF empty)")
    return "\n".join(lines)
