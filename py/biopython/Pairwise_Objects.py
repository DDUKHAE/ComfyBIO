from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import Align
from Bio.Align import substitution_matrices


_MODES = ["global", "local", "fogsaa"]
_MATRICES = ["BLOSUM62", "BLOSUM45", "BLOSUM80", "PAM250", "PAM30", "NUC.4.4"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Pairwise_align(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Pairwise_align",
            display_name="Pairwise align",
            category="Biopython/Pairwise",
            inputs=[
                io.String.Input("target", multiline=False, default="GAACTTT"),
                io.String.Input("query", multiline=False, default="GATTT"),
                io.Combo.Input("mode", options=_MODES, default="global"),
                io.Float.Input("match_score", min=-100.0, step=0.5, default=1.0),
                io.Float.Input("mismatch_score", min=-100.0, step=0.5, default=0.0),
                io.Float.Input("open_gap_score", min=-100.0, step=0.5, default=-1.0),
                io.Float.Input("extend_gap_score", min=-100.0, step=0.5, default=-1.0),
            ],
            outputs=[
                io.String.Output("alignments"),
                io.Int.Output("count"),
                io.Float.Output("score"),
                io.String.Output("best_alignment"),
            ],
        )

    @classmethod
    def execute(cls, target, query, mode, match_score, mismatch_score, open_gap_score, extend_gap_score) -> io.NodeOutput:
        aligner = Align.PairwiseAligner(
            mode=mode,
            match_score=match_score,
            mismatch_score=mismatch_score,
            open_gap_score=open_gap_score,
            extend_gap_score=extend_gap_score,
        )
        alns = aligner.align(target, query)
        aln_list = list(alns)
        best = str(aln_list[0]) if aln_list else ""
        score = aln_list[0].score if aln_list else 0.0
        return io.NodeOutput(base64.b64encode(pickle.dumps(aln_list)).decode(), len(aln_list), score, best)


class Pairwise_align_matrix(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Pairwise_align_matrix",
            display_name="Pairwise align (substitution matrix)",
            category="Biopython/Pairwise",
            inputs=[
                io.String.Input("target", multiline=False, default=""),
                io.String.Input("query", multiline=False, default=""),
                io.Combo.Input("mode", options=_MODES, default="global"),
                io.Combo.Input("matrix", options=_MATRICES, default="BLOSUM62"),
                io.Float.Input("open_gap_score", min=-100.0, step=0.5, default=-10.0),
                io.Float.Input("extend_gap_score", min=-100.0, step=0.5, default=-0.5),
            ],
            outputs=[
                io.String.Output("alignments"),
                io.Int.Output("count"),
                io.Float.Output("score"),
                io.String.Output("best_alignment"),
            ],
        )

    @classmethod
    def execute(cls, target, query, mode, matrix, open_gap_score, extend_gap_score) -> io.NodeOutput:
        aligner = Align.PairwiseAligner(mode=mode, open_gap_score=open_gap_score, extend_gap_score=extend_gap_score)
        aligner.substitution_matrix = substitution_matrices.load(matrix)
        aln_list = list(aligner.align(target, query))
        best = str(aln_list[0]) if aln_list else ""
        score = aln_list[0].score if aln_list else 0.0
        return io.NodeOutput(base64.b64encode(pickle.dumps(aln_list)).decode(), len(aln_list), score, best)


class Pairwise_score(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Pairwise_score",
            display_name="Pairwise score",
            category="Biopython/Pairwise",
            inputs=[
                io.String.Input("target", multiline=False, default=""),
                io.String.Input("query", multiline=False, default=""),
                io.Combo.Input("mode", options=_MODES, default="global"),
                io.Float.Input("match_score", min=-100.0, step=0.5, default=1.0),
                io.Float.Input("mismatch_score", min=-100.0, step=0.5, default=0.0),
                io.Float.Input("open_gap_score", min=-100.0, step=0.5, default=-1.0),
                io.Float.Input("extend_gap_score", min=-100.0, step=0.5, default=-1.0),
            ],
            outputs=[io.Float.Output("score")],
        )

    @classmethod
    def execute(cls, target, query, mode, match_score, mismatch_score, open_gap_score, extend_gap_score) -> io.NodeOutput:
        aligner = Align.PairwiseAligner(
            mode=mode,
            match_score=match_score,
            mismatch_score=mismatch_score,
            open_gap_score=open_gap_score,
            extend_gap_score=extend_gap_score,
        )
        return io.NodeOutput(aligner.score(target, query))


class Pairwise_get_alignment(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Pairwise_get_alignment",
            display_name="Pairwise get alignment",
            category="Biopython/Pairwise",
            inputs=[
                io.String.Input("alignments", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("alignment"),
                io.String.Output("text"),
                io.Float.Output("score"),
                io.Int.Output("length"),
                io.String.Output("target_seq"),
                io.String.Output("query_seq"),
            ],
        )

    @classmethod
    def execute(cls, alignments, index) -> io.NodeOutput:
        aln = pickle.loads(base64.b64decode(alignments))[index - 1]
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(aln)).decode(),
            str(aln),
            aln.score,
            aln.length,
            aln[0],
            aln[1],
        )


class Pairwise_aligner_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Pairwise_aligner_info",
            display_name="Pairwise aligner info",
            category="Biopython/Pairwise",
            inputs=[
                io.Combo.Input("mode", options=_MODES, default="global"),
                io.Float.Input("match_score", min=-100.0, step=0.5, default=1.0),
                io.Float.Input("mismatch_score", min=-100.0, step=0.5, default=0.0),
                io.Float.Input("open_gap_score", min=-100.0, step=0.5, default=-1.0),
                io.Float.Input("extend_gap_score", min=-100.0, step=0.5, default=-1.0),
            ],
            outputs=[io.String.Output("aligner_info")],
        )

    @classmethod
    def execute(cls, mode, match_score, mismatch_score, open_gap_score, extend_gap_score) -> io.NodeOutput:
        aligner = Align.PairwiseAligner(
            mode=mode,
            match_score=match_score,
            mismatch_score=mismatch_score,
            open_gap_score=open_gap_score,
            extend_gap_score=extend_gap_score,
        )
        return io.NodeOutput(str(aligner))


class Substitution_matrix_load(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Substitution_matrix_load",
            display_name="Substitution matrix load",
            category="Biopython/Pairwise",
            inputs=[io.Combo.Input("matrix", options=_MATRICES, default="BLOSUM62")],
            outputs=[io.String.Output("matrix_info")],
        )

    @classmethod
    def execute(cls, matrix) -> io.NodeOutput:
        mat = substitution_matrices.load(matrix)
        return io.NodeOutput(str(mat))


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Pairwise_align,
            Pairwise_align_matrix,
            Pairwise_score,
            Pairwise_get_alignment,
            Pairwise_aligner_info,
            Substitution_matrix_load,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
