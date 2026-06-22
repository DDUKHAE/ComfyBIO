from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class PLINK_qc(_Base):
    """Sample and variant quality control with PLINK.

    Filters by missingness (mind/geno), allele frequency (maf),
    and Hardy-Weinberg equilibrium (hwe). Outputs a cleaned binary fileset.

    Example extra_args:
        --hwe 1e-6 midp --remove-fam samples_to_remove.txt
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PLINK_qc",
            display_name="PLINK QC",
            category="VariantAnalysis/GWAS",
            inputs=[
                io.String.Input("bed_prefix",
                    display_name="PLINK binary prefix",
                    multiline=False, default="",
                    tooltip="Path prefix for .bed/.bim/.fam files (without extension)"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Float.Input("mind",
                    display_name="Sample missingness (mind)",
                    default=0.05, min=0.0, max=1.0,
                    tooltip="Exclude samples with >mind missing genotypes"),
                io.Float.Input("geno",
                    display_name="Variant missingness (geno)",
                    default=0.05, min=0.0, max=1.0,
                    tooltip="Exclude variants with >geno missing calls"),
                io.Float.Input("maf",
                    display_name="Minor allele frequency (maf)",
                    default=0.01, min=0.0, max=0.5,
                    tooltip="Exclude variants with MAF below threshold"),
                io.Float.Input("hwe",
                    display_name="HWE p-value threshold",
                    default=1e-6, min=0.0, max=1.0,
                    tooltip="Exclude variants failing HWE test below this p-value"),
                io.String.Input("extra_args",
                    display_name="Extra PLINK arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("filtered_prefix"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, bed_prefix, output_dir, mind, geno, maf, hwe, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        out_prefix = str(out_dir / "qc_filtered")

        cmd = [
            "plink",
            "--bfile", bed_prefix,
            "--mind", str(mind),
            "--geno", str(geno),
            "--maf", str(maf),
            "--hwe", str(hwe),
            "--make-bed",
            "--out", out_prefix,
        ]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr[:500] or result.stdout[:500]
            return io.NodeOutput(str(out_dir), out_prefix, f"ERROR:\n{err}")

        summary = _plink_log_summary(out_prefix + ".log", "PLINK QC")
        return io.NodeOutput(str(out_dir), out_prefix, summary)


class PLINK_assoc(_Base):
    """GWAS association testing with PLINK.

    Performs case-control (logistic/assoc) or quantitative trait (linear)
    association testing. Outputs association results with p-values.

    Example extra_args:
        --covar covariates.txt --covar-name PC1,PC2,PC3 --ci 0.95
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PLINK_assoc",
            display_name="PLINK association",
            category="VariantAnalysis/GWAS",
            inputs=[
                io.String.Input("bed_prefix",
                    display_name="PLINK binary prefix",
                    multiline=False, default="",
                    tooltip="QC-filtered .bed/.bim/.fam prefix"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.String.Input("pheno_file",
                    display_name="Phenotype file (optional)",
                    multiline=False, default="",
                    tooltip="PLINK phenotype file. Leave empty to use .fam column 6."),
                io.Combo.Input("test",
                    display_name="Association test",
                    options=["assoc", "logistic", "linear"],
                    default="assoc",
                    tooltip="assoc: chi-square; logistic: binary traits; linear: quantitative"),
                io.Float.Input("maf",
                    display_name="MAF filter",
                    default=0.01, min=0.0, max=0.5),
                io.Float.Input("hwe",
                    display_name="HWE filter",
                    default=1e-6, min=0.0, max=1.0),
                io.Float.Input("geno",
                    display_name="Variant missingness filter",
                    default=0.05, min=0.0, max=1.0),
                io.String.Input("extra_args",
                    display_name="Extra PLINK arguments",
                    multiline=True, default="",
                    tooltip="e.g. --covar covariates.txt --covar-name PC1,PC2,PC3"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("results_path"),
                io.Int.Output("n_significant"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, bed_prefix, output_dir, pheno_file, test, maf, hwe, geno, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        out_prefix = str(out_dir / "gwas")

        cmd = [
            "plink",
            "--bfile", bed_prefix,
            f"--{test}",
            "--maf", str(maf),
            "--hwe", str(hwe),
            "--geno", str(geno),
            "--out", out_prefix,
        ]
        if pheno_file and pheno_file.strip():
            cmd += ["--pheno", pheno_file]
        if extra_args.strip():
            cmd += shlex.split(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr[:500] or result.stdout[:500]
            return io.NodeOutput(str(out_dir), out_prefix, 0, f"ERROR:\n{err}")

        # Find results file
        results_path = ""
        for ext in [f".{test}", f".{test}.adjusted", ".assoc", ".logistic", ".linear"]:
            candidate = out_prefix + ext
            if Path(candidate).exists():
                results_path = candidate
                break

        n_sig, summary = _gwas_summary(results_path, test, out_prefix + ".log")
        return io.NodeOutput(str(out_dir), results_path or out_prefix, n_sig, summary)


# ── 요약 헬퍼 ───────────────────────────────────────────────────────────────

def _plink_log_summary(log_path: str, step: str) -> str:
    lines = [f"=== {step} Summary ==="]
    p = Path(log_path)
    if not p.exists():
        lines.append("  Log file not found.")
        return "\n".join(lines)
    for line in p.read_text().splitlines():
        line = line.strip()
        if any(kw in line for kw in [
            "samples", "variants", "removed", "excluded", "pass filters"
        ]):
            lines.append("  " + line)
    return "\n".join(lines)


def _gwas_summary(results_path: str, test: str, log_path: str) -> tuple[int, str]:
    lines = ["=== PLINK Association Summary ===", f"  Test : {test}"]
    n_sig = 0
    p = Path(results_path)
    if p.exists():
        try:
            import csv
            with open(results_path) as f:
                reader = csv.DictReader(f, delimiter="\t")
                # handle whitespace-delimited PLINK output
            # fall back to line counting
            rows = p.read_text().splitlines()[1:]
            n_total = len(rows)
            n_sig = sum(
                1 for r in rows
                if r.strip() and _p_col_below(r, 5e-8)
            )
            lines += [
                f"  Total variants tested : {n_total:,}",
                f"  Genome-wide significant (p<5e-8) : {n_sig:,}",
            ]
        except Exception as e:
            lines.append(f"  (summary parse error: {e})")
    lines += _plink_log_summary(log_path, "").splitlines()[1:]
    return n_sig, "\n".join(lines)


def _p_col_below(row: str, threshold: float) -> bool:
    parts = row.split()
    # PLINK assoc P is typically column 9 (0-indexed: 8)
    for part in reversed(parts):
        try:
            v = float(part)
            if 0 < v <= 1:
                return v < threshold
        except ValueError:
            continue
    return False
