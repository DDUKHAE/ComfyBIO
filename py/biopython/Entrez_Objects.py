from __future__ import annotations
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import Entrez


_DATABASES = ["pubmed", "nucleotide", "protein", "gene", "taxonomy", "pmc", "snp", "geo"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Entrez_einfo(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_einfo",
            display_name="Entrez einfo",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.String.Input("db", multiline=False, default=""),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, email, db) -> io.NodeOutput:
        Entrez.email = email
        if db.strip():
            stream = Entrez.einfo(db=db.strip())
        else:
            stream = Entrez.einfo()
        record = Entrez.read(stream)
        stream.close()
        return io.NodeOutput(str(record))


class Entrez_esearch(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_esearch",
            display_name="Entrez esearch",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("db", options=_DATABASES, default="pubmed"),
                io.String.Input("term", multiline=False, default="biopython[title]"),
                io.Int.Input("retmax", min=1, step=10, default=20, display_mode=io.NumberDisplay.number),
            ],
            outputs=[
                io.String.Output("id_list"),
                io.String.Output("count"),
                io.String.Output("webenv"),
                io.String.Output("query_key"),
            ],
        )

    @classmethod
    def execute(cls, email, db, term, retmax) -> io.NodeOutput:
        Entrez.email = email
        stream = Entrez.esearch(db=db, term=term, retmax=str(retmax), usehistory="y")
        record = Entrez.read(stream)
        stream.close()
        return io.NodeOutput(
            "\n".join(record.get("IdList", [])),
            record.get("Count", "0"),
            record.get("WebEnv", ""),
            record.get("QueryKey", ""),
        )


class Entrez_efetch(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_efetch",
            display_name="Entrez efetch",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("db", options=_DATABASES, default="nucleotide"),
                io.String.Input("ids", multiline=True, default="EU490707"),
                io.String.Input("rettype", multiline=False, default="gb"),
                io.String.Input("retmode", multiline=False, default="text"),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, email, db, ids, rettype, retmode) -> io.NodeOutput:
        Entrez.email = email
        id_str = ",".join(i.strip() for i in ids.splitlines() if i.strip())
        stream = Entrez.efetch(db=db, id=id_str, rettype=rettype, retmode=retmode)
        result = stream.read()
        stream.close()
        return io.NodeOutput(result)


class Entrez_efetch_save(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_efetch_save",
            display_name="Entrez efetch save",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("db", options=_DATABASES, default="nucleotide"),
                io.String.Input("ids", multiline=True, default="EU490707"),
                io.String.Input("rettype", multiline=False, default="gb"),
                io.String.Input("retmode", multiline=False, default="text"),
                io.String.Input("output_file", multiline=False, default="fetched.gb"),
            ],
            outputs=[io.String.Output("file_path"), io.Int.Output("bytes_written")],
        )

    @classmethod
    def execute(cls, email, db, ids, rettype, retmode, output_file) -> io.NodeOutput:
        Entrez.email = email
        id_str = ",".join(i.strip() for i in ids.splitlines() if i.strip())
        stream = Entrez.efetch(db=db, id=id_str, rettype=rettype, retmode=retmode)
        data = stream.read()
        stream.close()
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(output_file, mode) as f:
            f.write(data)
        return io.NodeOutput(output_file, len(data))


class Entrez_esummary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_esummary",
            display_name="Entrez esummary",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("db", options=_DATABASES, default="pubmed"),
                io.String.Input("ids", multiline=True, default="19304878"),
            ],
            outputs=[io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, email, db, ids) -> io.NodeOutput:
        Entrez.email = email
        id_str = ",".join(i.strip() for i in ids.splitlines() if i.strip())
        stream = Entrez.esummary(db=db, id=id_str)
        record = Entrez.read(stream)
        stream.close()
        return io.NodeOutput(str(record))


class Entrez_epost(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_epost",
            display_name="Entrez epost",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("db", options=_DATABASES, default="pubmed"),
                io.String.Input("ids", multiline=True, default=""),
            ],
            outputs=[io.String.Output("webenv"), io.String.Output("query_key")],
        )

    @classmethod
    def execute(cls, email, db, ids) -> io.NodeOutput:
        Entrez.email = email
        id_str = ",".join(i.strip() for i in ids.splitlines() if i.strip())
        record = Entrez.read(Entrez.epost(db, id=id_str))
        return io.NodeOutput(record["WebEnv"], record["QueryKey"])


class Entrez_elink(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_elink",
            display_name="Entrez elink",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.Combo.Input("dbfrom", options=_DATABASES, default="pubmed"),
                io.String.Input("ids", multiline=True, default="19304878"),
                io.String.Input("db", multiline=False, default=""),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, email, dbfrom, ids, db) -> io.NodeOutput:
        Entrez.email = email
        id_str = ",".join(i.strip() for i in ids.splitlines() if i.strip())
        kwargs = {"dbfrom": dbfrom, "id": id_str}
        if db.strip():
            kwargs["db"] = db.strip()
        record = Entrez.read(Entrez.elink(**kwargs))
        return io.NodeOutput(str(record))


class Entrez_egquery(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_egquery",
            display_name="Entrez egquery",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.String.Input("term", multiline=False, default="biopython"),
            ],
            outputs=[io.String.Output("counts_by_database")],
        )

    @classmethod
    def execute(cls, email, term) -> io.NodeOutput:
        Entrez.email = email
        stream = Entrez.egquery(term=term)
        record = Entrez.read(stream)
        stream.close()
        lines = ["%s: %s" % (row["DbName"], row["Count"]) for row in record["eGQueryResult"]]
        return io.NodeOutput("\n".join(lines))


class Entrez_espell(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Entrez_espell",
            display_name="Entrez espell",
            category="Biopython/Entrez",
            inputs=[
                io.String.Input("email", multiline=False, default=""),
                io.String.Input("term", multiline=False, default=""),
            ],
            outputs=[io.String.Output("corrected_query"), io.String.Output("original_query")],
        )

    @classmethod
    def execute(cls, email, term) -> io.NodeOutput:
        Entrez.email = email
        stream = Entrez.espell(term=term)
        record = Entrez.read(stream)
        stream.close()
        return io.NodeOutput(record.get("CorrectedQuery", ""), record.get("Query", ""))


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Entrez_einfo,
            Entrez_esearch,
            Entrez_efetch,
            Entrez_efetch_save,
            Entrez_esummary,
            Entrez_epost,
            Entrez_elink,
            Entrez_egquery,
            Entrez_espell,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
