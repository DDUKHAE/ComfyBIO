# Provider Readiness Report

> Note: This artifact was captured during the readiness/probe rollout and should be interpreted together with [2026-06-15-provider-smoke-comparison.md](/home/ydj/main/ComfyBIO_biopython/docs/superpowers/experiments/2026-06-15-provider-smoke-comparison.md). In particular, `codex` later succeeded in the smoke comparison with `gpt-5.5`, while `claude` failed due to a session limit despite being authenticated. The probe columns in this file are therefore historical rollout output, not the final authoritative provider verdict.

| provider | installed | authenticated | ready | probe_ok | model | probe_mode | probe_intent | probe_template_id | message | probe_error |
|---|---|---|---|---|---|---|---|---|---|---|
| deterministic | true | true | true | true | rule-based | hybrid | fasta_parse | fasta_parse | Deterministic rules engine is active |  |
| codex | true | true | true | false | gpt-5.5 | hybrid |  |  | Logged in using ChatGPT |  |
| claude | true | true | true | false | claude-sonnet-4-6 | hybrid |  |  | Logged in as dongjoon69@gmail.com | Claude CLI failed (exit 1): You've hit your session limit · resets 10:10pm (Asia/Seoul) |
| gemini | false | false | false | false | unknown | hybrid |  |  |  |  |
