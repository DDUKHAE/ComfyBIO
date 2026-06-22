from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import Blast


_PROGRAMS = ["blastn", "blastp", "blastx", "tblastn", "tblastx"]
_DATABASES = ["nt", "nr", "refseq_rna", "refseq_protein", "swissprot", "pdb"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class BLAST_qblast(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_qblast",
            display_name="BLAST qblast",
            category="Biopython/BLAST",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("program", options=_PROGRAMS, default="blastn"),
                io.Combo.Input("database", options=_DATABASES, default="nt"),
                io.String.Input("query", multiline=True, default=""),
                io.String.Input("output_file", multiline=False, default="blast_result.xml"),
                io.Float.Input("expect", min=0.0, step=0.01, default=10.0),
            ],
            outputs=[io.String.Output("file_path"), io.Int.Output("bytes_written")],
        )

    @classmethod
    def execute(cls, email, program, database, query, output_file, expect) -> io.NodeOutput:
        Blast.email = email
        result_stream = Blast.qblast(program, database, query.strip(), expect=expect)
        data = result_stream.read()
        result_stream.close()
        with open(output_file, "wb") as f:
            f.write(data)
        return io.NodeOutput(output_file, len(data))


class BLAST_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_read",
            display_name="BLAST read",
            category="Biopython/BLAST",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("record"),
                io.String.Output("query_id"),
                io.Int.Output("hit_count"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        rec = Blast.read(file_path)
        encoded = base64.b64encode(pickle.dumps(rec)).decode()
        query_id = rec.query.id if rec.query else ""
        return io.NodeOutput(encoded, query_id, len(rec), str(rec))


class BLAST_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_parse",
            display_name="BLAST parse",
            category="Biopython/BLAST",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("records"),
                io.Int.Output("count"),
                io.String.Output("program"),
                io.String.Output("database"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        blast_records = Blast.parse(file_path)
        recs = list(blast_records)
        return io.NodeOutput(
            base64.b64encode(pickle.dumps(recs)).decode(),
            len(recs),
            getattr(blast_records, "program", ""),
            getattr(blast_records, "db", ""),
        )


class BLAST_get_record(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_get_record",
            display_name="BLAST get record",
            category="Biopython/BLAST",
            inputs=[
                io.String.Input("records", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("record"), io.String.Output("query_id"), io.Int.Output("hit_count")],
        )

    @classmethod
    def execute(cls, records, index) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(records))[index - 1]
        return io.NodeOutput(base64.b64encode(pickle.dumps(rec)).decode(), rec.query.id if rec.query else "", len(rec))


class BLAST_hit_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_hit_info",
            display_name="BLAST hit info",
            category="Biopython/BLAST",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Int.Input("hit_index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("target_id"),
                io.String.Output("description"),
                io.Int.Output("alignment_count"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, record, hit_index) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        hit = rec[hit_index - 1]
        target = hit.target
        return io.NodeOutput(target.id, target.description, len(hit), str(hit))


class BLAST_hsp_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_hsp_info",
            display_name="BLAST HSP info",
            category="Biopython/BLAST",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Int.Input("hit_index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
                io.Int.Input("hsp_index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.Float.Output("evalue"),
                io.Float.Output("bitscore"),
                io.Float.Output("score"),
                io.String.Output("alignment_text"),
            ],
        )

    @classmethod
    def execute(cls, record, hit_index, hsp_index) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        hsp = rec[hit_index - 1][hsp_index - 1]
        ann = hsp.annotations
        return io.NodeOutput(
            ann.get("evalue", 0.0),
            ann.get("bit score", 0.0),
            hsp.score,
            str(hsp),
        )


class BLAST_filter_evalue(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="BLAST_filter_evalue",
            display_name="BLAST filter by E-value",
            category="Biopython/BLAST",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Float.Input("max_evalue", min=0.0, step=0.001, default=0.001),
            ],
            outputs=[
                io.String.Output("record"),
                io.Int.Output("hit_count"),
                io.String.Output("hit_ids"),
            ],
        )

    @classmethod
    def execute(cls, record, max_evalue) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        filtered = [h for h in rec if any(a.annotations.get("evalue", 1e9) <= max_evalue for a in h)]
        ids = "\n".join(h.target.id for h in filtered)
        import copy
        new_rec = copy.copy(rec)
        new_rec[:] = filtered
        return io.NodeOutput(base64.b64encode(pickle.dumps(new_rec)).decode(), len(filtered), ids)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            BLAST_qblast,
            BLAST_read,
            BLAST_parse,
            BLAST_get_record,
            BLAST_hit_info,
            BLAST_hsp_info,
            BLAST_filter_evalue,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
