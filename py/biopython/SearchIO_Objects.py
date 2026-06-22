from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import SearchIO


_FORMATS = ["blast-xml", "blast-tab", "blat-psl", "hmmer3-tab", "hmmer3-text", "fasta-m10", "exonerate-text"]
_WRITE_FORMATS = ["blast-tab", "blat-psl", "hmmer3-tab"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class SearchIO_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_read",
            display_name="SearchIO read",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.Combo.Input("format", options=_FORMATS, default="blast-xml"),
            ],
            outputs=[
                io.String.Output("qresult"),
                io.String.Output("query_id"),
                io.Int.Output("hit_count"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, file_path, format) -> io.NodeOutput:
        qr = SearchIO.read(file_path, format)
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(qr)).decode(),
            qr.id,
            len(qr),
            str(qr),
        )


class SearchIO_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_parse",
            display_name="SearchIO parse",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.Combo.Input("format", options=_FORMATS, default="blast-xml"),
            ],
            outputs=[
                io.String.Output("qresults"),
                io.Int.Output("count"),
                io.String.Output("query_ids"),
            ],
        )

    @classmethod
    def execute(cls, file_path, format) -> io.NodeOutput:
        qrs = list(SearchIO.parse(file_path, format))
        ids = "\n".join(q.id for q in qrs)
        return io.NodeOutput(base64.b64encode(pickle.dumps(qrs)).decode(), len(qrs), ids)


class SearchIO_get_qresult(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_get_qresult",
            display_name="SearchIO get query result",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("qresults", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("qresult"), io.String.Output("query_id"), io.Int.Output("hit_count")],
        )

    @classmethod
    def execute(cls, qresults, index) -> io.NodeOutput:
        qr = pickle.loads(base64.b64decode(qresults))[index - 1]
        return io.NodeOutput(base64.b64encode(pickle.dumps(qr)).decode(), qr.id, len(qr))


class SearchIO_hit_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_hit_info",
            display_name="SearchIO hit info",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("qresult", multiline=False, default=""),
                io.Int.Input("hit_index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("hit_id"),
                io.String.Output("description"),
                io.Int.Output("hsp_count"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, qresult, hit_index) -> io.NodeOutput:
        qr = pickle.loads(base64.b64decode(qresult))
        hit = qr[hit_index - 1]
        return io.NodeOutput(hit.id, hit.description, len(hit), str(hit))


class SearchIO_hsp_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_hsp_info",
            display_name="SearchIO HSP info",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("qresult", multiline=False, default=""),
                io.Int.Input("hit_index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
                io.Int.Input("hsp_index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("query_range"),
                io.String.Output("hit_range"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, qresult, hit_index, hsp_index) -> io.NodeOutput:
        qr = pickle.loads(base64.b64decode(qresult))
        hsp = qr[hit_index - 1][hsp_index - 1]
        return io.NodeOutput(
            str(hsp.query_range),
            str(hsp.hit_range),
            str(hsp),
        )


class SearchIO_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_write",
            display_name="SearchIO write",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("qresults", multiline=False, default=""),
                io.String.Input("file_path", multiline=False, default="output.tab"),
                io.Combo.Input("format", options=_WRITE_FORMATS, default="blast-tab"),
            ],
            outputs=[io.String.Output("counts"), io.String.Output("file_path")],
        )

    @classmethod
    def execute(cls, qresults, file_path, format) -> io.NodeOutput:
        data = pickle.loads(base64.b64decode(qresults))
        items = data if isinstance(data, list) else [data]
        counts = SearchIO.write(items, file_path, format)
        return io.NodeOutput(str(counts), file_path)


class SearchIO_convert(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SearchIO_convert",
            display_name="SearchIO convert",
            category="Biopython/SearchIO",
            inputs=[
                io.String.Input("input_path", multiline=False, default=""),
                io.Combo.Input("input_format", options=_FORMATS, default="blast-xml"),
                io.String.Input("output_path", multiline=False, default=""),
                io.Combo.Input("output_format", options=_WRITE_FORMATS, default="blast-tab"),
            ],
            outputs=[io.String.Output("counts"), io.String.Output("output_path")],
        )

    @classmethod
    def execute(cls, input_path, input_format, output_path, output_format) -> io.NodeOutput:
        counts = SearchIO.convert(input_path, input_format, output_path, output_format)
        return io.NodeOutput(str(counts), output_path)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            SearchIO_read,
            SearchIO_parse,
            SearchIO_get_qresult,
            SearchIO_hit_info,
            SearchIO_hsp_info,
            SearchIO_write,
            SearchIO_convert,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
