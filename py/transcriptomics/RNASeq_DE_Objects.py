from __future__ import annotations

import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class DESeq2_run(_Base):
    """Differential expression analysis with DESeq2 (via pydeseq2).

    Inputs a count matrix (genes × samples TSV) and a metadata TSV.
    Outputs a full results table, a significant-genes-only table,
    and a human-readable summary.

    Count matrix format (TSV):
        gene_id  sample1  sample2  ...
        GENE_A   120      240      ...

    Metadata format (TSV):
        sample_id   condition   (other columns allowed)
        sample1     control
        sample2     treated

    extra_args (JSON kwargs passed to DeseqStats):
        {"alpha": 0.01, "cooks_filter": true, "independent_filter": true}
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="DESeq2_run",
            display_name="DESeq2 run",
            category="Transcriptomics/DifferentialExpression",
            inputs=[
                # ── 입력 파일 ──────────────────────────────────────────
                io.String.Input("counts_path",
                    display_name="Count matrix (TSV)",
                    multiline=False, default="",
                    tooltip="Gene count matrix: rows=genes, cols=samples"),
                io.String.Input("metadata_path",
                    display_name="Sample metadata (TSV)",
                    multiline=False, default="",
                    tooltip="TSV with sample_id + condition columns"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default="",
                    tooltip="Directory for results TSV files"),
                # ── 주요 파라미터 ───────────────────────────────────────
                io.String.Input("condition_col",
                    display_name="Condition column",
                    multiline=False, default="condition",
                    tooltip="Column name in metadata that defines groups"),
                io.String.Input("reference_level",
                    display_name="Reference level (control group)",
                    multiline=False, default="control",
                    tooltip="The baseline group for fold-change calculation"),
                io.Float.Input("alpha",
                    display_name="Significance threshold (α)",
                    default=0.05, min=0.0, max=1.0,
                    tooltip="Adjusted p-value cutoff for significant genes"),
                io.Float.Input("lfc_threshold",
                    display_name="log2FC threshold",
                    default=0.0, min=0.0,
                    tooltip="Minimum absolute log2 fold change for testing (0 = standard Wald test)"),
                io.Int.Input("n_cpus",
                    display_name="CPUs",
                    default=1, min=1, max=32),
                # ── 고급 옵션 ───────────────────────────────────────────
                io.String.Input("extra_args",
                    display_name="Extra kwargs (JSON)",
                    multiline=True, default="{}",
                    tooltip='JSON kwargs for DeseqStats, e.g. {"cooks_filter": false}'),
            ],
            outputs=[
                io.String.Output("results_path",
                    tooltip="Full results TSV (all genes)"),
                io.String.Output("significant_path",
                    tooltip="Significant genes only (padj < alpha and |log2FC| > threshold)"),
                io.Int.Output("n_significant",
                    tooltip="Number of significant genes"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, counts_path, metadata_path, output_dir,
        condition_col, reference_level, alpha, lfc_threshold,
        n_cpus, extra_args,
    ) -> io.NodeOutput:
        import json
        import pandas as pd
        from pydeseq2.dds import DeseqDataSet
        from pydeseq2.default_inference import DefaultInference
        from pydeseq2.ds import DeseqStats

        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            extra_kwargs = json.loads(extra_args) if extra_args.strip() else {}
        except json.JSONDecodeError as e:
            summary = f"ERROR: extra_args is not valid JSON — {e}"
            return io.NodeOutput("", "", 0, summary)

        try:
            counts = pd.read_csv(counts_path, sep="\t", index_col=0).T
            metadata = pd.read_csv(metadata_path, sep="\t", index_col=0)

            common = counts.index.intersection(metadata.index)
            counts = counts.loc[common]
            metadata = metadata.loc[common]

            inference = DefaultInference(n_cpus=n_cpus)
            dds = DeseqDataSet(
                counts=counts,
                metadata=metadata,
                design_factors=condition_col,
                ref_level=[condition_col, reference_level],
                refit_cooks=True,
                inference=inference,
            )
            dds.deseq2()

            stat_kwargs = {"alpha": alpha, "inference": inference}
            stat_kwargs.update(extra_kwargs)
            stat_res = DeseqStats(dds, **stat_kwargs)
            stat_res.summary()
            results = stat_res.results_df

            results_path = str(out_dir / "deseq2_all.tsv")
            results.to_csv(results_path, sep="\t")

            sig_mask = (results["padj"] < alpha) & (results["padj"].notna())
            if lfc_threshold > 0:
                sig_mask &= results["log2FoldChange"].abs() >= lfc_threshold
            sig = results[sig_mask].sort_values("padj")
            sig_path = str(out_dir / "deseq2_significant.tsv")
            sig.to_csv(sig_path, sep="\t")

            summary = _deseq2_summary(results, sig, alpha, lfc_threshold)
            return io.NodeOutput(results_path, sig_path, len(sig), summary)

        except Exception as e:
            return io.NodeOutput("", "", 0, f"ERROR: {e}")


def _deseq2_summary(results, sig, alpha: float, lfc_threshold: float) -> str:
    n_total = len(results)
    n_tested = results["padj"].notna().sum()
    n_sig = len(sig)
    n_up = (sig["log2FoldChange"] > 0).sum()
    n_down = (sig["log2FoldChange"] < 0).sum()

    lines = [
        "=== DESeq2 Results Summary ===",
        f"Total genes tested : {n_tested:,} / {n_total:,}",
        f"Significant (padj<{alpha}" +
        (f", |log2FC|≥{lfc_threshold}" if lfc_threshold > 0 else "") + f") : {n_sig:,}",
        f"  Up-regulated     : {n_up:,}",
        f"  Down-regulated   : {n_down:,}",
        "",
        "Top 10 significant genes:",
    ]
    if n_sig > 0:
        for gene, row in sig.head(10).iterrows():
            lines.append(
                f"  {gene:<20}  log2FC={row['log2FoldChange']:+.2f}  "
                f"padj={row['padj']:.2e}"
            )
    else:
        lines.append("  (none)")
    return "\n".join(lines)
