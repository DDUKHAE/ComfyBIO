from __future__ import annotations

import json
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class SC_load(_Base):
    """Load single-cell data into AnnData (.h5ad).

    Accepts:
      - 10x Genomics output directory (barcodes.tsv.gz / features.tsv.gz / matrix.mtx.gz)
      - 10x HDF5 file (.h5)
      - AnnData file (.h5ad)
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SC_load",
            display_name="SC load",
            category="Transcriptomics/SingleCell",
            inputs=[
                io.String.Input("input_path",
                    display_name="Input path",
                    multiline=False, default="",
                    tooltip="10x directory, .h5 file, or .h5ad file"),
                io.Combo.Input("input_format",
                    display_name="Format",
                    options=["auto", "10x_mtx", "10x_h5", "h5ad"],
                    default="auto",
                    tooltip="auto = detect from extension/directory contents"),
                io.String.Input("output_path",
                    display_name="Output .h5ad path",
                    multiline=False, default=""),
            ],
            outputs=[
                io.String.Output("output_path"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(cls, input_path, input_format, output_path) -> io.NodeOutput:
        import scanpy as sc
        p = Path(input_path)

        fmt = input_format
        if fmt == "auto":
            if p.is_dir():
                fmt = "10x_mtx"
            elif p.suffix == ".h5":
                fmt = "10x_h5"
            else:
                fmt = "h5ad"

        try:
            if fmt == "10x_mtx":
                adata = sc.read_10x_mtx(str(p), var_names="gene_symbols", cache=False)
            elif fmt == "10x_h5":
                adata = sc.read_10x_h5(str(p))
            else:
                adata = sc.read_h5ad(str(p))
        except Exception as e:
            return io.NodeOutput("", f"ERROR: {e}")

        out = output_path if output_path else str(Path(tempfile.mkdtemp()) / "loaded.h5ad")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        adata.write_h5ad(out)

        summary = "\n".join([
            "=== SC Load Summary ===",
            f"Cells   : {adata.n_obs:,}",
            f"Genes   : {adata.n_vars:,}",
            f"Format  : {fmt}",
        ])
        return io.NodeOutput(out, summary)


class SC_preprocess(_Base):
    """QC filtering, normalization, and highly variable gene selection.

    Pipeline:
      1. Filter cells (min_genes, max_genes)
      2. Filter genes (min_cells)
      3. Compute % mitochondrial genes and filter (max_pct_mito)
      4. Normalize total counts per cell
      5. Log1p transform
      6. Select highly variable genes

    extra_args (JSON kwargs passed to sc.pp.highly_variable_genes):
      {"flavor": "seurat_v3", "min_mean": 0.0125}
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SC_preprocess",
            display_name="SC preprocess",
            category="Transcriptomics/SingleCell",
            inputs=[
                io.String.Input("input_path",
                    display_name="Input .h5ad",
                    multiline=False, default=""),
                io.String.Input("output_path",
                    display_name="Output .h5ad",
                    multiline=False, default=""),
                # ── QC 필터 ──────────────────────────────────────────
                io.Int.Input("min_genes",
                    display_name="Min genes per cell",
                    default=200, min=0,
                    tooltip="Remove cells with fewer genes (low-quality cells)"),
                io.Int.Input("max_genes",
                    display_name="Max genes per cell",
                    default=5000, min=0,
                    tooltip="Remove cells with more genes (likely doublets)"),
                io.Int.Input("min_cells",
                    display_name="Min cells per gene",
                    default=3, min=0,
                    tooltip="Remove genes detected in fewer cells"),
                io.Float.Input("max_pct_mito",
                    display_name="Max % mitochondrial",
                    default=20.0, min=0.0, max=100.0,
                    tooltip="Remove cells with high mitochondrial content (dying cells)"),
                io.String.Input("mito_prefix",
                    display_name="Mitochondrial gene prefix",
                    multiline=False, default="MT-",
                    tooltip="Prefix of mitochondrial gene names (MT- for human, mt- for mouse)"),
                # ── 정규화 ──────────────────────────────────────────
                io.Float.Input("target_sum",
                    display_name="Normalization target sum",
                    default=10000.0, min=1.0,
                    tooltip="Target count sum per cell after normalization (CPM = 1e6)"),
                io.Int.Input("n_top_genes",
                    display_name="Highly variable genes (n)",
                    default=2000, min=100,
                    tooltip="Number of highly variable genes to select"),
                # ── 고급 옵션 ──────────────────────────────────────
                io.String.Input("extra_args",
                    display_name="Extra HVG kwargs (JSON)",
                    multiline=True, default="{}",
                    tooltip='JSON kwargs for sc.pp.highly_variable_genes, e.g. {"flavor": "seurat_v3"}'),
            ],
            outputs=[
                io.String.Output("output_path"),
                io.Int.Output("n_cells_before"),
                io.Int.Output("n_cells_after"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, input_path, output_path, min_genes, max_genes, min_cells,
        max_pct_mito, mito_prefix, target_sum, n_top_genes, extra_args,
    ) -> io.NodeOutput:
        import scanpy as sc

        try:
            extra_kwargs = json.loads(extra_args) if extra_args.strip() else {}
        except json.JSONDecodeError as e:
            return io.NodeOutput("", 0, 0, f"ERROR: extra_args not valid JSON — {e}")

        try:
            adata = sc.read_h5ad(input_path)
            n_before = adata.n_obs

            sc.pp.filter_cells(adata, min_genes=min_genes)
            if max_genes > 0:
                sc.pp.filter_cells(adata, max_genes=max_genes)
            sc.pp.filter_genes(adata, min_cells=min_cells)

            # 미토콘드리아 QC
            mito_genes = adata.var_names.str.startswith(mito_prefix)
            if mito_genes.any():
                adata.obs["pct_counts_mt"] = (
                    adata[:, mito_genes].X.sum(axis=1).A1
                    / adata.X.sum(axis=1).A1 * 100
                )
                adata = adata[adata.obs["pct_counts_mt"] < max_pct_mito].copy()
            else:
                adata.obs["pct_counts_mt"] = 0.0

            n_after = adata.n_obs

            sc.pp.normalize_total(adata, target_sum=target_sum)
            sc.pp.log1p(adata)

            hvg_kwargs = {"n_top_genes": min(n_top_genes, adata.n_vars)}
            hvg_kwargs.update(extra_kwargs)
            sc.pp.highly_variable_genes(adata, **hvg_kwargs)

            out = output_path if output_path else str(Path(tempfile.mkdtemp()) / "preprocessed.h5ad")
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            adata.write_h5ad(out)

            n_hvg = adata.var["highly_variable"].sum()
            pct_mito_mean = adata.obs["pct_counts_mt"].mean()
            summary = "\n".join([
                "=== SC Preprocess Summary ===",
                f"Cells before  : {n_before:,}",
                f"Cells after   : {n_after:,}  ({n_after/n_before*100:.1f}% retained)",
                f"Genes after   : {adata.n_vars:,}",
                f"HVG selected  : {n_hvg:,}",
                f"Mean %mito    : {pct_mito_mean:.1f}%",
            ])
            return io.NodeOutput(out, n_before, n_after, summary)

        except Exception as e:
            return io.NodeOutput("", 0, 0, f"ERROR: {e}")


class SC_cluster(_Base):
    """Dimensionality reduction and clustering of single-cell data.

    Pipeline:
      1. PCA
      2. k-nearest neighbor graph
      3. Leiden or Louvain clustering
      4. UMAP (optional, for visualization)

    extra_args (JSON kwargs passed to clustering function):
      {"random_state": 42, "flavor": "igraph"}
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SC_cluster",
            display_name="SC cluster",
            category="Transcriptomics/SingleCell",
            inputs=[
                io.String.Input("input_path",
                    display_name="Input .h5ad (preprocessed)",
                    multiline=False, default=""),
                io.String.Input("output_path",
                    display_name="Output .h5ad",
                    multiline=False, default=""),
                # ── 주요 파라미터 ──────────────────────────────────────
                io.Int.Input("n_pcs",
                    display_name="PCA components",
                    default=50, min=2, max=200,
                    tooltip="Number of principal components to compute"),
                io.Int.Input("n_neighbors",
                    display_name="k-NN neighbors",
                    default=15, min=2, max=100,
                    tooltip="Number of neighbors for the kNN graph"),
                io.Float.Input("resolution",
                    display_name="Clustering resolution",
                    default=0.5, min=0.01, max=5.0,
                    tooltip="Higher resolution = more clusters"),
                io.Combo.Input("algorithm",
                    display_name="Clustering algorithm",
                    options=["leiden", "louvain"],
                    default="leiden"),
                io.Boolean.Input("compute_umap",
                    display_name="Compute UMAP",
                    default=True,
                    tooltip="Compute UMAP embedding for visualization"),
                # ── 고급 옵션 ──────────────────────────────────────────
                io.String.Input("extra_args",
                    display_name="Extra clustering kwargs (JSON)",
                    multiline=True, default="{}"),
            ],
            outputs=[
                io.String.Output("output_path"),
                io.Int.Output("n_clusters"),
                io.String.Output("cluster_sizes_json"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, input_path, output_path, n_pcs, n_neighbors,
        resolution, algorithm, compute_umap, extra_args,
    ) -> io.NodeOutput:
        import scanpy as sc

        try:
            extra_kwargs = json.loads(extra_args) if extra_args.strip() else {}
        except json.JSONDecodeError as e:
            return io.NodeOutput("", 0, "{}", f"ERROR: extra_args not valid JSON — {e}")

        try:
            adata = sc.read_h5ad(input_path)
            use_hvg = "highly_variable" in adata.var.columns

            n_pcs_actual = min(n_pcs, adata.n_vars - 1, adata.n_obs - 1)
            sc.pp.pca(adata, n_comps=n_pcs_actual, mask_var="highly_variable" if use_hvg else None)

            k = min(n_neighbors, adata.n_obs - 1)
            sc.pp.neighbors(adata, n_neighbors=k, n_pcs=n_pcs_actual)

            if algorithm == "leiden":
                sc.tl.leiden(adata, resolution=resolution, **extra_kwargs)
                cluster_col = "leiden"
            else:
                sc.tl.louvain(adata, resolution=resolution, **extra_kwargs)
                cluster_col = "louvain"

            if compute_umap:
                sc.tl.umap(adata)

            out = output_path if output_path else str(Path(tempfile.mkdtemp()) / "clustered.h5ad")
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            adata.write_h5ad(out)

            sizes = adata.obs[cluster_col].value_counts().to_dict()
            n_clusters = len(sizes)
            sizes_json = json.dumps({str(k): int(v) for k, v in sorted(sizes.items())})

            summary_lines = [
                f"=== SC Cluster Summary ({algorithm}) ===",
                f"Cells        : {adata.n_obs:,}",
                f"Clusters     : {n_clusters}",
                f"Resolution   : {resolution}",
                f"PCs used     : {n_pcs_actual}",
                f"k-NN         : {k}",
                f"UMAP         : {'yes' if compute_umap else 'no'}",
                "",
                "Cluster sizes:",
            ] + [f"  Cluster {k}: {v:,} cells" for k, v in sorted(sizes.items())]

            return io.NodeOutput(out, n_clusters, sizes_json, "\n".join(summary_lines))

        except Exception as e:
            return io.NodeOutput("", 0, "{}", f"ERROR: {e}")


class SC_annotate(_Base):
    """Cell type annotation based on marker gene expression.

    Scores each cluster using mean expression of provided marker genes
    and assigns the best-matching cell type label.

    Marker genes JSON format:
        {
            "T cell":   ["CD3D", "CD3E", "CD3G"],
            "B cell":   ["CD19", "MS4A1", "CD79A"],
            "NK cell":  ["NCAM1", "NKG7", "GNLY"],
            "Monocyte": ["CD14", "LYZ", "CST3"]
        }

    extra_args (JSON):
        {"min_score": 0.1}  — clusters below this mean expression score → "Unknown"
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SC_annotate",
            display_name="SC annotate",
            category="Transcriptomics/SingleCell",
            inputs=[
                io.String.Input("input_path",
                    display_name="Input .h5ad (clustered)",
                    multiline=False, default=""),
                io.String.Input("output_path",
                    display_name="Output .h5ad",
                    multiline=False, default=""),
                io.String.Input("marker_genes_json",
                    display_name="Marker genes (JSON)",
                    multiline=True,
                    default='{\n  "T cell": ["CD3D", "CD3E"],\n  "B cell": ["CD19", "MS4A1"]\n}',
                    tooltip="Dict of {cell_type: [marker_gene, ...]}"),
                io.Float.Input("min_score",
                    display_name="Min score (Unknown threshold)",
                    default=0.0, min=0.0,
                    tooltip="Clusters scoring below this on all types → 'Unknown'"),
                io.String.Input("extra_args",
                    display_name="Extra kwargs (JSON)",
                    multiline=True, default="{}"),
            ],
            outputs=[
                io.String.Output("output_path"),
                io.String.Output("annotation_json",
                    tooltip="Dict of {cluster_id: cell_type}"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, input_path, output_path, marker_genes_json,
        min_score, extra_args,
    ) -> io.NodeOutput:
        import numpy as np
        import anndata as ad

        try:
            marker_genes = json.loads(marker_genes_json)
        except json.JSONDecodeError as e:
            return io.NodeOutput("", "{}", f"ERROR: marker_genes_json not valid JSON — {e}")

        try:
            adata = ad.read_h5ad(input_path)

            cluster_col = None
            for col in ("leiden", "louvain"):
                if col in adata.obs.columns:
                    cluster_col = col
                    break
            if cluster_col is None:
                return io.NodeOutput("", "{}", "ERROR: No 'leiden' or 'louvain' column. Run SC_cluster first.")

            clusters = adata.obs[cluster_col].unique()
            cluster_labels: dict[str, str] = {}
            cluster_scores: dict[str, dict] = {}

            for cluster in clusters:
                mask = adata.obs[cluster_col] == cluster
                scores: dict[str, float] = {}
                for cell_type, markers in marker_genes.items():
                    present = [g for g in markers if g in adata.var_names]
                    if not present:
                        scores[cell_type] = 0.0
                        continue
                    data = adata[mask, present].X
                    if hasattr(data, "toarray"):
                        data = data.toarray()
                    scores[cell_type] = float(np.mean(data))

                best_type = "Unknown"
                best_score = min_score
                for cell_type, score in scores.items():
                    if score > best_score:
                        best_score = score
                        best_type = cell_type

                cluster_labels[str(cluster)] = best_type
                cluster_scores[str(cluster)] = {k: round(v, 4) for k, v in scores.items()}

            adata.obs["cell_type"] = adata.obs[cluster_col].map(cluster_labels)

            out = output_path if output_path else str(Path(tempfile.mkdtemp()) / "annotated.h5ad")
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            adata.write_h5ad(out)

            annotation_json = json.dumps(cluster_labels)
            type_counts = adata.obs["cell_type"].value_counts().to_dict()

            summary_lines = [
                "=== SC Annotate Summary ===",
                f"Clusters annotated : {len(cluster_labels)}",
                "",
                "Cell type distribution:",
            ] + [f"  {ct}: {count:,} cells" for ct, count in sorted(type_counts.items())]

            return io.NodeOutput(out, annotation_json, "\n".join(summary_lines))

        except Exception as e:
            return io.NodeOutput("", "{}", f"ERROR: {e}")


class SC_markers(_Base):
    """Find marker genes for each cluster using scanpy.

    Performs differential expression between each cluster and the rest
    to identify cluster-specific marker genes.

    extra_args (JSON kwargs for sc.tl.rank_genes_groups):
      {"method": "wilcoxon", "use_raw": false, "pts": true}
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SC_markers",
            display_name="SC find markers",
            category="Transcriptomics/SingleCell",
            inputs=[
                io.String.Input("input_path",
                    display_name="Input .h5ad (clustered)",
                    multiline=False, default=""),
                io.String.Input("output_path",
                    display_name="Output .h5ad",
                    multiline=False, default=""),
                io.Combo.Input("method",
                    display_name="Test method",
                    options=["wilcoxon", "t-test", "logreg", "t-test_overestim_var"],
                    default="wilcoxon",
                    tooltip="Statistical test for marker gene identification"),
                io.Int.Input("n_genes",
                    display_name="Top N genes per cluster",
                    default=25, min=1, max=500,
                    tooltip="Number of top marker genes to report per cluster"),
                io.Float.Input("min_fold_change",
                    display_name="Min fold change",
                    default=1.5, min=1.0,
                    tooltip="Minimum fold change for marker genes"),
                io.String.Input("output_tsv",
                    display_name="Markers TSV path",
                    multiline=False, default="",
                    tooltip="Optional: save marker table as TSV"),
                io.String.Input("extra_args",
                    display_name="Extra kwargs (JSON)",
                    multiline=True, default="{}"),
            ],
            outputs=[
                io.String.Output("output_path"),
                io.String.Output("markers_tsv"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, input_path, output_path, method, n_genes,
        min_fold_change, output_tsv, extra_args,
    ) -> io.NodeOutput:
        import scanpy as sc
        import pandas as pd

        try:
            extra_kwargs = json.loads(extra_args) if extra_args.strip() else {}
        except json.JSONDecodeError as e:
            return io.NodeOutput("", "", f"ERROR: extra_args not valid JSON — {e}")

        try:
            adata = sc.read_h5ad(input_path)

            cluster_col = None
            for col in ("leiden", "louvain", "cell_type"):
                if col in adata.obs.columns:
                    cluster_col = col
                    break
            if cluster_col is None:
                return io.NodeOutput("", "", "ERROR: No cluster column found.")

            rank_kwargs = {"groupby": cluster_col, "method": method, "n_genes": n_genes}
            rank_kwargs.update(extra_kwargs)
            sc.tl.rank_genes_groups(adata, **rank_kwargs)

            out = output_path if output_path else str(Path(tempfile.mkdtemp()) / "markers.h5ad")
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            adata.write_h5ad(out)

            # 마커 테이블 생성
            result = adata.uns["rank_genes_groups"]
            groups = result["names"].dtype.names
            records = []
            for group in groups:
                for i in range(n_genes):
                    records.append({
                        "cluster": group,
                        "gene": result["names"][group][i],
                        "score": result["scores"][group][i],
                        "logfoldchanges": result.get("logfoldchanges", {}).get(group, [None]*n_genes)[i],
                        "pvals_adj": result["pvals_adj"][group][i],
                    })
            df = pd.DataFrame(records)

            tsv_path = output_tsv or str(Path(out).parent / "markers.tsv")
            df.to_csv(tsv_path, sep="\t", index=False)

            summary_lines = [
                f"=== SC Markers Summary ({method}) ===",
                f"Clusters : {len(groups)}",
                f"Top genes per cluster : {n_genes}",
                "",
                "Top marker per cluster:",
            ]
            for group in groups:
                top_gene = result["names"][group][0]
                top_score = result["scores"][group][0]
                summary_lines.append(f"  Cluster {group}: {top_gene} (score={top_score:.2f})")

            return io.NodeOutput(out, tsv_path, "\n".join(summary_lines))

        except Exception as e:
            return io.NodeOutput("", "", f"ERROR: {e}")
