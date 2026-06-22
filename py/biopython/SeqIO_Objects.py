from __future__ import annotations
import base64
import pickle
from io import StringIO
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import SeqIO
from Bio.SeqIO.FastaIO import SimpleFastaParser
from Bio.SeqIO.QualityIO import FastqGeneralIterator

_PARSE_FORMATS = ["fasta", "genbank", "embl", "swiss", "fastq", "tab"]
_WRITE_FORMATS = ["fasta", "genbank", "embl", "fastq", "tab"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class SeqIO_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_parse",
            display_name="SeqIO parse",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
                io.Combo.Input("format", options=_PARSE_FORMATS, default="fasta"),
            ],
            outputs=[
                io.String.Output("records"),
                io.Int.Output("count"),
                io.String.Output("ids"),
            ],
        )

    @classmethod
    def execute(cls, source, source_kind, format) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        records = list(SeqIO.parse(handle, format))
        if source_kind == "path":
            handle.close()
        ids = "\n".join(r.id for r in records)
        return io.NodeOutput(base64.b64encode(pickle.dumps(records)).decode(), len(records), ids)


class SeqIO_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_write",
            display_name="SeqIO write",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("records", multiline=False, default=""),
                io.String.Input("file_path", multiline=False, default="output.fasta"),
                io.Combo.Input("format", options=_WRITE_FORMATS, default="fasta"),
            ],
            outputs=[
                io.Int.Output("count"),
                io.String.Output("file_path"),
            ],
        )

    @classmethod
    def execute(cls, records, file_path, format) -> io.NodeOutput:
        recs = pickle.loads(base64.b64decode(records))
        count = SeqIO.write(recs, file_path, format)
        return io.NodeOutput(count, file_path)


class SeqIO_convert(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_convert",
            display_name="SeqIO convert",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("input_path", multiline=False, default=""),
                io.Combo.Input("input_format", options=_PARSE_FORMATS, default="genbank"),
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
        count = SeqIO.convert(input_path, input_format, output_path, output_format)
        return io.NodeOutput(count, output_path)


class SeqIO_get_record(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_get_record",
            display_name="SeqIO get record",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("records", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, records, index) -> io.NodeOutput:
        recs = pickle.loads(base64.b64decode(records))
        return io.NodeOutput(base64.b64encode(pickle.dumps(recs[index - 1])).decode())


class SeqIO_filter_records(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_filter_records",
            display_name="SeqIO filter records",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("records", multiline=False, default=""),
                io.Int.Input("min_length", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("max_length", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("records"),
                io.Int.Output("count"),
            ],
        )

    @classmethod
    def execute(cls, records, min_length, max_length) -> io.NodeOutput:
        recs = pickle.loads(base64.b64decode(records))
        filtered = [r for r in recs if len(r) >= min_length and (max_length == 0 or len(r) <= max_length)]
        return io.NodeOutput(base64.b64encode(pickle.dumps(filtered)).decode(), len(filtered))


class SeqIO_records_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_records_info",
            display_name="SeqIO records info",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("records", multiline=False, default=""),
                io.Combo.Input("info_type", options=["ids", "lengths", "descriptions", "organisms", "summary"], default="summary"),
            ],
            outputs=[io.String.Output("info")],
        )

    @classmethod
    def execute(cls, records, info_type) -> io.NodeOutput:
        recs = pickle.loads(base64.b64decode(records))
        if info_type == "ids":
            result = "\n".join(r.id for r in recs)
        elif info_type == "lengths":
            result = "\n".join(f"{r.id}: {len(r)}" for r in recs)
        elif info_type == "descriptions":
            result = "\n".join(f"{r.id}: {r.description}" for r in recs)
        elif info_type == "organisms":
            result = "\n".join(f"{r.id}: {r.annotations.get('organism', 'N/A')}" for r in recs)
        else:
            result = f"count={len(recs)}\n" + "\n".join(f"{r.id} len={len(r)}" for r in recs)
        return io.NodeOutput(result)


class SeqIO_lookup_by_id(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqIO_lookup_by_id",
            display_name="SeqIO lookup by ID",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("records", multiline=False, default=""),
                io.String.Input("record_id", multiline=False, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, records, record_id) -> io.NodeOutput:
        recs = pickle.loads(base64.b64decode(records))
        d = SeqIO.to_dict(recs)
        return io.NodeOutput(base64.b64encode(pickle.dumps(d[record_id])).decode())


class SimpleFastaParser_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SimpleFastaParser_parse",
            display_name="Simple FASTA parser",
            category="Biopython/SeqIO",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
            ],
            outputs=[
                io.Int.Output("count"),
                io.Int.Output("total_length"),
                io.String.Output("titles"),
                io.String.Output("sequences"),
            ],
        )

    @classmethod
    def execute(cls, source, source_kind) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        titles_list, seqs_list = [], []
        for title, seq in SimpleFastaParser(handle):
            titles_list.append(title)
            seqs_list.append(seq)
        if source_kind == "path":
            handle.close()
        return io.NodeOutput(len(titles_list), sum(len(s) for s in seqs_list), "\n".join(titles_list), "\n".join(seqs_list))


class FastqGeneralIterator_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FastqGeneralIterator_parse",
            display_name="FASTQ general iterator",
            category="Biopython/SeqIO",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.Int.Output("count"),
                io.Int.Output("total_length"),
                io.String.Output("titles"),
                io.String.Output("sequences"),
                io.String.Output("qualities"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        titles_list, seqs_list, quals_list = [], [], []
        with open(file_path) as handle:
            for title, seq, qual in FastqGeneralIterator(handle):
                titles_list.append(title)
                seqs_list.append(seq)
                quals_list.append(qual)
        return io.NodeOutput(
            len(titles_list), sum(len(s) for s in seqs_list),
            "\n".join(titles_list), "\n".join(seqs_list), "\n".join(quals_list),
        )


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            SeqIO_parse, SeqIO_write, SeqIO_convert, SeqIO_get_record,
            SeqIO_filter_records, SeqIO_records_info, SeqIO_lookup_by_id,
            SimpleFastaParser_parse, FastqGeneralIterator_parse,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
