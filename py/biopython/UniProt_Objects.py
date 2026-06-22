from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import SwissProt, ExPASy, UniProt
from Bio.ExPASy import Prosite, Prodoc, Enzyme as ExEnzyme


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class SwissProt_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SwissProt_read",
            display_name="SwissProt read",
            category="Biopython/UniProt",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("record"),
                io.String.Output("entry_name"),
                io.String.Output("description"),
                io.String.Output("organism"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            rec = SwissProt.read(f)
        encoded = base64.b64encode(pickle.dumps(rec)).decode()
        return io.NodeOutput(encoded, rec.entry_name, rec.description, rec.organism)


class SwissProt_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SwissProt_parse",
            display_name="SwissProt parse",
            category="Biopython/UniProt",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("records"),
                io.Int.Output("count"),
                io.String.Output("entry_names"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            recs = list(SwissProt.parse(f))
        names = "\n".join(r.entry_name for r in recs)
        return io.NodeOutput(base64.b64encode(pickle.dumps(recs)).decode(), len(recs), names)


class SwissProt_record_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SwissProt_record_info",
            display_name="SwissProt record info",
            category="Biopython/UniProt",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Combo.Input("info_type", options=["description", "organism", "keywords", "accessions", "organism_classification", "references"], default="description"),
            ],
            outputs=[io.String.Output("info")],
        )

    @classmethod
    def execute(cls, record, info_type) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        val = getattr(rec, info_type)
        if isinstance(val, list):
            result = "\n".join(str(v) for v in val)
        else:
            result = str(val)
        return io.NodeOutput(result)


class ExPASy_get_sprot(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ExPASy_get_sprot",
            display_name="ExPASy get SwissProt",
            category="Biopython/UniProt",
            inputs=[io.String.Input("accession", multiline=False, default="O23729")],
            outputs=[
                io.String.Output("record"),
                io.String.Output("entry_name"),
                io.String.Output("description"),
            ],
        )

    @classmethod
    def execute(cls, accession) -> io.NodeOutput:
        handle = ExPASy.get_sprot_raw(accession)
        rec = SwissProt.read(handle)
        encoded = base64.b64encode(pickle.dumps(rec)).decode()
        return io.NodeOutput(encoded, rec.entry_name, rec.description)


class UniProt_search(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="UniProt_search",
            display_name="UniProt search",
            category="Biopython/UniProt",
            inputs=[
                io.String.Input("query", multiline=False, default="Insulin AND (reviewed:true)"),
                io.Int.Input("max_results", min=1, step=10, default=50, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("results"),
                io.Int.Output("count"),
                io.String.Output("ids"),
            ],
        )

    @classmethod
    def execute(cls, query, max_results) -> io.NodeOutput:
        results = list(UniProt.search(query, batch_size=max_results)[:max_results])
        ids = "\n".join(str(r) for r in results[:20])
        return io.NodeOutput(base64.b64encode(pickle.dumps(results)).decode(), len(results), ids)


class Prosite_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Prosite_parse",
            display_name="Prosite parse",
            category="Biopython/UniProt",
            inputs=[io.String.Input("file_path", multiline=False, default="prosite.dat")],
            outputs=[
                io.String.Output("records"),
                io.Int.Output("count"),
                io.String.Output("accessions"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            recs = list(Prosite.parse(f))
        accs = "\n".join(r.accession for r in recs[:20])
        return io.NodeOutput(base64.b64encode(pickle.dumps(recs)).decode(), len(recs), accs)


class ExEnzyme_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ExEnzyme_read",
            display_name="ExPASy Enzyme read",
            category="Biopython/UniProt",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("record"),
                io.String.Output("ec_id"),
                io.String.Output("description"),
                io.String.Output("catalytic_activity"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            rec = ExEnzyme.read(f)
        encoded = base64.b64encode(pickle.dumps(rec)).decode()
        return io.NodeOutput(encoded, rec["ID"], rec.get("DE", ""), rec.get("CA", ""))


class ScanProsite_scan(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ScanProsite_scan",
            display_name="ScanProsite scan",
            category="Biopython/UniProt",
            inputs=[io.String.Input("sequence", multiline=True, default="")],
            outputs=[
                io.Int.Output("n_seq"),
                io.Int.Output("n_match"),
                io.String.Output("hits"),
            ],
        )

    @classmethod
    def execute(cls, sequence) -> io.NodeOutput:
        from Bio.ExPASy import ScanProsite
        handle = ScanProsite.scan(seq=sequence.strip())
        result = ScanProsite.read(handle)
        hits = "\n".join(str(h) for h in result)
        return io.NodeOutput(result.n_seq, result.n_match, hits)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            SwissProt_read,
            SwissProt_parse,
            SwissProt_record_info,
            ExPASy_get_sprot,
            UniProt_search,
            Prosite_parse,
            ExEnzyme_read,
            ScanProsite_scan,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
