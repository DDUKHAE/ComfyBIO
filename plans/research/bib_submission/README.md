# BIB 제출 트랙

- 목표 저널: **Briefings in Bioinformatics (BIB)**
- Protocol ID: `COMFYBIO-BIB-001`
- 시작일: 2026-06-22
- 문서 기본 언어: 한국어
- 상태: Task 1 완료, held-out 실행 금지

## 목적

이 디렉터리는 BIB 제출을 위한 독립 연구 트랙이다. 기존 `docs/superpowers/experiments/`의 journal 문서는 감사·비교 기록으로 보존하며 이 트랙의 authoritative artifact로 사용하지 않는다.

BIB 공식 지침에 따라 논문을 standalone new-method software paper가 아니라 다음 세 요소의 결합으로 설계한다.

1. 자연어 기반 생물정보학 워크플로우 생성 분야의 구조화된 review
2. 공개·재현 가능한 comparative benchmark
3. ComfyBIO hybrid approach의 case study

## Task별 디렉터리

| Task | 디렉터리 | 핵심 산출물 |
|---:|---|---|
| 1 | `task_01_scope_protocol/` | BIB scope, protocol, requirement mapping, freeze manifest |
| 2 | `task_02_review_baselines/` | Review protocol, search strategy, baseline registry |
| 3 | `task_03_benchmark_schema/` | Query/gold/fixture/result schema 및 validator |
| 4 | `task_04_query_dataset/` | Held-out query seed/full dataset, leakage audit |
| 5 | `task_05_gold_criteria/` | Independent functional gold criteria, reference workflow |
| 6 | `task_06_bio_fixtures/` | Real/synthetic biological fixture, source/license manifest |
| 7 | `task_07_expected_outputs/` | Expected output과 semantic success criteria |
| 8 | `task_08_experiment_matrix/` | Baseline/ablation matrix, randomization, power check |
| 9 | `task_09_e2e_runner/` | Raw writer, scorer, headless ComfyUI e2e runner |
| 10 | `task_10_full_benchmark/` | Frozen benchmark raw run과 mode/baseline comparison |
| 11 | `task_11_expert_review/` | Blinded expert review package와 agreement |
| 12 | `task_12_statistical_analysis/` | Prespecified statistics, sensitivity/failure analysis |
| 13 | `task_13_reproducibility_manuscript/` | Archive, DOI, manuscript tables/figures/draft |
| 14 | `task_14_submission_audit/` | BIB checklist, claim audit, go/no-go |

## 디렉터리 규칙

- 새 산출물은 해당 Task 디렉터리 안에 생성한다.
- 여러 Task가 공유하는 파일은 최초 생성 Task가 소유하고 후속 Task는 상대 경로로 참조한다.
- Raw data는 수정하지 않고 append-only 또는 immutable run directory로 보존한다.
- Task 완료 시 해당 디렉터리에 `completion.md`와 hash manifest를 남긴다.
- Held-out 결과를 본 뒤 protocol, endpoint, benchmark membership 또는 제외 기준을 변경하지 않는다.
- 변경이 필요하면 원문과 새 문장을 모두 포함한 amendment를 Task 1 디렉터리에 기록한다.

## BIB 핵심 제약

BIB 공식 지침은 아직 다른 곳에 기술되지 않은 신방법만을 단독으로 소개하는 논문을 원칙적으로 받지 않으며, 해당 분야의 더 넓은 review 맥락을 요구한다. 따라서 ComfyBIO는 논문 전체가 아니라 review 및 benchmark 안의 case study다.

BIB가 명시적으로 관심을 두는 software comparison and benchmarking, predicted/extracted information의 정확성, text mining, tool selection과 limitation 해석을 연구 중심에 둔다.

공식 출처:

- [BIB 저자 지침](https://academic.oup.com/bib/pages/General_Instructions)
- [BIB 저널 소개 및 지표](https://academic.oup.com/bib/pages/About)

## 현재 실행 제한

Task 2의 review/baseline registry와 Task 3의 schema가 완료되기 전에는 journal benchmark query를 생성하거나 실행하지 않는다. 기존 smoke query는 개발 근거로만 사용한다.
