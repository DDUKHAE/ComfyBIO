# Codex Diagnostic

## Overall

- record_count: 1
- inter_model_agreement: 0.0000

## By Mode

| mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency | intent_match_rate | template_match_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| free | 1 | 1.0000 | 0.0000 | 0.2000 | 0.0000 | 0.0000 | 0.0000 |

## By Provider and Mode

| provider | mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency | intent_match_rate | template_match_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| codex | free | 1 | 1.0000 | 0.0000 | 0.2000 | 0.0000 | 0.0000 | 0.0000 |

## Records

| label | query | provider | model | mode | run | status | expected_intent | intent | expected_template_id | template_id | intent_match | template_match | equivalence_score | repair_applied | error_message |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|---:|---|---|
| parse a fasta file and summarize sequence ids | parse a fasta file and summarize sequence ids | codex | gpt-5.5 | free | 1 | success |  | fasta_parse |  | fasta_parse |  |  | 0.2000 | false |  |
