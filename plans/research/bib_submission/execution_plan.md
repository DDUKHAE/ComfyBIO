# BIB 제출 실행 계획

- Protocol ID: `COMFYBIO-BIB-001`
- 목표 저널: Briefings in Bioinformatics
- Authoritative root: `docs/superpowers/experiments/bib_submission/`
- 현재 단계: Task 1 완료

## 연구 전략

BIB 공식 scope에 맞춰 standalone software paper가 아니라 structured review, comparative benchmark 및 ComfyBIO case study를 결합한다.

## Task 상태

| Task | 작업 | 상태 | 선행 조건 |
|---:|---|---|---|
| 1 | BIB scope, protocol, requirement mapping | 완료 | 없음 |
| 2 | Structured review protocol 및 baseline registry | 대기 | Task 1 |
| 3 | Benchmark/gold/fixture/result schema와 validator | 대기 | Task 2 baseline taxonomy |
| 4 | Held-out query seed/full dataset과 leakage audit | 대기 | Task 3 |
| 5 | Independent functional gold criteria | 대기 | Task 3–4 |
| 6 | Biological fixture와 license/source manifest | 대기 | Task 4–5 |
| 7 | Expected output 및 semantic criteria | 대기 | Task 5–6 |
| 8 | Baseline/ablation matrix, power, randomization | 대기 | Task 2, 4–7 |
| 9 | Raw writer, scorer, external adapter, e2e runner | 대기 | Task 3, 8 |
| 10 | Frozen full benchmark | 대기 | Task 9 quality gate |
| 11 | Blinded expert review | 대기 | Task 10 artifact |
| 12 | Prespecified statistics와 failure synthesis | 대기 | Task 10–11 |
| 13 | Reproducibility archive와 BIB manuscript | 대기 | Task 12 |
| 14 | BIB submission-readiness audit | 대기 | Task 13 |

## Task 1 완료 기준

- [x] BIB 공식 scope와 경쟁도 확인
- [x] Standalone new-method 제한 반영
- [x] Review + benchmark + case-study framing 고정
- [x] Research question, claim, family, 포함/제외 범위 고정
- [x] External baseline gate 명시
- [x] Primary endpoint, sample size, retry, analysis 및 ethics gate 고정
- [x] Task별 디렉터리 생성
- [x] Freeze manifest 기록

## Task 2 시작 조건

Task 2는 다음 파일을 생성해야 완료된다.

- `task_02_review_baselines/review_protocol.md`
- `task_02_review_baselines/search_strings.json`
- `task_02_review_baselines/search_log.jsonl`
- `task_02_review_baselines/screening_schema.json`
- `task_02_review_baselines/baseline_registry.json`
- `task_02_review_baselines/taxonomy.md`
- `task_02_review_baselines/completion.md`

Task 2 완료 전에는 held-out query를 작성하거나 benchmark를 실행하지 않는다.

## 전역 Stop/Pause Rule

다음은 pause condition이다.

- BIB review framing을 지지할 문헌·tool coverage 부족
- External baseline selection evidence 없음
- Schema/referential integrity failure
- Positive-control execution failure
- Raw/provenance/randomization 누락
- Expert-review governance 미완료

Hybrid가 baseline보다 낮은 성능을 보이는 것은 pause condition이 아니라 보고할 결과다.
