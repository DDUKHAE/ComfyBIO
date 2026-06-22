from __future__ import annotations
import base64
import pickle
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import ComfyExtension, io
# pyrefly: ignore [missing-import]
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.MMCIFParser import MMCIFParser
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB import PDBIO, MMCIFIO, Superimposer, NeighborSearch


class _Base(io.ComfyNode):
    OUTPUT_NODE = True


class PDB_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_read",
            display_name="PDB read",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.String.Input("structure_id", multiline=False, default="structure"),
            ],
            outputs=[
                io.String.Output("structure"),
                io.String.Output("structure_id"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, file_path, structure_id) -> io.NodeOutput:
        parser = PDBParser(PERMISSIVE=1)
        structure = parser.get_structure(structure_id, file_path)
        chains = []
        for model in structure:
            for chain in model:
                chains.append("Model%d/Chain%s (%d residues)" % (model.id, chain.id, len(chain)))
        summary = "\n".join(chains)
        return io.NodeOutput(base64.b64encode(pickle.dumps(structure)).decode(), structure.id, summary)


class MMCIF_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="MMCIF_read",
            display_name="mmCIF read",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.String.Input("structure_id", multiline=False, default="structure"),
            ],
            outputs=[
                io.String.Output("structure"),
                io.String.Output("structure_id"),
                io.String.Output("summary"),
            ],
        )

    @classmethod
    def execute(cls, file_path, structure_id) -> io.NodeOutput:
        parser = MMCIFParser(QUIET=True)
        structure = parser.get_structure(structure_id, file_path)
        chains = []
        for model in structure:
            for chain in model:
                chains.append("Model%d/Chain%s (%d residues)" % (model.id, chain.id, len(chain)))
        return io.NodeOutput(base64.b64encode(pickle.dumps(structure)).decode(), structure.id, "\n".join(chains))


class MMCIF2Dict_read(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="MMCIF2Dict_read",
            display_name="mmCIF2Dict read",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("file_path", multiline=False, default=""),
                io.String.Input("tag", multiline=False, default="_exptl_crystal.density_percent_sol"),
            ],
            outputs=[io.String.Output("value"), io.String.Output("all_tags")],
        )

    @classmethod
    def execute(cls, file_path, tag) -> io.NodeOutput:
        d = MMCIF2Dict(file_path)
        value = str(d.get(tag, ""))
        all_tags = "\n".join(sorted(d.keys())[:50])
        return io.NodeOutput(value, all_tags)


class PDB_structure_info(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_structure_info",
            display_name="PDB structure info",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("structure", multiline=False, default=""),
                io.Combo.Input("level", options=["structure", "model", "chain", "residue", "atom"], default="chain"),
            ],
            outputs=[io.String.Output("info"), io.Int.Output("count")],
        )

    @classmethod
    def execute(cls, structure, level) -> io.NodeOutput:
        s = pickle.loads(base64.b64decode(structure))
        if level == "structure":
            info = "Structure: %s\nModels: %d" % (s.id, len(list(s.get_models())))
            count = 1
        elif level == "model":
            models = list(s.get_models())
            info = "\n".join("Model %s" % m.id for m in models)
            count = len(models)
        elif level == "chain":
            chains = list(s.get_chains())
            info = "\n".join("Chain %s (%d residues)" % (c.id, len(c)) for c in chains)
            count = len(chains)
        elif level == "residue":
            residues = list(s.get_residues())
            info = "\n".join("%s %s" % (r.get_resname(), r.id[1]) for r in residues[:50])
            count = len(residues)
        else:
            atoms = list(s.get_atoms())
            info = "\n".join("%s" % a.get_name() for a in atoms[:50])
            count = len(atoms)
        return io.NodeOutput(info, count)


class PDB_get_chain(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_get_chain",
            display_name="PDB get chain",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("structure", multiline=False, default=""),
                io.Int.Input("model_index", min=0, step=1, default=0, display_mode=io.NumberDisplay.number),
                io.String.Input("chain_id", multiline=False, default="A"),
            ],
            outputs=[
                io.String.Output("chain"),
                io.Int.Output("residue_count"),
                io.String.Output("sequence"),
            ],
        )

    @classmethod
    def execute(cls, structure, model_index, chain_id) -> io.NodeOutput:
        s = pickle.loads(base64.b64decode(structure))
        model = list(s.get_models())[model_index]
        chain = model[chain_id]
        residues = list(chain.get_residues())
        seq = "".join(r.get_resname().strip() for r in residues[:100])
        return io.NodeOutput(base64.b64encode(pickle.dumps(chain)).decode(), len(residues), seq)


class PDB_header(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_header",
            display_name="PDB header",
            category="Biopython/PDB",
            inputs=[io.String.Input("structure", multiline=False, default="")],
            outputs=[
                io.String.Output("name"),
                io.String.Output("resolution"),
                io.String.Output("keywords"),
                io.String.Output("deposition_date"),
            ],
        )

    @classmethod
    def execute(cls, structure) -> io.NodeOutput:
        s = pickle.loads(base64.b64decode(structure))
        h = s.header
        return io.NodeOutput(
            str(h.get("name", "")),
            str(h.get("resolution", "")),
            str(h.get("keywords", "")),
            str(h.get("deposition_date", "")),
        )


class PDB_write(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_write",
            display_name="PDB write",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("structure", multiline=False, default=""),
                io.String.Input("file_path", multiline=False, default="output.pdb"),
                io.Combo.Input("format", options=["pdb", "mmcif"], default="pdb"),
            ],
            outputs=[io.String.Output("file_path")],
        )

    @classmethod
    def execute(cls, structure, file_path, format) -> io.NodeOutput:
        s = pickle.loads(base64.b64decode(structure))
        if format == "pdb":
            writer = PDBIO()
        else:
            writer = MMCIFIO()
        writer.set_structure(s)
        writer.save(file_path)
        return io.NodeOutput(file_path)


class PDB_superimpose(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_superimpose",
            display_name="PDB superimpose",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("structure_fixed", multiline=False, default=""),
                io.String.Input("structure_moving", multiline=False, default=""),
                io.String.Input("chain_id", multiline=False, default="A"),
            ],
            outputs=[
                io.String.Output("structure_moved"),
                io.Float.Output("rmsd"),
            ],
        )

    @classmethod
    def execute(cls, structure_fixed, structure_moving, chain_id) -> io.NodeOutput:
        import copy
        sf = pickle.loads(base64.b64decode(structure_fixed))
        sm = pickle.loads(base64.b64decode(structure_moving))
        sm_copy = copy.deepcopy(sm)
        fixed_atoms = list(list(sf.get_models())[0][chain_id].get_atoms())
        moving_atoms = list(list(sm_copy.get_models())[0][chain_id].get_atoms())
        n = min(len(fixed_atoms), len(moving_atoms))
        sup = Superimposer()
        sup.set_atoms(fixed_atoms[:n], moving_atoms[:n])
        sup.apply(sm_copy.get_atoms())
        return io.NodeOutput(base64.b64encode(pickle.dumps(sm_copy)).decode(), sup.rms)


class PDB_neighbor_search(_Base):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PDB_neighbor_search",
            display_name="PDB neighbor search",
            category="Biopython/PDB",
            inputs=[
                io.String.Input("structure", multiline=False, default=""),
                io.Float.Input("center_x", min=-1000.0, step=0.1, default=0.0),
                io.Float.Input("center_y", min=-1000.0, step=0.1, default=0.0),
                io.Float.Input("center_z", min=-1000.0, step=0.1, default=0.0),
                io.Float.Input("radius", min=0.0, step=0.5, default=5.0),
                io.Combo.Input("level", options=["A", "R", "C"], default="R"),
            ],
            outputs=[io.String.Output("neighbors"), io.Int.Output("count")],
        )

    @classmethod
    def execute(cls, structure, center_x, center_y, center_z, radius, level) -> io.NodeOutput:
        s = pickle.loads(base64.b64decode(structure))
        atoms = list(s.get_atoms())
        ns = NeighborSearch(atoms)
        center = (center_x, center_y, center_z)
        results = ns.search(center, radius, level=level)
        info = "\n".join(str(r) for r in results[:50])
        return io.NodeOutput(info, len(results))


class ExampleExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            PDB_read,
            MMCIF_read,
            MMCIF2Dict_read,
            PDB_structure_info,
            PDB_get_chain,
            PDB_header,
            PDB_write,
            PDB_superimpose,
            PDB_neighbor_search,
        ]


async def comfy_entrypoint() -> ExampleExtension:
    return ExampleExtension()
