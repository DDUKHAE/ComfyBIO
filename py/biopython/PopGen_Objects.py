from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio.PopGen import GenePop


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class PopGen_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PopGen_read",
            display_name="PopGen read",
            category="Biopython/PopGen",
            inputs=[io.String.Input("file_path", multiline=False, default="")],
            outputs=[
                io.String.Output("record"),
                io.String.Output("loci"),
                io.Int.Output("loci_count"),
                io.Int.Output("population_count"),
            ],
        )

    @classmethod
    def execute(cls, file_path) -> io.NodeOutput:
        with open(file_path) as f:
            rec = GenePop.read(f)
        encoded = base64.b64encode(pickle.dumps(rec)).decode()
        loci = ", ".join(rec.loci_list)
        return io.NodeOutput(encoded, loci, len(rec.loci_list), len(rec.populations))


class PopGen_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PopGen_info",
            display_name="PopGen info",
            category="Biopython/PopGen",
            inputs=[io.String.Input("record", multiline=False, default="")],
            outputs=[
                io.String.Output("loci"),
                io.Int.Output("loci_count"),
                io.Int.Output("population_count"),
                io.String.Output("populations_summary"),
            ],
        )

    @classmethod
    def execute(cls, record) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        loci = ", ".join(rec.loci_list)
        pops = "\n".join(
            "Pop%d: %d individuals" % (i, len(p))
            for i, p in enumerate(rec.populations)
        )
        return io.NodeOutput(loci, len(rec.loci_list), len(rec.populations), pops)


class PopGen_remove_population(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PopGen_remove_population",
            display_name="PopGen remove population",
            category="Biopython/PopGen",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Int.Input("position", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("record"), io.Int.Output("population_count")],
        )

    @classmethod
    def execute(cls, record, position) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        rec.remove_population(position)
        return io.NodeOutput(base64.b64encode(pickle.dumps(rec)).decode(), len(rec.populations))


class PopGen_remove_locus(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PopGen_remove_locus",
            display_name="PopGen remove locus",
            category="Biopython/PopGen",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Combo.Input("by", options=["name", "position"], default="name"),
                io.String.Input("name", multiline=False, default=""),
                io.Int.Input("position", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("record"), io.Int.Output("loci_count")],
        )

    @classmethod
    def execute(cls, record, by, name, position) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        if by == "name":
            rec.remove_locus_by_name(name)
        else:
            rec.remove_locus_by_position(position)
        return io.NodeOutput(base64.b64encode(pickle.dumps(rec)).decode(), len(rec.loci_list))


class PopGen_split_in_loci(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PopGen_split_in_loci",
            display_name="PopGen split in loci",
            category="Biopython/PopGen",
            inputs=[io.String.Input("record", multiline=False, default="")],
            outputs=[io.String.Output("records_dict"), io.String.Output("loci_names")],
        )

    @classmethod
    def execute(cls, record) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        loci_dict = rec.split_in_loci()
        names = ", ".join(loci_dict.keys())
        return io.NodeOutput(base64.b64encode(pickle.dumps(loci_dict)).decode(), names)


class PopGen_split_in_pops(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PopGen_split_in_pops",
            display_name="PopGen split in populations",
            category="Biopython/PopGen",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("pop_names", multiline=True, default="Pop1\nPop2"),
            ],
            outputs=[io.String.Output("records_dict"), io.String.Output("pop_names_out")],
        )

    @classmethod
    def execute(cls, record, pop_names) -> io.NodeOutput:
        rec = pickle.loads(base64.b64decode(record))
        names = [n.strip() for n in pop_names.splitlines() if n.strip()]
        pops_dict = rec.split_in_pops(names)
        return io.NodeOutput(base64.b64encode(pickle.dumps(pops_dict)).decode(), ", ".join(pops_dict.keys()))


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            PopGen_read,
            PopGen_info,
            PopGen_remove_population,
            PopGen_remove_locus,
            PopGen_split_in_loci,
            PopGen_split_in_pops,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
