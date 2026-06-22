from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import phenotype


_FORMATS = ["pm-csv", "pm-json"]


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Phenotype_parse(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_parse",
            display_name="Phenotype parse",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.Combo.Input("format", options=_FORMATS, default="pm-csv"),
            ],
            outputs=[
                io.String.Output("plates"),
                io.Int.Output("count"),
                io.String.Output("plate_ids"),
            ],
        )

    @classmethod
    def execute(cls, file_path, format) -> io.NodeOutput:
        plates = list(phenotype.parse(file_path, format))
        ids = "\n".join("%s (%d wells)" % (p.id, len(p)) for p in plates)
        return io.NodeOutput(base64.b64encode(pickle.dumps(plates)).decode(), len(plates), ids)


class Phenotype_get_plate(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_get_plate",
            display_name="Phenotype get plate",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("plates", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("plate"), io.String.Output("plate_id"), io.Int.Output("well_count")],
        )

    @classmethod
    def execute(cls, plates, index) -> io.NodeOutput:
        plist = pickle.loads(base64.b64decode(plates))
        plate = plist[index - 1]
        return io.NodeOutput(base64.b64encode(pickle.dumps(plate)).decode(), plate.id, len(plate))


class Phenotype_get_well(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_get_well",
            display_name="Phenotype get well",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("plate", multiline=False, default=""),
                io.String.Input("well_id", multiline=False, default="A01"),
            ],
            outputs=[io.String.Output("well"), io.String.Output("well_id_out"), io.String.Output("data_preview")],
        )

    @classmethod
    def execute(cls, plate, well_id) -> io.NodeOutput:
        p = pickle.loads(base64.b64decode(plate))
        well = p[well_id.upper()]
        preview = str(list(well)[:5])
        return io.NodeOutput(base64.b64encode(pickle.dumps(well)).decode(), well.id, preview)


class Phenotype_well_slice(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_well_slice",
            display_name="Phenotype well slice",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("well", multiline=False, default=""),
                io.Float.Input("start", min=0.0, step=1.0, default=0.0),
                io.Float.Input("end", min=0.0, step=1.0, default=10.0),
            ],
            outputs=[io.String.Output("values")],
        )

    @classmethod
    def execute(cls, well, start, end) -> io.NodeOutput:
        w = pickle.loads(base64.b64decode(well))
        values = w[start:end]
        return io.NodeOutput("\n".join(str(v) for v in values))


class Phenotype_subtract_control(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_subtract_control",
            display_name="Phenotype subtract control",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("plate", multiline=False, default=""),
                io.String.Input("control_well", multiline=False, default="A01"),
            ],
            outputs=[io.String.Output("plate"), io.String.Output("plate_id")],
        )

    @classmethod
    def execute(cls, plate, control_well) -> io.NodeOutput:
        p = pickle.loads(base64.b64decode(plate))
        corrected = p.subtract_control(control=control_well.upper())
        return io.NodeOutput(base64.b64encode(pickle.dumps(corrected)).decode(), corrected.id)


class Phenotype_fit(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_fit",
            display_name="Phenotype fit well",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("well", multiline=False, default=""),
                io.Combo.Input("model", options=["default", "gompertz", "logistic", "richards"], default="default"),
            ],
            outputs=[
                io.String.Output("well"),
                io.String.Output("model_used"),
                io.String.Output("parameters"),
            ],
        )

    @classmethod
    def execute(cls, well, model) -> io.NodeOutput:
        w = pickle.loads(base64.b64decode(well))
        if model == "default":
            w.fit()
        else:
            w.fit(model)
        params = "\n".join(
            "%s: %.4f" % (p, getattr(w, p))
            for p in ["min", "max", "average_height", "area", "plateau", "slope", "lag"]
            if getattr(w, p, None) is not None
        )
        return io.NodeOutput(base64.b64encode(pickle.dumps(w)).decode(), str(w.model), params)


class Phenotype_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Phenotype_write",
            display_name="Phenotype write",
            category="Biopython/Phenotype",
            inputs=[
                io.String.Input("plate", multiline=False, default=""),
                io.String.Input("file_path", multiline=False, default="output.json"),
                io.Combo.Input("format", options=["pm-json"], default="pm-json"),
            ],
            outputs=[io.Int.Output("count"), io.String.Output("file_path")],
        )

    @classmethod
    def execute(cls, plate, file_path, format) -> io.NodeOutput:
        p = pickle.loads(base64.b64decode(plate))
        count = phenotype.write(p, file_path, format)
        return io.NodeOutput(count, file_path)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Phenotype_parse,
            Phenotype_get_plate,
            Phenotype_get_well,
            Phenotype_well_slice,
            Phenotype_subtract_control,
            Phenotype_fit,
            Phenotype_write,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
