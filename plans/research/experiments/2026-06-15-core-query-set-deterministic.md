# Core Query Set Deterministic Baseline

## Overall

- record_count: 10
- inter_model_agreement: 0.0000

## By Mode

| mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency | intent_match_rate | template_match_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| hybrid | 10 | 1.0000 | 0.0000 | 1.0000 | 0.9000 | 1.0000 | 1.0000 |

## By Provider and Mode

| provider | mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency | intent_match_rate | template_match_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| deterministic | hybrid | 10 | 1.0000 | 0.0000 | 1.0000 | 0.9000 | 1.0000 | 1.0000 |

## Records

| label | query | provider | model | mode | run | status | expected_intent | intent | expected_template_id | template_id | intent_match | template_match | equivalence_score | repair_applied | error_message |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|---:|---|---|
| fasta_parse_basic | parse a fasta file and summarize sequence ids | deterministic | rule-based | hybrid | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 1.0000 | false |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | deterministic | rule-based | hybrid | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 1.0000 | true |  |
| msa_basic | read an alignment file and summarize the alignment | deterministic | rule-based | hybrid | 1 | success | multiple_alignment | multiple_alignment | msa_basic | msa_basic | true | true | 1.0000 | true |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | deterministic | rule-based | hybrid | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 1.0000 | true |  |
| annotation_basic | create a sequence feature and summarize its annotation | deterministic | rule-based | hybrid | 1 | success | annotation | annotation | annotation_basic | annotation_basic | true | true | 1.0000 | true |  |
| searchio_analysis_basic | parse searchio results and inspect qresult hsps | deterministic | rule-based | hybrid | 1 | success | searchio_analysis | searchio_analysis | searchio_analysis | searchio_analysis | true | true | 1.0000 | true |  |
| pairwise_alignment_basic | run pairwise sequence alignment and inspect the best alignment | deterministic | rule-based | hybrid | 1 | success | pairwise_alignment | pairwise_alignment | pairwise_alignment | pairwise_alignment | true | true | 1.0000 | true |  |
| entrez_fetch_basic | search entrez and fetch matching records | deterministic | rule-based | hybrid | 1 | success | entrez_fetch | entrez_fetch | entrez_fetch | entrez_fetch | true | true | 1.0000 | true |  |
| pdb_structure_basic | read a pdb structure and inspect structure information | deterministic | rule-based | hybrid | 1 | success | pdb_structure_basic | pdb_structure_basic | pdb_structure_basic | pdb_structure_basic | true | true | 1.0000 | true |  |
| uniprot_lookup_basic | search uniprot for a protein accession | deterministic | rule-based | hybrid | 1 | success | uniprot_lookup | uniprot_lookup | uniprot_lookup | uniprot_lookup | true | true | 1.0000 | true |  |
