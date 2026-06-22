# Deterministic Mode Smoke Run

## Overall

- record_count: 6
- inter_model_agreement: 1.0000

## By Mode

| mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency |
|---|---:|---:|---:|---:|---:|
| free | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| hybrid | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| normalized | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |

## By Provider and Mode

| provider | mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency |
|---|---|---:|---:|---:|---:|---:|
| deterministic | free | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| deterministic | hybrid | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| deterministic | normalized | 2 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |

## Records

| query | provider | model | mode | run | status | intent | template_id | equivalence_score | repair_applied | error_message |
|---|---|---|---|---:|---|---|---|---:|---|---|
| parse a fasta file and summarize sequence ids | deterministic | rule-based | free | 1 | success | fasta_parse | fasta_parse | 1.0000 | false |  |
| parse a fasta file and summarize sequence ids | deterministic | rule-based | free | 2 | success | fasta_parse | fasta_parse | 1.0000 | false |  |
| parse a fasta file and summarize sequence ids | deterministic | rule-based | normalized | 1 | success | fasta_parse | fasta_parse | 1.0000 | false |  |
| parse a fasta file and summarize sequence ids | deterministic | rule-based | normalized | 2 | success | fasta_parse | fasta_parse | 1.0000 | false |  |
| parse a fasta file and summarize sequence ids | deterministic | rule-based | hybrid | 1 | success | fasta_parse | fasta_parse | 1.0000 | false |  |
| parse a fasta file and summarize sequence ids | deterministic | rule-based | hybrid | 2 | success | fasta_parse | fasta_parse | 1.0000 | false |  |
