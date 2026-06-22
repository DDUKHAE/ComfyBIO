from __future__ import annotations
import base64
import pickle
from io import StringIO
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import motifs
from Bio.Seq import Seq


_READ_FORMATS = ["sites", "pfm", "jaspar", "meme", "transfac"]
_WRITE_FORMATS = ["pfm", "jaspar", "transfac"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Motif_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_create",
            display_name="Motif create from instances",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("instances", multiline=True, default="TACAA\nTACGC\nTACCC"),
                io.String.Input("alphabet", multiline=False, default="ACGT"),
            ],
            outputs=[
                io.String.Output("motif"),
                io.Int.Output("length"),
                io.Int.Output("num_instances"),
                io.String.Output("consensus"),
            ],
        )

    @classmethod
    def execute(cls, instances, alphabet) -> io.NodeOutput:
        seqs = [Seq(s.strip()) for s in instances.splitlines() if s.strip()]
        m = motifs.create(seqs, alphabet=alphabet)
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(m)).decode(),
            len(m),
            len(seqs),
            str(m.consensus),
        )


class Motif_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_read",
            display_name="Motif read",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
                io.Combo.Input("format", options=_READ_FORMATS, default="jaspar"),
            ],
            outputs=[
                io.String.Output("motif"),
                io.Int.Output("length"),
                io.String.Output("consensus"),
                io.String.Output("counts"),
            ],
        )

    @classmethod
    def execute(cls, source, source_kind, format) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        m = motifs.read(handle, format)
        if source_kind == "path":
            handle.close()
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(m)).decode(),
            len(m),
            str(m.consensus),
            str(m.counts),
        )


class Motif_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_parse",
            display_name="Motif parse",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
                io.Combo.Input("format", options=_READ_FORMATS, default="jaspar"),
            ],
            outputs=[
                io.String.Output("motifs"),
                io.Int.Output("count"),
                io.String.Output("consensus_list"),
            ],
        )

    @classmethod
    def execute(cls, source, source_kind, format) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        mlist = list(motifs.parse(handle, format))
        if source_kind == "path":
            handle.close()
        consensus_list = "\n".join(str(m.consensus) for m in mlist)
        return io.NodeOutput(base64.b64encode(pickle.dumps(mlist)).decode(), len(mlist), consensus_list)


class Motif_get_motif(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_get_motif",
            display_name="Motif get from list",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("motifs_list", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("motif"),
                io.Int.Output("length"),
                io.String.Output("consensus"),
            ],
        )

    @classmethod
    def execute(cls, motifs_list, index) -> io.NodeOutput:
        mlist = pickle.loads(base64.b64decode(motifs_list))
        m = mlist[index - 1]
        return io.NodeOutput(base64.b64encode(pickle.dumps(m)).decode(), len(m), str(m.consensus))


class Motif_consensus(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_consensus",
            display_name="Motif consensus",
            category="Biopython/Motif",
            inputs=[io.String.Input("motif", multiline=False, default="")],
            outputs=[
                io.String.Output("consensus"),
                io.String.Output("anticonsensus"),
                io.String.Output("degenerate_consensus"),
                io.String.Output("counts_matrix"),
            ],
        )

    @classmethod
    def execute(cls, motif) -> io.NodeOutput:
        m = pickle.loads(base64.b64decode(motif))
        try:
            deg = str(m.degenerate_consensus)
        except Exception:
            deg = ""
        return io.NodeOutput(str(m.consensus), str(m.anticonsensus), deg, str(m.counts))


class Motif_reverse_complement(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_reverse_complement",
            display_name="Motif reverse complement",
            category="Biopython/Motif",
            inputs=[io.String.Input("motif", multiline=False, default="")],
            outputs=[
                io.String.Output("motif"),
                io.String.Output("consensus"),
            ],
        )

    @classmethod
    def execute(cls, motif) -> io.NodeOutput:
        m = pickle.loads(base64.b64decode(motif))
        rc = m.reverse_complement()
        return io.NodeOutput(base64.b64encode(pickle.dumps(rc)).decode(), str(rc.consensus))


class Motif_pssm_scan(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_pssm_scan",
            display_name="Motif PSSM scan",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("motif", multiline=False, default=""),
                io.String.Input("sequence", multiline=False, default="ACGTACGT"),
                io.Float.Input("pseudocount", min=0.0, step=0.1, default=0.5),
            ],
            outputs=[
                io.String.Output("scores"),
                io.Int.Output("hit_count"),
                io.String.Output("best_position"),
            ],
        )

    @classmethod
    def execute(cls, motif, sequence, pseudocount) -> io.NodeOutput:
        m = pickle.loads(base64.b64decode(motif))
        m.pseudocounts = pseudocount
        pssm = m.pssm
        scores = pssm.calculate(sequence)
        score_list = list(scores) if hasattr(scores, "__iter__") else [scores]
        best_pos = score_list.index(max(score_list)) if score_list else 0
        return io.NodeOutput(
            "\n".join("%.4f" % s for s in score_list),
            len(score_list),
            "position %d (score %.4f)" % (best_pos, max(score_list) if score_list else 0),
        )


class Motif_weblogo(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_weblogo",
            display_name="Motif weblogo",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("motif", multiline=False, default=""),
                io.String.Input("output_file", multiline=False, default="motif_logo.png"),
            ],
            outputs=[io.String.Output("file_path")],
        )

    @classmethod
    def execute(cls, motif, output_file) -> io.NodeOutput:
        m = pickle.loads(base64.b64decode(motif))
        m.weblogo(output_file)
        return io.NodeOutput(output_file)


class Motif_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Motif_write",
            display_name="Motif write",
            category="Biopython/Motif",
            inputs=[
                io.String.Input("motif", multiline=False, default=""),
                io.Combo.Input("format", options=_WRITE_FORMATS, default="jaspar"),
            ],
            outputs=[io.String.Output("text")],
        )

    @classmethod
    def execute(cls, motif, format) -> io.NodeOutput:
        m = pickle.loads(base64.b64decode(motif))
        return io.NodeOutput(motifs.write([m], format))


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Motif_create,
            Motif_read,
            Motif_parse,
            Motif_get_motif,
            Motif_consensus,
            Motif_reverse_complement,
            Motif_pssm_scan,
            Motif_weblogo,
            Motif_write,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
