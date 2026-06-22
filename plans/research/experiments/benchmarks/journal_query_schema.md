# 저널 자연어 Query 스키마

- 스키마 버전: `1.0.0`
- Dataset ID: `comfybio-journal-query-set-v1`
- Machine-readable schema: `docs/superpowers/experiments/schemas/journal_query_set_v1.schema.json`
- Dataset: `docs/superpowers/experiments/benchmarks/journal_query_set_v1.json`
- Validator: `scripts/validate_journal_package.py`

## 목적

이 스키마는 held-out 자연어 query, 정답 intent, 허용 가능한 template/workflow, fixture, expected output, 작성 provenance 및 leakage 검토를 하나의 추적 가능한 record로 연결한다.

기존 smoke benchmark의 단순 JSON 배열과 달리 top-level object를 사용한다. 그 이유는 schema version, dataset 상태 및 freeze 여부를 query와 분리하여 기록하기 위해서다. 기존 experiment runner와의 adapter는 Task 8에서 구현한다.

## Top-level 구조

```json
{
  "schema_version": "1.0.0",
  "dataset_id": "comfybio-journal-query-set-v1",
  "status": "draft_schema_only",
  "frozen": false,
  "queries": []
}
```

| 필드 | 형식 | 설명 |
|---|---|---|
| `schema_version` | string | 현재 `1.0.0`으로 고정 |
| `dataset_id` | string | 현재 dataset의 안정 식별자 |
| `status` | enum | `draft_schema_only`, `seed_draft`, `full_draft`, `frozen` |
| `frozen` | boolean | held-out 실행을 위한 불변 상태 여부 |
| `queries` | array | 아래 query record 목록 |

`status=frozen`이면 `frozen=true`여야 한다. 그 외 상태에서는 `frozen=false`여야 하며 validator가 이를 검사한다.

## Query record 필드

| 필드 | 필수 | 설명 |
|---|---|---|
| `schema_version` | 예 | Record schema 버전. `1.0.0` |
| `id` | 예 | `JQ001` 형식의 안정 ID |
| `label` | 예 | 소문자 snake_case label |
| `query` | 예 | 평가 대상 영어 자연어 요청 |
| `expected_intent` | 예 | 12개 primary intent 또는 `unsupported` |
| `acceptable_template_ids` | 예 | 허용 가능한 template ID 목록 |
| `acceptable_workflow_ids` | 예 | `GW_*` 형식의 허용 workflow ID 목록 |
| `functional_equivalence_group` | 예 | `FEG_*` 형식의 기능적 동등성 그룹 |
| `difficulty` | 예 | `easy`, `medium`, `hard`, `adversarial` |
| `domain` | 예 | 생물정보학 domain 분류 |
| `support_status` | 예 | `supported`, `unsupported`, `ambiguous` |
| `input_fixture_id` | 예 | `FX_*` fixture ID 또는 null |
| `expected_output_id` | 예 | `OUT_*` expected output ID 또는 null |
| `source` | 예 | Query 작성 출처 |
| `provenance` | 예 | 익명 작성자 코드, 역할, 작성 시각, 개발 참여 여부 |
| `leakage_review` | 예 | Keyword/near-duplicate 검토 상태 및 일치 항목 |
| `notes` | 예 | 예외와 판단 근거. 없으면 빈 문자열 |

Schema에 정의되지 않은 추가 필드는 허용하지 않는다. 새 필드가 필요하면 schema version과 amendment를 갱신한다.

## 허용 Intent

Primary family:

- `fasta_parse`
- `pairwise_alignment`
- `multiple_alignment`
- `blast_search`
- `searchio_analysis`
- `phylogeny`
- `annotation`
- `pdb_structure_basic`
- `motif_scan_basic`
- `entrez_fetch`
- `uniprot_lookup`
- `kegg_pathway_basic`

의도적으로 지원하지 않는 요청에는 `unsupported`를 사용한다.

## Domain

- `sequence_io`
- `alignment`
- `similarity_search`
- `phylogeny`
- `annotation`
- `structure`
- `motif`
- `external_database`

Domain은 분석용 상위 분류이며 intent와 동일하지 않다.

## 난이도 기준

### `easy`

- 단일 명확한 목적
- 일반적으로 핵심 node 1–2개
- 입력 format과 원하는 output이 직접 표현됨
- 분기나 복수 중간 산출물이 없음

### `medium`

- 일반적으로 핵심 node 2–4개
- Parse 후 summary 또는 analysis가 필요
- 한 개 이상의 parameter 또는 중간 결과 해석이 필요
- 지원 범위 안에서 의도가 명확함

### `hard`

- 일반적으로 핵심 node 4개 이상
- 여러 중간 산출물, branch 또는 비자명한 edge가 필요
- 복수 biological operation을 올바른 순서로 연결해야 함
- 단순 keyword matching만으로 충분하지 않음

### `adversarial`

다음 중 하나 이상을 의도적으로 포함한다.

- Template keyword가 없는 paraphrase
- 모호하거나 불완전한 표현
- 잘못된 format 또는 상충하는 요구
- 지원하지 않는 요청
- 시스템이 안전하게 거부·제한해야 하는 요청

`adversarial`은 항상 `unsupported`를 의미하지 않는다. 어려운 paraphrase지만 지원 가능한 query일 수 있다.

## Support status 조건

### `supported`

다음 필드는 비어 있을 수 없다.

- `acceptable_template_ids`
- `acceptable_workflow_ids`
- `functional_equivalence_group`
- `input_fixture_id`
- `expected_output_id`

### `unsupported`

- `expected_intent`는 `unsupported`
- Template/workflow 목록은 빈 배열
- Functional group, fixture 및 expected output은 null

### `ambiguous`

복수 해석이 가능하지만 평가 가능한 case에 사용한다. 허용 가능한 intent가 여러 개인 기능은 현재 schema에서 단일 `expected_intent`와 복수 template/workflow로 표현한다. Intent 자체가 복수 정답이어야 하면 schema amendment 없이 억지로 기록하지 않는다.

## Provenance

```json
{
  "author_code": "AUTHOR_01",
  "author_role": "independent_domain_expert",
  "created_at": "2026-06-22T12:00:00+09:00",
  "development_involvement": false
}
```

- 실제 이름이나 이메일을 dataset에 기록하지 않는다.
- 익명 코드와 신원 매핑이 필요하면 접근 통제된 별도 문서로 관리한다.
- Project author가 작성한 query는 `author_written_heldout`과 `development_involvement=true`로 명시한다.

## Leakage review

```json
{
  "status": "pending",
  "matched_terms": [],
  "reviewed_by": null,
  "reviewed_at": null
}
```

- `pending`: 아직 검토하지 않음
- `pass`: 허용할 수 없는 keyword 또는 near-duplicate 없음
- `flagged`: 직접 keyword 또는 유사 문장이 발견됨

`flagged` record를 자동 삭제하지 않는다. `notes`에 포함 이유를 기록하고 full benchmark 전 reviewer가 유지·수정·제외를 결정한다.

## Supported query 예시

```json
{
  "schema_version": "1.0.0",
  "id": "JQ001",
  "label": "sequence_file_summary_easy_001",
  "query": "open a sequence file and list the records it contains",
  "expected_intent": "fasta_parse",
  "acceptable_template_ids": ["fasta_parse"],
  "acceptable_workflow_ids": ["GW_fasta_parse_001"],
  "functional_equivalence_group": "FEG_fasta_summary_001",
  "difficulty": "easy",
  "domain": "sequence_io",
  "support_status": "supported",
  "input_fixture_id": "FX_FASTA_SMALL_001",
  "expected_output_id": "OUT_FASTA_SUMMARY_001",
  "source": "independent_contributor",
  "provenance": {
    "author_code": "AUTHOR_01",
    "author_role": "independent_domain_expert",
    "created_at": "2026-06-22T12:00:00+09:00",
    "development_involvement": false
  },
  "leakage_review": {
    "status": "pending",
    "matched_terms": [],
    "reviewed_by": null,
    "reviewed_at": null
  },
  "notes": ""
}
```

이 예시는 schema 설명용이며 `journal_query_set_v1.json`에 자동 포함하지 않는다.

## Validator phase

```bash
python scripts/validate_journal_package.py \
  --query-json docs/superpowers/experiments/benchmarks/journal_query_set_v1.json \
  --phase draft
```

| Phase | 검사 |
|---|---|
| `draft` | Root/record 구조, type, enum, ID, 조건부 필드, 중복 |
| `seed` | `draft` + query 30개 이상 + family별 최소 2개 |
| `full` | `seed` + 정확히 120개 + 난이도 분포 36/48/24/12 + leakage review 완료 |
| `package` | `full` + fixture/output/gold index referential integrity |

## Referential integrity

`package` phase에서는 다음 참조가 실제 index에 존재해야 한다.

- `acceptable_workflow_ids` → `gold_workflows/index.json`
- `input_fixture_id` → `fixtures/fixture_manifest.json`
- `expected_output_id` → `expected_outputs/index.json`

해당 index는 Task 4–6에서 생성하므로 Task 2와 Task 3에서는 `draft`, `seed`, `full` phase를 사용한다.

## Freeze 규칙

- `journal_query_set_v1.json`은 Task 2 종료 시 `draft_schema_only`, `frozen=false`다.
- Task 3 seed 작성 시 `seed_draft`로 변경한다.
- 120개 작성 후 검토 중에는 `full_draft`를 사용한다.
- 모든 validation과 독립 검토가 끝나면 `frozen=true`, `status=frozen`으로 변경하고 SHA-256을 기록한다.
- 첫 held-out 실행 후 query 변경은 원본을 보존하는 protocol amendment로만 수행한다.
