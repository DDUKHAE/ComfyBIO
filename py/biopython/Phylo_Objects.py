from __future__ import annotations
import base64
import pickle
from io import StringIO
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import Phylo


_FORMATS = ["newick", "nexus", "phyloxml", "nexml", "cdao"]
_WRITE_FORMATS = ["newick", "nexus", "phyloxml", "nexml", "cdao"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Phylo_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_read",
            display_name="Phylo read",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
                io.Combo.Input("format", options=_FORMATS, default="newick"),
            ],
            outputs=[io.String.Output("tree"), io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, source, source_kind, format) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        tree = Phylo.read(handle, format)
        if source_kind == "path":
            handle.close()
        buf = StringIO()
        Phylo.draw_ascii(tree, file=buf)
        return io.NodeOutput(base64.b64encode(pickle.dumps(tree)).decode(), buf.getvalue())


class Phylo_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_parse",
            display_name="Phylo parse",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.Combo.Input("format", options=_FORMATS, default="phyloxml"),
            ],
            outputs=[io.String.Output("trees"), io.Int.Output("count")],
        )

    @classmethod
    def execute(cls, file_path, format) -> io.NodeOutput:
        trees = list(Phylo.parse(file_path, format))
        return io.NodeOutput(base64.b64encode(pickle.dumps(trees)).decode(), len(trees))


class Phylo_get_tree(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_get_tree",
            display_name="Phylo get tree",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("trees", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("tree"), io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, trees, index) -> io.NodeOutput:
        tree = pickle.loads(base64.b64decode(trees))[index - 1]
        buf = StringIO()
        Phylo.draw_ascii(tree, file=buf)
        return io.NodeOutput(base64.b64encode(pickle.dumps(tree)).decode(), buf.getvalue())


class Phylo_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_write",
            display_name="Phylo write",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("tree", multiline=False, default=""),
                io.String.Input("file_path", multiline=False, default="output.nwk"),
                io.Combo.Input("format", options=_WRITE_FORMATS, default="newick"),
            ],
            outputs=[io.Int.Output("count"), io.String.Output("file_path")],
        )

    @classmethod
    def execute(cls, tree, file_path, format) -> io.NodeOutput:
        t = pickle.loads(base64.b64decode(tree))
        items = t if isinstance(t, list) else [t]
        count = Phylo.write(items, file_path, format)
        return io.NodeOutput(count, file_path)


class Phylo_convert(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_convert",
            display_name="Phylo convert",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("input_path", multiline=False, default=""),
                io.Combo.Input("input_format", options=_FORMATS, default="newick"),
                io.String.Input("output_path", multiline=False, default=""),
                io.Combo.Input("output_format", options=_WRITE_FORMATS, default="phyloxml"),
            ],
            outputs=[io.Int.Output("count"), io.String.Output("output_path")],
        )

    @classmethod
    def execute(cls, input_path, input_format, output_path, output_format) -> io.NodeOutput:
        count = Phylo.convert(input_path, input_format, output_path, output_format)
        return io.NodeOutput(count, output_path)


class Phylo_draw_ascii(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_draw_ascii",
            display_name="Phylo draw ASCII",
            category="Biopython/Phylo",
            inputs=[io.String.Input("tree", multiline=False, default="")],
            outputs=[io.String.Output("ascii_art")],
        )

    @classmethod
    def execute(cls, tree) -> io.NodeOutput:
        t = pickle.loads(base64.b64decode(tree))
        buf = StringIO()
        Phylo.draw_ascii(t, file=buf)
        return io.NodeOutput(buf.getvalue())


class Phylo_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_info",
            display_name="Phylo info",
            category="Biopython/Phylo",
            inputs=[io.String.Input("tree", multiline=False, default="")],
            outputs=[
                io.Int.Output("terminals"),
                io.Float.Output("total_branch_length"),
                io.Boolean.Output("is_bifurcating"),
                io.String.Output("terminal_names"),
            ],
        )

    @classmethod
    def execute(cls, tree) -> io.NodeOutput:
        t = pickle.loads(base64.b64decode(tree))
        terminals = t.get_terminals()
        names = ", ".join(c.name or "" for c in terminals)
        return io.NodeOutput(
            t.count_terminals(),
            t.total_branch_length(),
            t.is_bifurcating(),
            names,
        )


class Phylo_common_ancestor(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_common_ancestor",
            display_name="Phylo common ancestor",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("tree", multiline=False, default=""),
                io.String.Input("name1", multiline=False, default=""),
                io.String.Input("name2", multiline=False, default=""),
            ],
            outputs=[io.String.Output("ancestor_name"), io.Int.Output("terminal_count")],
        )

    @classmethod
    def execute(cls, tree, name1, name2) -> io.NodeOutput:
        t = pickle.loads(base64.b64decode(tree))
        mrca = t.common_ancestor({"name": name1}, {"name": name2})
        return io.NodeOutput(mrca.name or "(internal)", mrca.count_terminals())


class Phylo_ladderize(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_ladderize",
            display_name="Phylo ladderize",
            category="Biopython/Phylo",
            inputs=[
                io.String.Input("tree", multiline=False, default=""),
                io.Boolean.Input("reverse", default=False),
            ],
            outputs=[io.String.Output("tree"), io.String.Output("ascii_art")],
        )

    @classmethod
    def execute(cls, tree, reverse) -> io.NodeOutput:
        t = pickle.loads(base64.b64decode(tree))
        t.ladderize(reverse=reverse)
        buf = StringIO()
        Phylo.draw_ascii(t, file=buf)
        return io.NodeOutput(base64.b64encode(pickle.dumps(t)).decode(), buf.getvalue())


class Phylo_root_at_midpoint(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phylo_root_at_midpoint",
            display_name="Phylo root at midpoint",
            category="Biopython/Phylo",
            inputs=[io.String.Input("tree", multiline=False, default="")],
            outputs=[io.String.Output("tree"), io.String.Output("ascii_art")],
        )

    @classmethod
    def execute(cls, tree) -> io.NodeOutput:
        t = pickle.loads(base64.b64decode(tree))
        t.root_at_midpoint()
        buf = StringIO()
        Phylo.draw_ascii(t, file=buf)
        return io.NodeOutput(base64.b64encode(pickle.dumps(t)).decode(), buf.getvalue())


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Phylo_read,
            Phylo_parse,
            Phylo_get_tree,
            Phylo_write,
            Phylo_convert,
            Phylo_draw_ascii,
            Phylo_info,
            Phylo_common_ancestor,
            Phylo_ladderize,
            Phylo_root_at_midpoint,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
