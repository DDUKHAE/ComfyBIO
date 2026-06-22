from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio.KEGG import Enzyme, REST


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class KEGG_enzyme_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="KEGG_enzyme_read",
            display_name="KEGG enzyme read",
            category="Biopython/KEGG",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("record"),
                io.String.Output("entry"),
                io.String.Output("classname"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            rec = Enzyme.read(f)
        encoded = base64.b64encode(pickle.dumps(rec)).decode()
        classname = "; ".join(rec.classname) if rec.classname else ""
        return io.NodeOutput(encoded, rec.entry, classname)


class KEGG_enzyme_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="KEGG_enzyme_parse",
            display_name="KEGG enzyme parse",
            category="Biopython/KEGG",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("records"),
                io.Int.Output("count"),
                io.String.Output("entries"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            recs = list(Enzyme.parse(f))
        entries = "\n".join(r.entry for r in recs)
        return io.NodeOutput(base64.b64encode(pickle.dumps(recs)).decode(), len(recs), entries)


class KEGG_api_get(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="KEGG_api_get",
            display_name="KEGG API get",
            category="Biopython/KEGG",
            inputs=[
                io.String.Input("query", multiline=False, default="ec:5.4.2.2"),
                io.String.Input("option", multiline=False, default=""),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, query, option) -> io.NodeOutput:
        args = [query] if not option.strip() else [[query], option.strip()]
        if isinstance(args[0], list):
            result = REST.kegg_get(*args).read()
        else:
            result = REST.kegg_get(args[0]).read()
        return io.NodeOutput(result)


class KEGG_api_list(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="KEGG_api_list",
            display_name="KEGG API list",
            category="Biopython/KEGG",
            inputs=[
                io.String.Input("database", multiline=False, default="pathway"),
                io.String.Input("organism", multiline=False, default=""),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, database, organism) -> io.NodeOutput:
        if organism.strip():
            result = REST.kegg_list(database, organism.strip()).read()
        else:
            result = REST.kegg_list(database).read()
        return io.NodeOutput(result)


class KEGG_api_find(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="KEGG_api_find",
            display_name="KEGG API find",
            category="Biopython/KEGG",
            inputs=[
                io.String.Input("database", multiline=False, default="compound"),
                io.String.Input("query", multiline=False, default=""),
                io.String.Input("option", multiline=False, default=""),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, database, query, option) -> io.NodeOutput:
        if option.strip():
            result = REST.kegg_find(database, query, option.strip()).read()
        else:
            result = REST.kegg_find(database, query).read()
        return io.NodeOutput(result)


class KEGG_api_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="KEGG_api_info",
            display_name="KEGG API info",
            category="Biopython/KEGG",
            inputs=[io.String.Input("database", multiline=False, default="kegg")],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, database) -> io.NodeOutput:
        return io.NodeOutput(REST.kegg_info(database).read())


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            KEGG_enzyme_read,
            KEGG_enzyme_parse,
            KEGG_api_get,
            KEGG_api_list,
            KEGG_api_find,
            KEGG_api_info,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
