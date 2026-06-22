# Template Coverage and Quality Benchmark

| template_id | intent | category | req_nodes | req_edges | opt_nodes | exact | missing_edge | extra_node | repaired | repair_applied |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| annotation_basic | annotation | Biopython/Sequence Annotation Objects | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| blast_basic | blast_search | Biopython/BLAST, Biopython/SearchIO | 4 | 3 | 2 | 1.00 | 0.80 | 0.90 | 1.00 | true |
| cluster_basic | cluster_basic | Biopython/Cluster | 2 | 1 | 3 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| entrez_fetch | entrez_fetch | Biopython/Entrez | 2 | 1 | 1 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| fasta_parse | fasta_parse | Biopython/SeqIO | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| graphics_basic | graphics_basic | Biopython/Graphics, Biopython/Sequence Annotation Objects | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| kegg_enzyme_file_basic | kegg_enzyme_file_basic | Biopython/KEGG | 1 | 0 | 1 | 1.00 | 1.00 | 0.90 | 1.00 | true |
| kegg_pathway_basic | kegg_pathway_basic | Biopython/KEGG | 1 | 0 | 3 | 1.00 | 1.00 | 0.90 | 1.00 | true |
| motif_scan_basic | motif_scan_basic | Biopython/Motif | 2 | 1 | 3 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| msa_basic | multiple_alignment | Biopython/Alignment | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| pairwise_alignment | pairwise_alignment | Biopython/Pairwise | 2 | 1 | 1 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| pdb_chain_analysis | pdb_chain_analysis | Biopython/PDB | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| pdb_structure_basic | pdb_structure_basic | Biopython/PDB | 2 | 1 | 3 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| phylogeny_basic | phylogeny | Biopython/Phylo | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| popgen_basic | popgen_basic | Biopython/PopGen | 2 | 1 | 3 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| searchio_analysis | searchio_analysis | Biopython/SearchIO | 3 | 2 | 2 | 1.00 | 0.70 | 0.90 | 1.00 | true |
| sequence_annotation_edit | sequence_annotation_edit | Biopython/SeqIO, Biopython/Sequence Annotation Objects | 3 | 2 | 2 | 1.00 | 0.70 | 0.90 | 1.00 | true |
| sequence_objects_basic | sequence_objects_basic | Biopython/Sequence Objects | 2 | 1 | 2 | 1.00 | 0.40 | 0.90 | 1.00 | true |
| uniprot_lookup | uniprot_lookup | Biopython/UniProt | 1 | 0 | 0 | 1.00 | 1.00 | 0.90 | 1.00 | true |

## Notes

- `exact`: score for the synthetic canonical spec built from required nodes/edges.
- `missing_edge`: score after removing one required edge when available.
- `extra_node`: score after injecting one non-template node.
- `repaired`: score after running `repair_workflow_spec()` on the extra-node case.
