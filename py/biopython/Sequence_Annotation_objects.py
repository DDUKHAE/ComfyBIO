from __future__ import annotations
import base64
import json
import pickle
from io import StringIO
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import (
    AfterPosition, BeforePosition, CompoundLocation, ExactPosition,
    OneOfPosition, Reference, SeqFeature, SimpleLocation, UnknownPosition, WithinPosition,
)
from Bio.SeqRecord import SeqRecord


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class SeqRecord_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_read",
            display_name="SeqRecord read",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("source_kind", options=["path", "text"], default="path"),
                io.Combo.Input("format", options=["fasta", "genbank"], default="fasta"),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, source, source_kind, format) -> io.NodeOutput:
        handle = open(source) if source_kind == "path" else StringIO(source)
        record = SeqIO.read(handle, format)
        if source_kind == "path":
            handle.close()
        return io.NodeOutput(base64.b64encode(pickle.dumps(record)).decode())


class SeqRecord_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_create",
            display_name="SeqRecord create",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("sequence", multiline=False, default=""),
                io.String.Input("id", multiline=False, default="<unknown id>"),
                io.String.Input("name", multiline=False, default="<unknown name>"),
                io.String.Input("description", multiline=False, default="<unknown description>"),
                io.Combo.Input("molecule_type", options=["DNA", "RNA", "protein"], default="DNA"),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, sequence, id, name, description, molecule_type="DNA") -> io.NodeOutput:
        record = SeqRecord(
            Seq(sequence),
            id=id or "<unknown id>",
            name=name or "<unknown name>",
            description=description or "<unknown description>",
        )
        record.annotations["molecule_type"] = molecule_type
        return io.NodeOutput(base64.b64encode(pickle.dumps(record)).decode())


class SeqRecord_summary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_summary",
            display_name="SeqRecord summary",
            category="Biopython/Sequence Annotation Objects",
            inputs=[io.String.Input("record", multiline=False, default="")],
            outputs=[io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, record) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        summary = (
            f"SeqRecord(id={r.id!r}, name={r.name!r}, len={len(r)}, "
            f"features={len(r.features)}, dbxrefs={len(r.dbxrefs)}, "
            f"annotations={sorted(r.annotations.keys())}, "
            f"letter_annotations={sorted(r.letter_annotations.keys())})"
        )
        return io.NodeOutput(summary)


class SeqRecord_get_fields(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_get_fields",
            display_name="SeqRecord fields",
            category="Biopython/Sequence Annotation Objects",
            inputs=[io.String.Input("record", multiline=False, default="")],
            outputs=[
                io.String.Output("id"),
                io.String.Output("name"),
                io.String.Output("description"),
                io.String.Output("sequence"),
            ],
        )

    @classmethod
    def execute(cls, record) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        return io.NodeOutput(r.id, r.name, r.description, str(r.seq))


class SeqRecord_set_annotation(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_set_annotation",
            display_name="SeqRecord set annotation",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("key", multiline=False, default=""),
                io.String.Input("value", multiline=False, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, key, value) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        try:
            r.annotations[key] = json.loads(value)
        except Exception:
            r.annotations[key] = value
        return io.NodeOutput(base64.b64encode(pickle.dumps(r)).decode())


class SeqRecord_set_letter_annotation(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_set_letter_annotation",
            display_name="SeqRecord set letter annotation",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("key", multiline=False, default="phred_quality"),
                io.String.Input("values", multiline=True, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, key, values) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        try:
            parsed = json.loads(values)
            if isinstance(parsed, dict):
                parsed = list(parsed.values())
        except Exception:
            parsed = [int(x) for x in values.replace(",", " ").split() if x]
        r.letter_annotations[key] = parsed
        return io.NodeOutput(base64.b64encode(pickle.dumps(r)).decode())


class SeqRecord_set_dbxrefs(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_set_dbxrefs",
            display_name="SeqRecord set dbxrefs",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("dbxrefs", multiline=True, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, dbxrefs) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        r.dbxrefs = [l.strip() for l in dbxrefs.splitlines() if l.strip()]
        return io.NodeOutput(base64.b64encode(pickle.dumps(r)).decode())


class SeqRecord_add_feature(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_add_feature",
            display_name="SeqRecord add feature",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("feature", multiline=False, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, feature) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        r.features.append(pickle.loads(base64.b64decode(feature)))
        return io.NodeOutput(base64.b64encode(pickle.dumps(r)).decode())


class SeqRecord_add_reference(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_add_reference",
            display_name="SeqRecord add reference",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("reference", multiline=False, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, reference) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        r.annotations.setdefault("references", [])
        r.annotations["references"].append(pickle.loads(base64.b64decode(reference)))
        return io.NodeOutput(base64.b64encode(pickle.dumps(r)).decode())


class SeqRecord_format(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_format",
            display_name="SeqRecord format",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("source", multiline=False, default=""),
                io.Combo.Input("format", options=["fasta", "genbank"], default="fasta"),
                io.String.Input("name", multiline=False, default="Sequence"),
            ],
            outputs=[io.String.Output("formatted")],
        )

    @classmethod
    def execute(cls, source, format, name="Sequence") -> io.NodeOutput:
        try:
            rec = pickle.loads(base64.b64decode(source))
            return io.NodeOutput(rec.format(format))
        except Exception:
            return io.NodeOutput(">%s\n%s\n" % (name, source))


class SeqRecord_slice(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_slice",
            display_name="SeqRecord slice",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.Int.Input("start", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("end", min=0, step=1, default=1, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, start, end) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        return io.NodeOutput(base64.b64encode(pickle.dumps(r[start:end])).decode())


class SeqRecord_addition(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_addition",
            display_name="SeqRecord addition",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record1", multiline=False, default=""),
                io.String.Input("record2", multiline=False, default=""),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record1, record2) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record1)) + pickle.loads(base64.b64decode(record2))
        return io.NodeOutput(base64.b64encode(pickle.dumps(r)).decode())


class SeqRecord_reverse_complement(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_reverse_complement",
            display_name="SeqRecord reverse complement",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("record", multiline=False, default=""),
                io.String.Input("id", multiline=False, default=""),
                io.Boolean.Input("preserve_name", default=False),
                io.Boolean.Input("preserve_description", default=False),
                io.Boolean.Input("preserve_annotations", default=False),
                io.Boolean.Input("preserve_dbxrefs", default=False),
            ],
            outputs=[io.String.Output("record")],
        )

    @classmethod
    def execute(cls, record, id="", preserve_name=False, preserve_description=False, preserve_annotations=False, preserve_dbxrefs=False) -> io.NodeOutput:
        r = pickle.loads(base64.b64decode(record))
        kwargs = {}
        if id:
            kwargs["id"] = id
        if preserve_name:
            kwargs["name"] = r.name
        if preserve_description:
            kwargs["description"] = r.description
        if preserve_annotations:
            kwargs["annotations"] = r.annotations.copy()
        if preserve_dbxrefs:
            kwargs["dbxrefs"] = r.dbxrefs[:]
        return io.NodeOutput(base64.b64encode(pickle.dumps(r.reverse_complement(**kwargs))).decode())


class SeqRecord_compare_attributes(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqRecord_compare_attributes",
            display_name="SeqRecord compare attributes",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("source1", multiline=False, default=""),
                io.String.Input("source2", multiline=False, default=""),
                io.Combo.Input("compare", options=["seq", "id", "name", "description", "id_and_seq"], default="seq"),
            ],
            outputs=[io.Boolean.Output("equal")],
        )

    @classmethod
    def execute(cls, source1, source2, compare) -> io.NodeOutput:
        r1 = pickle.loads(base64.b64decode(source1))
        r2 = pickle.loads(base64.b64decode(source2))
        if compare == "seq":
            return io.NodeOutput(r1.seq == r2.seq)
        if compare == "id":
            return io.NodeOutput(r1.id == r2.id)
        if compare == "name":
            return io.NodeOutput(r1.name == r2.name)
        if compare == "description":
            return io.NodeOutput(r1.description == r2.description)
        return io.NodeOutput(r1.id == r2.id and r1.seq == r2.seq)


class Position_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Position_create",
            display_name="Position create",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.Combo.Input("position_type", options=["exact", "before", "after", "within", "one_of", "unknown"], default="exact"),
                io.Int.Input("position", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("left", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.Int.Input("right", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.String.Input("choices", multiline=True, default=""),
            ],
            outputs=[io.String.Output("position")],
        )

    @classmethod
    def execute(cls, position_type, position, left, right, choices) -> io.NodeOutput:
        if position_type == "exact":
            obj = ExactPosition(position)
        elif position_type == "before":
            obj = BeforePosition(position)
        elif position_type == "after":
            obj = AfterPosition(position)
        elif position_type == "within":
            obj = WithinPosition(position, left=left, right=right)
        elif position_type == "one_of":
            obj = OneOfPosition(position, [int(x) for x in choices.replace(",", " ").split() if x])
        else:
            obj = UnknownPosition()
        return io.NodeOutput(base64.b64encode(pickle.dumps(obj)).decode())


class Position_summary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Position_summary",
            display_name="Position summary",
            category="Biopython/Sequence Annotation Objects",
            inputs=[io.String.Input("position", multiline=False, default="")],
            outputs=[io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, position) -> io.NodeOutput:
        pos = pickle.loads(base64.b64decode(position))
        if isinstance(pos, UnknownPosition):
            return io.NodeOutput("UnknownPosition()")
        return io.NodeOutput(f"{pos!r} int={int(pos)}")


class SimpleLocation_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SimpleLocation_create",
            display_name="SimpleLocation create",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("start", multiline=False, default="0"),
                io.String.Input("end", multiline=False, default="1"),
                io.Int.Input("strand", min=-1, max=1, step=1, default=1, display_mode=io.NumberDisplay.number),
                io.String.Input("ref", multiline=False, default=""),
                io.String.Input("ref_db", multiline=False, default=""),
            ],
            outputs=[io.String.Output("location")],
        )

    @classmethod
    def execute(cls, start, end, strand, ref="", ref_db="") -> io.NodeOutput:
        try:
            start_pos = pickle.loads(base64.b64decode(start))
        except Exception:
            start_pos = int(start)
        try:
            end_pos = pickle.loads(base64.b64decode(end))
        except Exception:
            end_pos = int(end)
        loc = SimpleLocation(start_pos, end_pos, strand=strand, ref=ref or None, ref_db=ref_db or None)
        return io.NodeOutput(base64.b64encode(pickle.dumps(loc)).decode())


class CompoundLocation_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="CompoundLocation_create",
            display_name="CompoundLocation create",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("parts", multiline=True, default=""),
                io.Combo.Input("operator", options=["join", "order"], default="join"),
            ],
            outputs=[io.String.Output("location")],
        )

    @classmethod
    def execute(cls, parts, operator) -> io.NodeOutput:
        locations = [pickle.loads(base64.b64decode(line.strip())) for line in parts.splitlines() if line.strip()]
        return io.NodeOutput(base64.b64encode(pickle.dumps(CompoundLocation(locations, operator=operator))).decode())


class Location_summary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Location_summary",
            display_name="Location summary",
            category="Biopython/Sequence Annotation Objects",
            inputs=[io.String.Input("location", multiline=False, default="")],
            outputs=[io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, location) -> io.NodeOutput:
        loc = pickle.loads(base64.b64decode(location))
        summary = f"{loc!r} len={len(loc)} start={int(loc.start)} end={int(loc.end)} strand={loc.strand}"
        return io.NodeOutput(summary)


class Location_contains(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Location_contains",
            display_name="Location contains",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("location", multiline=False, default=""),
                io.Int.Input("coordinate", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.Boolean.Output("contains")],
        )

    @classmethod
    def execute(cls, location, coordinate) -> io.NodeOutput:
        return io.NodeOutput(coordinate in pickle.loads(base64.b64decode(location)))


class SeqFeature_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqFeature_create",
            display_name="SeqFeature create",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("location", multiline=False, default=""),
                io.String.Input("type", multiline=False, default=""),
                io.String.Input("qualifiers", multiline=True, default=""),
                io.String.Input("id", multiline=False, default="<unknown id>"),
            ],
            outputs=[io.String.Output("feature")],
        )

    @classmethod
    def execute(cls, location, type, qualifiers, id="<unknown id>") -> io.NodeOutput:
        loc = pickle.loads(base64.b64decode(location)) if location else None
        try:
            quals = json.loads(qualifiers)
        except Exception:
            quals = {k.strip(): v.strip() for k, _, v in (l.partition("=") for l in qualifiers.splitlines() if l.strip())}
        feature = SeqFeature(location=loc, type=type, id=id or "<unknown id>", qualifiers=quals)
        return io.NodeOutput(base64.b64encode(pickle.dumps(feature)).decode())


class SeqFeature_summary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqFeature_summary",
            display_name="SeqFeature summary",
            category="Biopython/Sequence Annotation Objects",
            inputs=[io.String.Input("feature", multiline=False, default="")],
            outputs=[io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, feature) -> io.NodeOutput:
        f = pickle.loads(base64.b64decode(feature))
        quals = {key: list(val) for key, val in f.qualifiers.items()}
        return io.NodeOutput(f"SeqFeature(type={f.type!r}, location={f.location!r}, qualifiers={quals})")


class SeqFeature_contains(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqFeature_contains",
            display_name="SeqFeature contains",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("feature", multiline=False, default=""),
                io.Int.Input("coordinate", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
            ],
            outputs=[io.Boolean.Output("contains")],
        )

    @classmethod
    def execute(cls, feature, coordinate) -> io.NodeOutput:
        return io.NodeOutput(coordinate in pickle.loads(base64.b64decode(feature)))


class SeqFeature_extract(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeqFeature_extract",
            display_name="SeqFeature extract",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("sequence_or_record", multiline=False, default=""),
                io.String.Input("feature", multiline=False, default=""),
            ],
            outputs=[io.String.Output("sequence")],
        )

    @classmethod
    def execute(cls, sequence_or_record, feature) -> io.NodeOutput:
        feat = pickle.loads(base64.b64decode(feature))
        try:
            target = pickle.loads(base64.b64decode(sequence_or_record))
        except Exception:
            target = Seq(sequence_or_record)
        return io.NodeOutput(str(feat.extract(target)))


class Reference_create(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Reference_create",
            display_name="Reference create",
            category="Biopython/Sequence Annotation Objects",
            inputs=[
                io.String.Input("authors", multiline=False, default=""),
                io.String.Input("title", multiline=False, default=""),
                io.String.Input("journal", multiline=False, default=""),
                io.String.Input("medline_id", multiline=False, default=""),
                io.String.Input("pubmed_id", multiline=False, default=""),
                io.String.Input("comment", multiline=False, default=""),
                io.String.Input("location", multiline=False, default=""),
            ],
            outputs=[io.String.Output("reference")],
        )

    @classmethod
    def execute(cls, authors, title, journal, medline_id, pubmed_id, comment, location) -> io.NodeOutput:
        ref = Reference()
        ref.authors = authors
        ref.title = title
        ref.journal = journal
        ref.medline_id = medline_id
        ref.pubmed_id = pubmed_id
        ref.comment = comment
        ref.location = pickle.loads(base64.b64decode(location)) if location else None
        return io.NodeOutput(base64.b64encode(pickle.dumps(ref)).decode())


class Reference_summary(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Reference_summary",
            display_name="Reference summary",
            category="Biopython/Sequence Annotation Objects",
            inputs=[io.String.Input("reference", multiline=False, default="")],
            outputs=[io.String.Output("summary")],
        )

    @classmethod
    def execute(cls, reference) -> io.NodeOutput:
        ref = pickle.loads(base64.b64decode(reference))
        summary = (
            f"Reference(authors={getattr(ref, 'authors', '')!r}, title={getattr(ref, 'title', '')!r}, "
            f"journal={getattr(ref, 'journal', '')!r}, medline_id={getattr(ref, 'medline_id', '')!r}, "
            f"pubmed_id={getattr(ref, 'pubmed_id', '')!r}, comment={getattr(ref, 'comment', '')!r}, "
            f"location={getattr(ref, 'location', None)!r})"
        )
        return io.NodeOutput(summary)


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            SeqRecord_read, SeqRecord_create, SeqRecord_summary, SeqRecord_get_fields,
            SeqRecord_set_annotation, SeqRecord_set_letter_annotation, SeqRecord_set_dbxrefs,
            SeqRecord_add_feature, SeqRecord_add_reference, SeqRecord_format,
            SeqRecord_slice, SeqRecord_addition, SeqRecord_reverse_complement,
            SeqRecord_compare_attributes, Position_create, Position_summary,
            SimpleLocation_create, CompoundLocation_create, Location_summary,
            Location_contains, SeqFeature_create, SeqFeature_summary,
            SeqFeature_contains, SeqFeature_extract, Reference_create, Reference_summary,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
