from __future__ import annotations
import base64
import pickle
from io import StringIO
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import Align

_FORMATS = ["fasta", "clustal", "stockholm", "phylip", "maf", "psl", "sam", "nexus", "emboss", "a2m"]
_WRITE_FORMATS = ["fasta", "clustal", "stockholm", "phylip", "maf", "psl", "sam", "nexus", "a2m"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Align_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_read",
            display_name="Align read",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
                io.Combo.Input("format", options=_FORMATS, default="clustal"),
            ],
            outputs=[
                io.String.Output("alignment"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, source, source_kind, format) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        aln = Align.read(handle, format)
        if source_kind == "path":
            handle.close()
        return io.NodeOutput(base64.b64encode(pickle.dumps(aln)).decode(), str(aln))


class Align_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_parse",
            display_name="Align parse",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.Combo.Input("format", options=_FORMATS, default="maf"),
            ],
            outputs=[
                io.String.Output("alignments"),
                io.Int.Output("count"),
            ],
        )

    @classmethod
    def execute(cls, file_path, format) -> io.NodeOutput:
        alns = list(Align.parse(file_path, format))
        return io.NodeOutput(base64.b64encode(pickle.dumps(alns)).decode(), len(alns))


class Align_get_item(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_get_item",
            display_name="Align get item",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("alignments", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("alignment"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, alignments, index) -> io.NodeOutput:
        aln = pickle.loads(base64.b64decode(alignments))[index - 1]
        return io.NodeOutput(base64.b64encode(pickle.dumps(aln)).decode(), str(aln))


class Align_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_write",
            display_name="Align write",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("alignments", multiline=False, default=""),
                io.String.Input("file_path", multiline=False, default="output.aln"),
                io.Combo.Input("format", options=_WRITE_FORMATS, default="clustal"),
            ],
            outputs=[
                io.Int.Output("count"),
                io.String.Output("file_path"),
            ],
        )

    @classmethod
    def execute(cls, alignments, file_path, format) -> io.NodeOutput:
        data = pickle.loads(base64.b64decode(alignments))
        items = data if isinstance(data, list) else [data]
        return io.NodeOutput(Align.write(items, file_path, format), file_path)


class Align_summary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_summary",
            display_name="Align summary",
            category="Biopython/Alignment",
            inputs=[io.String.Input("alignment", multiline=False, default="")],
            outputs=[
                io.String.Output("summary"),
                io.Int.Output("rows"),
                io.Int.Output("columns"),
            ],
        )

    @classmethod
    def execute(cls, alignment) -> io.NodeOutput:
        aln = pickle.loads(base64.b64decode(alignment))
        rows, cols = aln.shape
        return io.NodeOutput(str(aln), rows, cols)


class Align_counts(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_counts",
            display_name="Align counts",
            category="Biopython/Alignment",
            inputs=[io.String.Input("alignment", multiline=False, default="")],
            outputs=[
                io.Int.Output("identities"),
                io.Int.Output("mismatches"),
                io.Int.Output("gaps"),
                io.Int.Output("aligned"),
                io.String.Output("detail"),
            ],
        )

    @classmethod
    def execute(cls, alignment) -> io.NodeOutput:
        c = pickle.loads(base64.b64decode(alignment)).counts()
        return io.NodeOutput(c.identities, c.mismatches, c.gaps, c.aligned, str(c))


class Align_get_row(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_get_row",
            display_name="Align get row",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("alignment", multiline=False, default=""),
                io.Int.Input("row", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, alignment, row) -> io.NodeOutput:
        return io.NodeOutput(pickle.loads(base64.b64decode(alignment))[row - 1])


class Align_format(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_format",
            display_name="Align format",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("alignment", multiline=False, default=""),
                io.Combo.Input("format", options=_WRITE_FORMATS, default="fasta"),
            ],
            outputs=[io.String.Output("text")],
        )

    @classmethod
    def execute(cls, alignment, format) -> io.NodeOutput:
        return io.NodeOutput(pickle.loads(base64.b64decode(alignment)).format(format))


class Align_slice(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_slice",
            display_name="Align slice columns",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("alignment", multiline=False, default=""),
                io.Int.Input("start", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("end", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("alignment"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, alignment, start, end) -> io.NodeOutput:
        aln = pickle.loads(base64.b64decode(alignment))
        sliced = aln[:, start:end] if end > 0 else aln[:, start:]
        return io.NodeOutput(base64.b64encode(pickle.dumps(sliced)).decode(), str(sliced))


class Align_sort(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_sort",
            display_name="Align sort",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("alignment", multiline=False, default=""),
                io.Boolean.Input("reverse", default=False),
            ],
            outputs=[
                io.String.Output("alignment"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, alignment, reverse) -> io.NodeOutput:
        aln = pickle.loads(base64.b64decode(alignment))
        aln.sort(reverse=reverse)
        return io.NodeOutput(base64.b64encode(pickle.dumps(aln)).decode(), str(aln))


class Align_convert(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Align_convert",
            display_name="Align convert",
            category="Biopython/Alignment",
            inputs=[
                io.String.Input("input_path", multiline=False, default=""),
                io.Combo.Input("input_format", options=_FORMATS, default="stockholm"),
                io.String.Input("output_path", multiline=False, default=""),
                io.Combo.Input("output_format", options=_WRITE_FORMATS, default="fasta"),
            ],
            outputs=[
                io.Int.Output("count"),
                io.String.Output("output_path"),
            ],
        )

    @classmethod
    def execute(cls, input_path, input_format, output_path, output_format) -> io.NodeOutput:
        alns = list(Align.parse(input_path, input_format))
        count = Align.write(alns, output_path, output_format)
        return io.NodeOutput(count, output_path)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Align_read, Align_parse, Align_get_item, Align_write,
            Align_summary, Align_counts, Align_get_row, Align_format,
            Align_slice, Align_sort, Align_convert,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
