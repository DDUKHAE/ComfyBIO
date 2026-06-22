# ComfyBIO 식물 육종 확장 & 멀티모달 타당성 검토

- **문서 성격**: 연구 제안서 · 타당성 검토 (구현 명세가 아님)
- **작성일**: 2026-06-04
- **대상 시스템**: `ComfyBIO_biopython` (ComfyUI 커스텀 노드 + LLM 기반 워크플로우 생성 엔진)
- **확장 전략**: A 아키텍처(기존 구조 재활용) + C 순서(멀티모달 수직 슬라이스 우선)

---

## 1. 목표와 배경

### 1.1 목표
현재 Biopython 노드만 다루는 LLM 기반 워크플로우 생성 프로젝트를 두 방향으로 확장한다.

1. **식물 육종 활용**: 육종 분석 노드 추가, 표현형/필드 데이터 처리, 외부 육종 DB/툴 연동, LLM 엔진의 도메인 인식 확장.
2. **멀티모달 가능성 검증(PoC)**: 표현형 이미지를 입력받아 멀티모달 LLM이 적절한 분석 워크플로우를 생성할 수 있는지 타당성을 확인.

본 문서는 "각 방향이 기술적으로 되는가, 무엇을 먼저 해야 하는가"를 판단하기 위한 타당성 검토이며, 상세 구현 명세는 후속 단계(writing-plans)에서 Phase별로 작성한다.

### 1.2 현행 시스템 분석 (확장의 출발점)
3계층 구조로 이루어져 있다.

| 계층 | 위치 | 역할 |
|------|------|------|
| 노드 계층 | `py/*.py` | Biopython 기반 159개 노드(Align, BLAST, Entrez, KEGG, Phylo, PopGen, SeqIO, PDB, Motif, Cluster, Graphics, Phenotype 등). 각 노드는 `io.Schema`로 정의되고 ComfyUI에 등록된다. |
| 레지스트리/프롬프트 | `harness_core/build_registry.py`, `node_registry.json`, `biopython_prompts.py` | `build_registry.py`가 `py/*.py`를 **AST로 파싱**해 `node_registry.json` 생성. `biopython_prompts.py`가 이를 압축 카탈로그 문자열로 변환해 LLM 프롬프트에 주입. |
| LLM 엔진 | `harness_core/llm_runner.py`, `llm_adapters/{claude,codex,gemini}_cli.py` | goal(텍스트) → provider(CLI 래퍼) 호출 → 노드/엣지 spec(JSON) 생성 → `llm_contracts.parse_and_validate_llm_output`로 검증. |

**핵심 관찰**:
- 노드는 `io.Schema` 패턴만 따르면 `build_registry.py`가 자동 수집한다 → **새 노드 추가 시 엔진 코드 무수정**.
- 현재 모달리티는 텍스트 단일 경로다(goal 문자열 → 노드 선택). 이미지 입력 경로가 없다.
- 객체(SeqRecord, Alignment 등)는 STRING(base64+pickle)으로 직렬화되어 노드 간 S→S로 연결된다.

---

## 2. 아키텍처 원칙 — 변경 최소화 (A안)

기존 3계층을 그대로 유지·재활용하며, 추가는 "새 파일"과 "어댑터 시그니처 확장"으로 흡수한다.

- **노드 계층**: 육종 노드를 *새 `py/*.py` 파일*로만 추가. 기존 `io.Schema` 패턴을 따르면 `build_registry.py`가 자동 등록한다. → 엔진 코드 무수정.
- **레지스트리/프롬프트**: `node_registry.json` 재생성 + `biopython_prompts.py`에 육종 도메인 힌트 보강.
- **LLM 엔진**: `llm_runner.py` 인터페이스 유지. 멀티모달은 어댑터 `generate(prompt, ..., image_paths=...)` 시그니처 확장으로 흡수(기존 호출부는 기본값으로 영향 없음).

### 도메인 팩 분리(B안)은 "장래 옵션"
육종 노드가 늘면 카탈로그(현재 159줄)가 비대해져 LLM 노드 선택 정확도에 영향을 줄 수 있다. 이때 **육종을 별도 레지스트리/프롬프트 모듈로 분리하고 엔진이 도메인별로 라우팅**하는 도메인 팩(B안)을 도입한다. 단, 선(先)리팩토링은 과설계이므로 **카탈로그 비대가 실측될 때** 도입하는 트리거 기반 옵션으로만 남긴다(§3.4, §4 참조).

---

## 3. 확장 계획 (Phase별)

### Phase 1 — 멀티모달 PoC 수직 슬라이스 (최우선, 리스크 선해소)

가장 새롭고 불확실한 가설(멀티모달)을 먼저 검증한다.

**앵커 시나리오**: 사용자가 잎/병해/종자 사진을 첨부 → 멀티모달 LLM이 이미지를 해석 → 적절한 측정·분석 워크플로우(노드 spec) 생성.

**타당성 핵심 질문 — CLI 래퍼가 이미지를 받는가?**
- 멀티모달 LLM 접근은 **CLI 래퍼 유지**를 전제로 한다(API/SDK 전환 아님).
- gemini CLI는 프롬프트 내 `@경로` 파일 참조(이미지 포함)를 지원하며, claude CLI도 경로 참조가 가능한 것으로 알려져 있다. → 어댑터 `generate`에 `image_paths` 인자를 추가하고, 프롬프트에 `@경로`를 주입하는 방식이 후보다.
- 단, provider별 실제 동작은 불확실하므로 **문서/계획에 "실측 검증 단계"를 명시**한다: 어떤 CLI가 실제로 이미지를 모델까지 통과시키는지 확인하는 최소 실험을 Phase 1의 첫 작업으로 둔다.

**최소 육종 노드**: 앵커 시나리오를 지탱할 정도만 신설(예: 표현형 이미지 측정 노드 스텁 1~2개). 폭넓은 노드군은 Phase 2로 미룬다.

**성공 기준 (measurable)**:
1. 이미지 첨부가 선택된 CLI를 통과해 모델에 도달한다.
2. LLM이 이미지 내용을 반영한 노드 선택을 한다(텍스트만 줬을 때와 구별되는 결과).
3. 생성된 spec이 `parse_and_validate_llm_output(expected_type="biopython_workflow_spec")`를 통과한다.

**Phase 1 산출물**: 이미지 경로를 통과시키는 어댑터 1종 + 앵커 시나리오 데모 + 실측 검증 기록.

### Phase 2 — 육종 분석 노드군 (개요)
기존 노드 패턴을 따라 새 `py/*.py`로 추가:
- GWAS(전장유전체 연관분석)
- 유전체 선발 GS / GEBV 예측
- 마커보조선발 MAS
- QTL 매핑
- 연관지도(linkage map)
- VCF/유전형 데이터 I/O

### Phase 3 — 표현형/필드 데이터 처리 (개요)
> ⚠️ **중요 구분**: 현재 `py/Phenotype_Objects.py`는 `Bio.phenotype`(표현형 **마이크로어레이/생장곡선**) 기반으로, **식물 형질(trait) 데이터가 아니다.** 따라서 육종용 표현형 — 형질 측정치, 시험포장 설계(experimental design), 형질-마커 연관 — 노드는 **별도 신설**이 필요하다. 기존 노드 확장으로 오인하지 않도록 한다.

### Phase 4 — 외부 육종 DB/툴 연동 (개요)
- 데이터베이스: Ensembl Plants, Gramene, GrainGenes, BrAPI
- 툴: TASSEL, PLINK 등 (대부분 외부 프로세스 래퍼 노드 형태가 될 가능성, §4 리스크 참조)

### Phase 5 — LLM 엔진 도메인 인식 확장 (개요)
프롬프트가 형질·계통·세대 등 육종 개념을 이해하고 워크플로우를 짜도록 `biopython_prompts.py`를 점진 보강. 카탈로그 비대가 노드 선택 정확도를 떨어뜨리는 것이 실측되면 도메인 팩(B안) 도입을 검토한다.

---

## 4. 타당성 / 리스크

| 리스크 | 내용 | 완화 |
|--------|------|------|
| CLI 이미지 통과 불확실성 | provider별로 이미지를 모델까지 전달하는지 미확인 | Phase 1 첫 작업에서 최소 실험으로 선검증 |
| 외부 육종 라이브러리 생태계 | 육종 도구 상당수가 R/CLI(TASSEL, PLINK 등)로, 순수 Python(Biopython류) 자산이 얕음 | 노드를 외부 프로세스 래퍼로 설계하는 방안 수용 |
| 카탈로그 비대 | 노드 수 증가(159→200+)가 LLM 노드 선택 정확도에 영향 | 도메인 팩(B안)을 트리거 기반 옵션으로 준비 |
| 표현형 개념 혼동 | 기존 `Phenotype_Objects`(마이크로어레이)와 육종 표현형(형질) 혼동 | 별도 노드군으로 명확히 분리(§3 Phase 3) |

---

## 5. 문서 산출물 구성

본 문서(`docs/superpowers/specs/2026-06-04-breeding-multimodal-expansion-design.md`)가 연구 제안서·타당성 검토 산출물이다. 구성: 목표/배경 → 현행 분석 → 아키텍처 원칙 → Phase별 계획 → 성공 기준 → 리스크.

**다음 단계**: 본 검토 승인 후, Phase 1(멀티모달 PoC 수직 슬라이스)에 대해 writing-plans로 상세 구현 계획을 작성한다. Phase 2~5는 본 문서의 로드맵 수준으로 유지하며, 착수 시점에 각각 별도 spec → plan 사이클로 상세화한다.
