from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import Cluster
import numpy as np


_DIST = ["e", "b", "c", "a", "u", "x", "s", "k"]
_DIST_LABELS = ["euclidean", "city-block", "pearson", "abs-pearson", "uncentered", "abs-uncentered", "spearman", "kendall"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Cluster_load_data(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_load_data",
            display_name="Cluster load data (CSV)",
            category="Biopython/Cluster",
            inputs=[
                io.String.Input("csv_text", multiline=True, default="1.0,2.0,3.0\n4.0,5.0,6.0\n7.0,8.0,9.0"),
                io.String.Input("separator", multiline=False, default=","),
            ],
            outputs=[
                io.String.Output("data"),
                io.Int.Output("rows"),
                io.Int.Output("cols"),
            ],
        )

    @classmethod
    def execute(cls, csv_text, separator) -> io.NodeOutput:
        rows = []
        for line in csv_text.strip().splitlines():
            if line.strip():
                rows.append([float(x) for x in line.split(separator)])
        data = np.array(rows)
        return io.NodeOutput(base64.b64encode(pickle.dumps(data)).decode(), data.shape[0], data.shape[1])


class Cluster_distance_matrix(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_distance_matrix",
            display_name="Cluster distance matrix",
            category="Biopython/Cluster",
            inputs=[
                io.String.Input("data", multiline=False, default=""),
                io.Combo.Input("dist", options=_DIST_LABELS, default="pearson"),
                io.Boolean.Input("transpose", default=False),
            ],
            outputs=[
                io.String.Output("matrix"),
                io.String.Output("matrix_preview"),
            ],
        )

    @classmethod
    def execute(cls, data, dist, transpose) -> io.NodeOutput:
        d = pickle.loads(base64.b64decode(data))
        dist_char = _DIST[_DIST_LABELS.index(dist)]
        matrix = Cluster.distancematrix(d, dist=dist_char, transpose=int(transpose))
        preview_lines = []
        for i, row in enumerate(matrix[:5]):
            preview_lines.append("Row%d: %s" % (i, " ".join("%.4f" % v for v in (row or []))))
        return io.NodeOutput(base64.b64encode(pickle.dumps(matrix)).decode(), "\n".join(preview_lines))


class Cluster_hierarchical(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_hierarchical",
            display_name="Cluster hierarchical",
            category="Biopython/Cluster",
            inputs=[
                io.String.Input("data", multiline=False, default=""),
                io.Combo.Input("method", options=["s", "m", "a", "c"], default="m"),
                io.Combo.Input("dist", options=_DIST_LABELS, default="pearson"),
                io.Boolean.Input("transpose", default=False),
            ],
            outputs=[
                io.String.Output("tree"),
                io.String.Output("tree_summary"),
            ],
        )

    @classmethod
    def execute(cls, data, method, dist, transpose) -> io.NodeOutput:
        d = pickle.loads(base64.b64decode(data))
        dist_char = _DIST[_DIST_LABELS.index(dist)]
        tree = Cluster.treecluster(d, method=method, dist=dist_char, transpose=int(transpose))
        lines = ["Node %d: left=%d, right=%d, dist=%.4f" % (i, n.left, n.right, n.distance) for i, n in enumerate(tree)]
        return io.NodeOutput(base64.b64encode(pickle.dumps(tree)).decode(), "\n".join(lines[:20]))


class Cluster_kcluster(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_kcluster",
            display_name="Cluster k-means",
            category="Biopython/Cluster",
            inputs=[
                io.String.Input("data", multiline=False, default=""),
                io.Int.Input("nclusters", min=2, step=1, default=3, display_mode=io.NumberDisplay.number),
                io.Int.Input("npass", min=1, step=1, default=10, display_mode=io.NumberDisplay.number),
                io.Combo.Input("dist", options=_DIST_LABELS, default="euclidean"),
                io.Boolean.Input("transpose", default=False),
            ],
            outputs=[
                io.String.Output("cluster_ids"),
                io.Float.Output("error"),
                io.Int.Output("nfound"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, data, nclusters, npass, dist, transpose) -> io.NodeOutput:
        d = pickle.loads(base64.b64decode(data))
        dist_char = _DIST[_DIST_LABELS.index(dist)]
        clusterid, error, nfound = Cluster.kcluster(
            d, nclusters=nclusters, npass=npass, dist=dist_char, transpose=int(transpose)
        )
        summary = "Cluster assignments: " + ", ".join(str(c) for c in clusterid)
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(clusterid)).decode(),
            float(error),
            int(nfound),
            summary,
        )


class Cluster_kmedoids(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_kmedoids",
            display_name="Cluster k-medoids",
            category="Biopython/Cluster",
            inputs=[
                io.String.Input("distance_matrix", multiline=False, default=""),
                io.Int.Input("nclusters", min=2, step=1, default=3, display_mode=io.NumberDisplay.number),
                io.Int.Input("npass", min=1, step=1, default=10, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("cluster_ids"),
                io.Float.Output("error"),
                io.Int.Output("nfound"),
            ],
        )

    @classmethod
    def execute(cls, distance_matrix, nclusters, npass) -> io.NodeOutput:
        matrix = pickle.loads(base64.b64decode(distance_matrix))
        clusterid, error, nfound = Cluster.kmedoids(matrix, nclusters=nclusters, npass=npass)
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(clusterid)).decode(),
            float(error),
            int(nfound),
        )


class Cluster_pca(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_pca",
            display_name="Cluster PCA",
            category="Biopython/Cluster",
            inputs=[io.String.Input("data", multiline=False, default="")],
            outputs=[
                io.String.Output("coordinates"),
                io.String.Output("eigenvalues"),
                io.String.Output("mean"),
            ],
        )

    @classmethod
    def execute(cls, data) -> io.NodeOutput:
        d = pickle.loads(base64.b64decode(data))
        mean, coordinates, components, eigenvalues = Cluster.pca(d)
        eig_str = " ".join("%.4f" % v for v in eigenvalues)
        mean_str = " ".join("%.4f" % v for v in mean)
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(coordinates)).decode(),
            eig_str,
            mean_str,
        )


class Cluster_som(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Cluster_som",
            display_name="Cluster SOM",
            category="Biopython/Cluster",
            inputs=[
                io.String.Input("data", multiline=False, default=""),
                io.Int.Input("nxgrid", min=1, step=1, default=2, display_mode=io.NumberDisplay.number),
                io.Int.Input("nygrid", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
                io.Int.Input("niter", min=100, step=100, default=1000, display_mode=io.NumberDisplay.number),
                io.Combo.Input("dist", options=_DIST_LABELS, default="euclidean"),
            ],
            outputs=[
                io.String.Output("cluster_ids"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, data, nxgrid, nygrid, niter, dist) -> io.NodeOutput:
        d = pickle.loads(base64.b64decode(data))
        dist_char = _DIST[_DIST_LABELS.index(dist)]
        clusterid, celldata = Cluster.somcluster(d, nxgrid=nxgrid, nygrid=nygrid, niter=niter, dist=dist_char)
        summary = "\n".join("Row%d -> cell(%d,%d)" % (i, c[0], c[1]) for i, c in enumerate(clusterid))
        return io.NodeOutput(base64.b64encode(pickle.dumps(clusterid)).decode(), summary)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Cluster_load_data,
            Cluster_distance_matrix,
            Cluster_hierarchical,
            Cluster_kcluster,
            Cluster_kmedoids,
            Cluster_pca,
            Cluster_som,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
