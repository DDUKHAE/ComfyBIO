from __future__ import annotations

# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class STAR_align(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="STAR_align",
            display_name="STAR align",
            category="Transcriptomics/Alignment",
            inputs=[
                io.String.Input("r1_path", multiline=False, default=""),
                io.String.Input("r2_path", multiline=False, default=""),
                io.String.Input("genome_dir", multiline=False, default=""),
                io.String.Input("output_dir", multiline=False, default=""),
                io.Int.Input("threads", default=4),
            ],
            outputs=[io.String.Output("output_dir")],
        )

    @classmethod
    def execute(cls, r1_path, r2_path, genome_dir, output_dir, threads) -> io.NodeOutput:
        from llm_core.transcriptomics.align import run_star_align
        out = run_star_align(
            r1_path=r1_path,
            genome_dir=genome_dir,
            output_dir=output_dir or None,
            r2_path=r2_path or None,
            threads=threads,
        )
        return io.NodeOutput(out)


class Kallisto_quant(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Kallisto_quant",
            display_name="kallisto quant",
            category="Transcriptomics/Alignment",
            inputs=[
                io.String.Input("r1_path", multiline=False, default=""),
                io.String.Input("index_path", multiline=False, default=""),
                io.String.Input("output_dir", multiline=False, default=""),
                io.Float.Input("fragment_length", default=200.0),
                io.Float.Input("sd", default=20.0),
                io.Int.Input("threads", default=4),
            ],
            outputs=[io.String.Output("output_dir")],
        )

    @classmethod
    def execute(cls, r1_path, index_path, output_dir, fragment_length, sd, threads) -> io.NodeOutput:
        from llm_core.transcriptomics.align import run_kallisto_quant
        out = run_kallisto_quant(
            r1_path=r1_path,
            index_path=index_path,
            output_dir=output_dir or None,
            single_end=True,
            fragment_length=fragment_length,
            sd=sd,
            threads=threads,
        )
        return io.NodeOutput(out)
