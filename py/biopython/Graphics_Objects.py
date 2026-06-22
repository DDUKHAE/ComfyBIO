from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio.Graphics import GenomeDiagram
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


_FORMATS = ["PDF", "EPS", "SVG", "PNG"]
_ORIENTATIONS = ["landscape", "portrait"]
_DIAGRAM_FORMATS = ["linear", "circular"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class GenomeDiagram_from_genbank(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GenomeDiagram_from_genbank",
            display_name="Genome Diagram from GenBank",
            category="Biopython/Graphics",
            inputs=[
                io.String.Input("genbank_file", multiline=False, default=""),
                io.String.Input("diagram_name", multiline=False, default="Genome"),
                io.String.Input("feature_type", multiline=False, default="gene"),
                io.Combo.Input("diagram_format", options=_DIAGRAM_FORMATS, default="linear"),
                io.Combo.Input("orientation", options=_ORIENTATIONS, default="landscape"),
                io.Int.Input("fragments", min=1, step=1, default=4, display_mode=io.NumberDisplay.number),
                io.String.Input("output_file", multiline=False, default="genome_diagram.pdf"),
                io.Combo.Input("output_format", options=_FORMATS, default="PDF"),
            ],
            outputs=[io.String.Output("file_path"), io.Int.Output("feature_count")],
        )

    @classmethod
    def execute(cls, genbank_file, diagram_name, feature_type, diagram_format, orientation, fragments, output_file, output_format) -> io.NodeOutput:
        from reportlab.lib import colors
        record = SeqIO.read(genbank_file, "genbank")
        gd_diagram = GenomeDiagram.Diagram(diagram_name)
        gd_track = gd_diagram.new_track(1, name="Features")
        gd_feature_set = gd_track.new_set()
        count = 0
        for feature in record.features:
            if feature.type != feature_type:
                continue
            color = colors.blue if count % 2 == 0 else colors.lightblue
            gd_feature_set.add_feature(feature, color=color, label=True)
            count += 1
        if diagram_format == "circular":
            gd_diagram.draw(format="circular", circular=True, pagesize=(800, 800), start=0, end=len(record))
        else:
            gd_diagram.draw(format="linear", orientation=orientation, pagesize="A4", fragments=fragments, start=0, end=len(record))
        gd_diagram.write(output_file, output_format)
        return io.NodeOutput(output_file, count)


class GenomeDiagram_from_seqrecord(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GenomeDiagram_from_seqrecord",
            display_name="Genome Diagram from SeqRecord",
            category="Biopython/Graphics",
            inputs=[
                io.String.Input("seqrecord", multiline=False, default=""),
                io.String.Input("diagram_name", multiline=False, default="Genome"),
                io.String.Input("feature_type", multiline=False, default="gene"),
                io.Combo.Input("diagram_format", options=_DIAGRAM_FORMATS, default="linear"),
                io.Combo.Input("orientation", options=_ORIENTATIONS, default="landscape"),
                io.Int.Input("fragments", min=1, step=1, default=4, display_mode=io.NumberDisplay.number),
                io.String.Input("output_file", multiline=False, default="genome_diagram.pdf"),
                io.Combo.Input("output_format", options=_FORMATS, default="PDF"),
            ],
            outputs=[io.String.Output("file_path"), io.Int.Output("feature_count")],
        )

    @classmethod
    def execute(cls, seqrecord, diagram_name, feature_type, diagram_format, orientation, fragments, output_file, output_format) -> io.NodeOutput:
        from reportlab.lib import colors
        record = pickle.loads(base64.b64decode(seqrecord))
        gd_diagram = GenomeDiagram.Diagram(diagram_name)
        gd_track = gd_diagram.new_track(1, name="Features")
        gd_feature_set = gd_track.new_set()
        count = 0
        for feature in record.features:
            if feature.type != feature_type:
                continue
            color = colors.blue if count % 2 == 0 else colors.lightblue
            gd_feature_set.add_feature(feature, color=color, label=True)
            count += 1
        if diagram_format == "circular":
            gd_diagram.draw(format="circular", circular=True, pagesize=(800, 800), start=0, end=len(record))
        else:
            gd_diagram.draw(format="linear", orientation=orientation, pagesize="A4", fragments=fragments, start=0, end=len(record))
        gd_diagram.write(output_file, output_format)
        return io.NodeOutput(output_file, count)


class GenomeDiagram_compare_regions(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GenomeDiagram_compare_regions",
            display_name="Genome Diagram compare regions",
            category="Biopython/Graphics",
            inputs=[
                io.String.Input("genbank_file1", multiline=False, default=""),
                io.String.Input("genbank_file2", multiline=False, default=""),
                io.String.Input("diagram_name", multiline=False, default="Comparison"),
                io.String.Input("output_file", multiline=False, default="comparison.pdf"),
                io.Combo.Input("output_format", options=_FORMATS, default="PDF"),
            ],
            outputs=[io.String.Output("file_path")],
        )

    @classmethod
    def execute(cls, genbank_file1, genbank_file2, diagram_name, output_file, output_format) -> io.NodeOutput:
        from reportlab.lib import colors
        rec1 = SeqIO.read(genbank_file1, "genbank")
        rec2 = SeqIO.read(genbank_file2, "genbank")
        gd_diagram = GenomeDiagram.Diagram(diagram_name)
        for i, (record, color) in enumerate([(rec1, colors.blue), (rec2, colors.red)], 1):
            track = gd_diagram.new_track(i, name=record.id)
            fset = track.new_set()
            for feature in record.features:
                if feature.type == "gene":
                    fset.add_feature(feature, color=color, label=True)
        gd_diagram.draw(format="linear", orientation="landscape", pagesize="A4", fragments=1, start=0, end=max(len(rec1), len(rec2)))
        gd_diagram.write(output_file, output_format)
        return io.NodeOutput(output_file)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            GenomeDiagram_from_genbank,
            GenomeDiagram_from_seqrecord,
            GenomeDiagram_compare_regions,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
