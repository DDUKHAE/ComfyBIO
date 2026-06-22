from __future__ import annotations

import json
# pyrefly: ignore [missing-import]
from comfy_api.latest import io


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Fastp_trim(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Fastp_trim",
            display_name="fastp trim",
            category="Transcriptomics/QC",
            inputs=[
                io.String.Input("r1_path", multiline=False, default=""),
                io.String.Input("r2_path", multiline=False, default=""),
                io.String.Input("output_dir", multiline=False, default=""),
                io.Int.Input("thread", default=4),
            ],
            outputs=[
                io.String.Output("output_dir"),
                io.String.Output("stats_json"),
            ],
        )

    @classmethod
    def execute(cls, r1_path, r2_path, output_dir, thread) -> io.NodeOutput:
        from llm_core.transcriptomics.qc import run_fastp
        stats = run_fastp(
            r1_path=r1_path,
            r2_path=r2_path or None,
            output_dir=output_dir or None,
            thread=thread,
        )
        return io.NodeOutput(output_dir, json.dumps(stats))
