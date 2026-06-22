# Provider Smoke Comparison

## Overall

- record_count: 27
- inter_model_agreement: 0.2222

## By Mode

| mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency | intent_match_rate | template_match_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| free | 9 | 0.6667 | 0.0000 | 0.2444 | 0.0000 | 1.0000 | 1.0000 |
| hybrid | 9 | 0.6667 | 0.0000 | 0.6556 | 0.4444 | 1.0000 | 1.0000 |
| normalized | 9 | 0.6667 | 0.0000 | 0.2444 | 0.0000 | 1.0000 | 1.0000 |

## By Provider and Mode

| provider | mode | records | valid_json_rate | executable_workflow_rate | mean_equivalence_score | repair_frequency | intent_match_rate | template_match_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| claude | free | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| claude | hybrid | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| claude | normalized | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| codex | free | 3 | 1.0000 | 0.0000 | 0.4000 | 0.0000 | 1.0000 | 1.0000 |
| codex | hybrid | 3 | 1.0000 | 0.0000 | 0.9667 | 0.6667 | 1.0000 | 1.0000 |
| codex | normalized | 3 | 1.0000 | 0.0000 | 0.4000 | 0.0000 | 1.0000 | 1.0000 |
| deterministic | free | 3 | 1.0000 | 0.0000 | 0.3333 | 0.0000 | 1.0000 | 1.0000 |
| deterministic | hybrid | 3 | 1.0000 | 0.0000 | 1.0000 | 0.6667 | 1.0000 | 1.0000 |
| deterministic | normalized | 3 | 1.0000 | 0.0000 | 0.3333 | 0.0000 | 1.0000 | 1.0000 |

## Records

| label | query | provider | model | mode | run | status | expected_intent | intent | expected_template_id | template_id | intent_match | template_match | equivalence_score | repair_applied | error_message |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|---:|---|---|
| fasta_parse_basic | parse a fasta file and summarize sequence ids | deterministic | rule-based | free | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 1.0000 | false |  |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | deterministic | rule-based | normalized | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 1.0000 | false |  |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | deterministic | rule-based | hybrid | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 1.0000 | false |  |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | codex | gpt-5.5 | free | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 0.2000 | false |  |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | codex | gpt-5.5 | normalized | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 0.2000 | false |  |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | codex | gpt-5.5 | hybrid | 1 | success | fasta_parse | fasta_parse | fasta_parse | fasta_parse | true | true | 1.0000 | true |  |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | claude | claude-sonnet-4-6 | free | 1 | error | fasta_parse |  | fasta_parse |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | claude | claude-sonnet-4-6 | normalized | 1 | error | fasta_parse |  | fasta_parse |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| fasta_parse_basic | parse a fasta file and summarize sequence ids | claude | claude-sonnet-4-6 | hybrid | 1 | error | fasta_parse |  | fasta_parse |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| blast_search_basic | run blast against a nucleotide database and inspect hits | deterministic | rule-based | free | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 0.0000 | false |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | deterministic | rule-based | normalized | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 0.0000 | false |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | deterministic | rule-based | hybrid | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 1.0000 | true |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | codex | gpt-5.5 | free | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 0.0000 | false |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | codex | gpt-5.5 | normalized | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 0.0000 | false |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | codex | gpt-5.5 | hybrid | 1 | success | blast_search | blast_search | blast_basic | blast_basic | true | true | 0.9000 | true |  |
| blast_search_basic | run blast against a nucleotide database and inspect hits | claude | claude-sonnet-4-6 | free | 1 | error | blast_search |  | blast_basic |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| blast_search_basic | run blast against a nucleotide database and inspect hits | claude | claude-sonnet-4-6 | normalized | 1 | error | blast_search |  | blast_basic |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| blast_search_basic | run blast against a nucleotide database and inspect hits | claude | claude-sonnet-4-6 | hybrid | 1 | error | blast_search |  | blast_basic |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | deterministic | rule-based | free | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 0.0000 | false |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | deterministic | rule-based | normalized | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 0.0000 | false |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | deterministic | rule-based | hybrid | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 1.0000 | true |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | codex | gpt-5.5 | free | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 1.0000 | false |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | codex | gpt-5.5 | normalized | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 1.0000 | false |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | codex | gpt-5.5 | hybrid | 1 | success | phylogeny | phylogeny | phylogeny_basic | phylogeny_basic | true | true | 1.0000 | false |  |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | claude | claude-sonnet-4-6 | free | 1 | error | phylogeny |  | phylogeny_basic |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | claude | claude-sonnet-4-6 | normalized | 1 | error | phylogeny |  | phylogeny_basic |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| phylogeny_basic | read a phylogenetic tree file and inspect tree information | claude | claude-sonnet-4-6 | hybrid | 1 | error | phylogeny |  | phylogeny_basic |  |  |  | 0.0000 | false | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
