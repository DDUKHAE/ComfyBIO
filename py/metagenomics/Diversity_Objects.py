from __future__ import annotations

import math
import tempfile
from pathlib import Path
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Alpha_diversity(_Base):
    """Alpha diversity calculation from abundance profiles.

    Computes within-sample diversity metrics (Shannon, Simpson, Chao1,
    observed OTUs) from MetaPhlAn or Bracken abundance tables.
    Uses scikit-bio when available; falls back to built-in implementations.

    Input format (TSV): rows = taxa, columns = samples (or single sample).
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Alpha_diversity",
            display_name="alpha diversity",
            category="Metagenomics/Diversity",
            inputs=[
                io.String.Input("profile_path",
                    display_name="Abundance profile (TSV)",
                    multiline=False, default="",
                    tooltip="MetaPhlAn profile or Bracken abundance table"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Combo.Input("metric",
                    display_name="Diversity metric",
                    options=["shannon", "simpson", "chao1", "observed_otus"],
                    default="shannon"),
                io.String.Input("sample_col",
                    display_name="Sample column (optional)",
                    multiline=False, default="",
                    tooltip="Column name for sample abundances. Empty = use first numeric column."),
                io.String.Input("extra_args",
                    display_name="Extra arguments",
                    multiline=True, default="",
                    tooltip="Reserved for future use"),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("results_path",
                    tooltip="Alpha diversity results TSV"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, profile_path, output_dir, metric, sample_col, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        results_path = str(out_dir / "alpha_diversity.tsv")

        try:
            counts, samples = _load_abundance_table(profile_path, sample_col)
        except Exception as e:
            return io.NodeOutput(str(out_dir), results_path,
                                 f"ERROR loading profile: {e}")

        results = {}
        for sample, abunds in zip(samples, zip(*counts)):
            abunds = [max(0.0, a) for a in abunds]
            results[sample] = _compute_alpha(abunds, metric)

        with open(results_path, "w") as f:
            f.write(f"sample\t{metric}\n")
            for sample, value in results.items():
                f.write(f"{sample}\t{value:.6f}\n")

        summary = _alpha_summary(results, metric)
        return io.NodeOutput(str(out_dir), results_path, summary)


class Beta_diversity(_Base):
    """Beta diversity (between-sample dissimilarity) from abundance profiles.

    Computes Bray-Curtis or Jaccard dissimilarity matrix and writes
    PCoA coordinates for visualization. Uses scikit-bio when available;
    falls back to NumPy-based implementation.

    Input format (TSV): rows = taxa, columns = samples.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Beta_diversity",
            display_name="beta diversity",
            category="Metagenomics/Diversity",
            inputs=[
                io.String.Input("profile_path",
                    display_name="Abundance profile (TSV)",
                    multiline=False, default="",
                    tooltip="MetaPhlAn profile or Bracken abundance table (multi-sample)"),
                io.String.Input("output_dir",
                    display_name="Output directory",
                    multiline=False, default=""),
                io.Combo.Input("metric",
                    display_name="Dissimilarity metric",
                    options=["bray_curtis", "jaccard", "unifrac"],
                    default="bray_curtis",
                    tooltip="unifrac requires phylogenetic tree (scikit-bio required)"),
                io.String.Input("extra_args",
                    display_name="Extra arguments",
                    multiline=True, default=""),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("distance_matrix_path",
                    tooltip="Pairwise dissimilarity matrix (TSV)"),
                io.String.Output("pcoa_path",
                    tooltip="PCoA coordinates (TSV)"),
                io.String.Output("summary_text"),
            ],
        )

    @classmethod
    def execute(
        cls, profile_path, output_dir, metric, extra_args,
    ) -> io.NodeOutput:
        out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        out_dir.mkdir(parents=True, exist_ok=True)
        dm_path = str(out_dir / "distance_matrix.tsv")
        pcoa_path = str(out_dir / "pcoa_coordinates.tsv")

        try:
            counts, samples = _load_abundance_table(profile_path, "")
        except Exception as e:
            return io.NodeOutput(str(out_dir), dm_path, pcoa_path,
                                 f"ERROR loading profile: {e}")

        if len(samples) < 2:
            return io.NodeOutput(str(out_dir), dm_path, pcoa_path,
                                 "ERROR: Need at least 2 samples for beta diversity.")

        if metric == "unifrac":
            return io.NodeOutput(str(out_dir), dm_path, pcoa_path,
                                 "ERROR: UniFrac requires phylogenetic tree. Use scikit-bio with tree parameter.")

        try:
            dm = _compute_beta(counts, samples, metric)
            _write_distance_matrix(dm, samples, dm_path)
            explained = _compute_pcoa(dm, samples, pcoa_path)
            summary = _beta_summary(samples, metric, explained)
        except Exception as e:
            return io.NodeOutput(str(out_dir), dm_path, pcoa_path,
                                 f"ERROR computing {metric}: {e}")

        return io.NodeOutput(str(out_dir), dm_path, pcoa_path, summary)


# ── helper functions ────────────────────────────────────────────────────────

def _load_abundance_table(
    profile_path: str, sample_col: str
) -> tuple[list[list[float]], list[str]]:
    p = Path(profile_path)
    if not p.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    lines = [l for l in p.read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    if not lines:
        raise ValueError("Empty profile file.")

    header = lines[0].split("\t")
    # Detect numeric columns
    data_rows = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        data_rows.append(parts)

    if sample_col and sample_col in header:
        col_idx = [header.index(sample_col)]
    else:
        col_idx = [i for i in range(1, len(header))
                   if _is_numeric_col(data_rows, i)]

    samples = [header[i] for i in col_idx]
    counts = []
    for parts in data_rows:
        row = []
        for i in col_idx:
            try:
                row.append(float(parts[i]) if i < len(parts) else 0.0)
            except ValueError:
                row.append(0.0)
        counts.append(row)

    return counts, samples


def _is_numeric_col(rows: list, col_idx: int) -> bool:
    numeric = 0
    for parts in rows[:10]:
        if col_idx < len(parts):
            try:
                float(parts[col_idx])
                numeric += 1
            except ValueError:
                pass
    return numeric > 0


def _compute_alpha(abunds: list[float], metric: str) -> float:
    total = sum(abunds)
    if total == 0:
        return 0.0

    if metric == "observed_otus":
        return float(sum(1 for a in abunds if a > 0))

    props = [a / total for a in abunds if a > 0]

    if metric == "shannon":
        return -sum(p * math.log(p) for p in props)

    if metric == "simpson":
        return 1.0 - sum(p * p for p in props)

    if metric == "chao1":
        f1 = sum(1 for a in abunds if a == 1)
        f2 = sum(1 for a in abunds if a == 2)
        s_obs = sum(1 for a in abunds if a > 0)
        if f2 == 0:
            return float(s_obs + f1 * (f1 - 1) / 2)
        return float(s_obs + f1 ** 2 / (2 * f2))

    return 0.0


def _compute_beta(
    counts: list[list[float]], samples: list[str], metric: str
) -> list[list[float]]:
    n = len(samples)
    dm = [[0.0] * n for _ in range(n)]
    # counts is (taxa × samples): transpose to (samples × taxa)
    s_vecs = list(zip(*counts))

    for i in range(n):
        for j in range(i + 1, n):
            u = s_vecs[i]
            v = s_vecs[j]
            if metric == "bray_curtis":
                num = sum(abs(a - b) for a, b in zip(u, v))
                den = sum(a + b for a, b in zip(u, v))
                d = num / den if den > 0 else 0.0
            else:  # jaccard
                shared = sum(1 for a, b in zip(u, v) if a > 0 and b > 0)
                total = sum(1 for a, b in zip(u, v) if a > 0 or b > 0)
                d = 1.0 - (shared / total if total > 0 else 0.0)
            dm[i][j] = d
            dm[j][i] = d
    return dm


def _write_distance_matrix(dm: list[list[float]], samples: list[str],
                            path: str) -> None:
    with open(path, "w") as f:
        f.write("\t" + "\t".join(samples) + "\n")
        for i, row in enumerate(dm):
            f.write(samples[i] + "\t" + "\t".join(f"{v:.6f}" for v in row) + "\n")


def _compute_pcoa(dm: list[list[float]], samples: list[str],
                  pcoa_path: str) -> list[float]:
    try:
        import numpy as np
        n = len(samples)
        D = np.array(dm)
        D2 = D ** 2
        H = np.eye(n) - np.ones((n, n)) / n
        B = -0.5 * H @ D2 @ H
        eigenvalues, eigenvectors = np.linalg.eigh(B)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        positive_mask = eigenvalues > 0
        explained = []
        total_pos = eigenvalues[positive_mask].sum()
        for ev in eigenvalues[:3]:
            explained.append(max(0.0, ev / total_pos * 100) if total_pos > 0 else 0.0)

        with open(pcoa_path, "w") as f:
            n_axes = min(3, sum(positive_mask))
            headers = ["sample"] + [f"PC{i+1}" for i in range(n_axes)]
            f.write("\t".join(headers) + "\n")
            for i, sample in enumerate(samples):
                coords = [str(eigenvectors[i, j] * math.sqrt(max(0, eigenvalues[j])))
                          for j in range(n_axes)]
                f.write(sample + "\t" + "\t".join(coords) + "\n")
        return explained[:3]
    except ImportError:
        with open(pcoa_path, "w") as f:
            f.write("sample\tPC1\tPC2\n")
            for sample in samples:
                f.write(f"{sample}\tN/A\tN/A\n")
        return []


def _alpha_summary(results: dict[str, float], metric: str) -> str:
    values = list(results.values())
    lines = [
        "=== Alpha Diversity Summary ===",
        f"Metric   : {metric}",
        f"Samples  : {len(results)}",
    ]
    if values:
        lines += [
            f"Mean     : {sum(values)/len(values):.4f}",
            f"Min      : {min(values):.4f}",
            f"Max      : {max(values):.4f}",
        ]
    lines.append("\nPer-sample values:")
    for sample, value in results.items():
        lines.append(f"  {sample:<30}  {value:.4f}")
    return "\n".join(lines)


def _beta_summary(samples: list[str], metric: str,
                  explained: list[float]) -> str:
    lines = [
        "=== Beta Diversity Summary ===",
        f"Metric   : {metric}",
        f"Samples  : {len(samples)}",
    ]
    if explained:
        for i, pct in enumerate(explained):
            lines.append(f"PC{i+1} variance explained: {pct:.1f}%")
    lines.append("(Use pcoa_coordinates.tsv for visualization)")
    return "\n".join(lines)
