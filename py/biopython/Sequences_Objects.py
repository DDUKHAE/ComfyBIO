from __future__ import annotations
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio.Data import CodonTable
from Bio.Seq import MutableSeq, Seq, back_transcribe, reverse_complement, transcribe, translate
from Bio.SeqUtils import gc_fraction


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class Seq_len(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_len",
            display_name="Sequence Length",
            category="Biopython/Sequence Objects",
            inputs=[io.String.Input("sequence", multiline=False, default="")],
            outputs=[io.Int.Output("length")],
        )

    @classmethod
    def execute(cls, sequence) -> io.NodeOutput:
        return io.NodeOutput(len(Seq(sequence)))


class Seq_element(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_element",
            display_name="Sequence element",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Int.Input("index", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("element")],
        )

    @classmethod
    def execute(cls, sequence, index) -> io.NodeOutput:
        return io.NodeOutput(Seq(sequence)[index - 1])


class Seq_count(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_count",
            display_name="Sequence count",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.String.Input("amino_acid", multiline=False, default=""),
            ],
            outputs=[io.Int.Output("count")],
        )

    @classmethod
    def execute(cls, sequence, amino_acid) -> io.NodeOutput:
        return io.NodeOutput(Seq(sequence).count(amino_acid))


class Seq_GC_percent(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_GC_percent",
            display_name="Sequence GC%",
            category="Biopython/Sequence Objects",
            inputs=[io.String.Input("sequence", multiline=False, default="")],
            outputs=[io.Float.Output("gc_percent")],
        )

    @classmethod
    def execute(cls, sequence) -> io.NodeOutput:
        return io.NodeOutput(gc_fraction(Seq(sequence)) * 100)


class Seq_slicing(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_slicing",
            display_name="Sequence slicing",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Int.Input("start", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
                io.Int.Input("end", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, start, end) -> io.NodeOutput:
        return io.NodeOutput(str(Seq(sequence)[start - 1:end]))


class Seq_reverse_complement(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_reverse_complement",
            display_name="Sequence reverse complement",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Combo.Input("operation", options=["reverse", "complement", "reverse_complement"], default="reverse"),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, operation) -> io.NodeOutput:
        seq = Seq(sequence)
        if operation == "reverse":
            return io.NodeOutput(str(seq[::-1]))
        if operation == "complement":
            return io.NodeOutput(str(seq.complement()))
        return io.NodeOutput(str(seq.reverse_complement()))


class Seq_adding(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_adding",
            display_name="Sequence adding",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence1", multiline=False, default=""),
                io.String.Input("sequence2", multiline=False, default=""),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence1, sequence2) -> io.NodeOutput:
        return io.NodeOutput(str(Seq(sequence1) + Seq(sequence2)))


class Seq_to_string(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_to_string",
            display_name="Sequence to string",
            category="Biopython/Sequence Objects",
            inputs=[io.String.Input("sequence", multiline=False, default="")],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence) -> io.NodeOutput:
        return io.NodeOutput(str(Seq(sequence)))


class Seq_join(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_join",
            display_name="Sequence join",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequences", multiline=True, default=""),
                io.String.Input("spacer_base", multiline=False, default="N"),
                io.Int.Input("spacer_count", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequences, spacer_base, spacer_count) -> io.NodeOutput:
        seqs = [Seq(line.strip()) for line in sequences.splitlines() if line.strip()]
        return io.NodeOutput(str(Seq(spacer_base * spacer_count).join(seqs)))


class Seq_change_case(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_change_case",
            display_name="Sequence change case",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Combo.Input("case", options=["upper", "lower"], default="upper"),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, case) -> io.NodeOutput:
        if case == "upper":
            return io.NodeOutput(Seq(sequence).upper())
        return io.NodeOutput(Seq(sequence).lower())


class Seq_transcribe_ops(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_transcribe_ops",
            display_name="Sequence transcription",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Combo.Input("operation", options=["transcribe", "back_transcribe", "template_transcribe"], default="transcribe"),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, operation) -> io.NodeOutput:
        seq = Seq(sequence)
        if operation == "transcribe":
            return io.NodeOutput(str(seq.transcribe()))
        if operation == "back_transcribe":
            return io.NodeOutput(str(seq.back_transcribe()))
        return io.NodeOutput(str(seq.reverse_complement().transcribe()))


class Seq_translate(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_translate",
            display_name="Sequence translate",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Combo.Input("table", options=[v.names[0] for v in CodonTable.unambiguous_dna_by_id.values()], default="Standard"),
                io.Boolean.Input("to_stop", default=False),
                io.String.Input("stop_symbol", multiline=False, default="*"),
                io.Boolean.Input("cds", default=False),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, table, to_stop=False, stop_symbol="*", cds=False) -> io.NodeOutput:
        table_id = {v.names[0]: k for k, v in CodonTable.unambiguous_dna_by_id.items()}[table]
        return io.NodeOutput(str(Seq(sequence).translate(table=table_id, to_stop=to_stop, stop_symbol=stop_symbol, cds=cds)))


class Codon_table(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Codon_table",
            display_name="Codon table",
            category="Biopython/Sequence Objects",
            inputs=[
                io.Combo.Input("table", options=[v.names[0] for v in CodonTable.unambiguous_dna_by_id.values()], default="Standard"),
                io.Combo.Input("query_type", options=["full_table", "stop_codons", "start_codons", "forward_table"], default="full_table"),
                io.String.Input("codon", multiline=False, default="ACG"),
            ],
            outputs=[io.String.Output("value")],
        )

    @classmethod
    def execute(cls, table, query_type, codon) -> io.NodeOutput:
        table_id = {v.names[0]: k for k, v in CodonTable.unambiguous_dna_by_id.items()}[table]
        codon_table = CodonTable.unambiguous_dna_by_id[table_id]
        if query_type == "full_table":
            return io.NodeOutput(str(codon_table))
        if query_type == "stop_codons":
            return io.NodeOutput(", ".join(codon_table.stop_codons))
        if query_type == "start_codons":
            return io.NodeOutput(", ".join(codon_table.start_codons))
        return io.NodeOutput(codon_table.forward_table[codon.upper()])


class Mutable_seq_objects(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Mutable_seq_objects",
            display_name="Mutable seq objects",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Combo.Input("edit_type", options=["insert", "remove", "replace", "reverse"], default="insert"),
                io.Int.Input("position", min=1, step=1, default=1, display_mode=io.NumberDisplay.number),
                io.String.Input("base", multiline=False, default=""),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, edit_type, position, base) -> io.NodeOutput:
        seq = MutableSeq(sequence)
        if edit_type == "insert":
            seq.insert(position - 1, base)
        elif edit_type == "remove":
            seq.pop(position - 1)
        elif edit_type == "replace":
            seq[position - 1] = base
        elif edit_type == "reverse":
            seq.reverse()
        return io.NodeOutput(str(seq))


class Finding_subsequences(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Finding_subsequences",
            display_name="Finding subsequences",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.String.Input("subsequence", multiline=False, default=""),
                io.Combo.Input("find_type", options=["find", "rfind", "index", "rindex", "count", "startswith", "endswith"], default="find"),
            ],
            outputs=[io.String.Output("result")],
        )

    @classmethod
    def execute(cls, sequence, subsequence, find_type) -> io.NodeOutput:
        seq = Seq(sequence)
        if find_type == "find":
            return io.NodeOutput(str(seq.find(subsequence)))
        if find_type == "rfind":
            return io.NodeOutput(str(seq.rfind(subsequence)))
        if find_type == "index":
            return io.NodeOutput(str(seq.index(subsequence)))
        if find_type == "rindex":
            return io.NodeOutput(str(seq.rindex(subsequence)))
        if find_type == "count":
            return io.NodeOutput(str(seq.count(subsequence)))
        if find_type == "startswith":
            return io.NodeOutput(str(seq.startswith(subsequence)))
        return io.NodeOutput(str(seq.endswith(subsequence)))


class Seq_unknown(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_unknown",
            display_name="Unknown sequence",
            category="Biopython/Sequence Objects",
            inputs=[io.Int.Input("length", min=0, step=1, default=10, display_mode=io.NumberDisplay.number)],
            outputs=[io.String.Output("summary"), io.Int.Output("length")],
        )

    @classmethod
    def execute(cls, length) -> io.NodeOutput:
        seq = Seq(None, length=length)
        return io.NodeOutput(repr(seq), len(seq))


class Seq_partial_slice(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_partial_slice",
            display_name="Partial sequence slice",
            category="Biopython/Sequence Objects",
            inputs=[
                io.Int.Input("known_start", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.String.Input("known_sequence", multiline=False, default=""),
                io.Int.Input("total_length", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("slice_start", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("slice_end", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, known_start, known_sequence, total_length, slice_start, slice_end) -> io.NodeOutput:
        return io.NodeOutput(str(Seq({known_start: known_sequence}, length=total_length)[slice_start:slice_end]))


class Seq_search(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_search",
            display_name="Sequence search",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.String.Input("subsequences", multiline=True, default=""),
            ],
            outputs=[io.String.Output("matches")],
        )

    @classmethod
    def execute(cls, sequence, subsequences) -> io.NodeOutput:
        subs = [line.strip() for line in subsequences.splitlines() if line.strip()]
        lines = [f"{index} {sub}" for index, sub in Seq(sequence).search(subs)]
        return io.NodeOutput("\n".join(lines))


class Seq_module_function(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Seq_module_function",
            display_name="Sequence module function",
            category="Biopython/Sequence Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.Combo.Input("function", options=["reverse_complement", "transcribe", "back_transcribe", "translate"], default="reverse_complement"),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence, function) -> io.NodeOutput:
        if function == "reverse_complement":
            return io.NodeOutput(reverse_complement(sequence))
        if function == "transcribe":
            return io.NodeOutput(transcribe(sequence))
        if function == "back_transcribe":
            return io.NodeOutput(back_transcribe(sequence))
        return io.NodeOutput(translate(sequence))


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            Seq_len, Seq_element, Seq_count, Seq_GC_percent, Seq_slicing,
            Seq_reverse_complement, Seq_adding, Seq_to_string, Seq_join,
            Seq_change_case, Seq_transcribe_ops, Seq_translate, Codon_table,
            Mutable_seq_objects, Finding_subsequences, Seq_unknown,
            Seq_partial_slice, Seq_search, Seq_module_function,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
