# BIB 논문 개발 진행 보고

- 작성일: 2026-06-22
- 브랜치: master
- 현재 태그: `foundation-v1.0`

---

## 1. 전체 방향 전환 (오늘 확정)

### 기존 framing
ComfyBIO 단일 소프트웨어를 bioinformatics workflow generation case study로 제시.

### 새 framing
ComfyUI를 visual workflow management system(WMS)으로 활용한 자연어 기반 분석 워크플로우 생성 프레임워크를, 생명과학 5개 도메인 multi-domain benchmark로 검증.

**잠정 제목:**
> Natural Language-Driven Analysis Workflow Generation Using ComfyUI as a Visual Workflow Management System: A Multi-Domain Benchmark Across Life Sciences

### 5개 Case Study 도메인

| CS | 이름 | 핵심 도구 | 핵심 NL 챌린지 |
|----|------|----------|---------------|
| CS1 | ComfyBIO | Biopython | 서열 어휘 정확도 |
| CS2 | ComfyTranscriptomics | Scanpy/DESeq2/STAR | bulk vs sc 분기 추론, 샘플수 기반 tool 선택 |
| CS3 | ComfyChem | RDKit/AutoDock Vina | 화학 전문 어휘 파싱 |
| CS4 | ComfyProteomics | MaxQuant/MSFragger | 실험 설계 타입(LFQ vs TMT) 추론 |
| CS5 | ComfyEpigenomics | Bowtie2/MACS3/Bismark | ChIP vs ATAC vs bisulfite 기법 분류 |

### 핵심 설계 원칙

- **Tool Selection Registry (TSR)**: 랜덤이 아닌 데이터 컨텍스트 기반 deterministic rule로 tool 선택. nf-core 파이프라인·공인 benchmark 논문 기반.
- **Multi-path Gold Criteria**: canonical / alternative-valid / INVALID 3계층 판정. functional equivalence 기준으로 복수 tool path를 모두 정답으로 인정.
- **Domain-as-Project**: 각 도메인이 12개 workflow family + tool landscape tree를 가진 소규모 프로젝트.
- **Cross-domain Meta-analysis**: 5개 도메인 독립 benchmark 후 failure taxonomy, tool selection accuracy, adversarial robustness 비교.

---

## 2. 오늘 완료된 산출물

### 2-1. 설계 문서

| 파일 | 내용 |
|------|-----|
| `docs/superpowers/specs/2026-06-22-multi-domain-workflow-design.md` | 전체 논문 재프레이밍 설계 spec |
| `docs/superpowers/plans/2026-06-22-multi-domain-foundation-plan.md` | Foundation 구현 plan (7 tasks) |

### 2-2. Foundation 구현 (`foundation-v1.0`)

총 8개 커밋, 95개 테스트 통과, 회귀 없음.

#### 신규 패키지 구조

```
llm_interface/llm_core/
  tsr/
    __init__.py          # TSREngine, load_domain_tsr, list_domains export
    schema.py            # ToolValidity, ToolChoice, StepRule, DomainTSR
    engine.py            # TSREngine — AST 기반 안전 rule 평가기
    loader.py            # YAML → DomainTSR, deepcopy로 캐시 격리
    domains/
      bioinformatics.yaml  # CS1 규칙 (6 steps)
      transcriptomics.yaml # CS2 규칙 (8 steps, 분기 포함)
  gold/
    __init__.py          # TieredGold, GoldEvaluator, Verdict export
    schema.py            # Verdict, CanonicalGold, AlternativeGold, AdversarialOverride, TieredGold
    evaluator.py         # GoldEvaluator — tiered 판정 + functional equivalence
  benchmark/
    __init__.py          # DomainPlugin, HeldOutQuery, ToolSpecificity, Difficulty export
    query_schema.py      # HeldOutQuery, ToolSpecificity, Difficulty
    domain_plugin.py     # DomainPlugin ABC
```

#### 테스트 파일 (신규 29개)

```
tests/llm_core/
  test_tsr_schema.py      # 3 tests
  test_tsr_engine.py      # 8 tests
  test_tsr_loader.py      # 6 tests
  test_gold_schema.py     # 2 tests
  test_gold_evaluator.py  # 5 tests
  test_query_schema.py    # 3 tests
  test_domain_plugin.py   # 2 tests
```

#### 커밋 이력

| 해시 | 메시지 |
|------|-------|
| `5ce89cd3` | feat(tsr): add TSR schema dataclasses |
| `1c53a4c9` | feat(tsr): add TSREngine rule evaluator |
| `fe493e17` | feat(tsr): add YAML loader and CS1/CS2 domain rule files |
| `8cb856a5` | feat(gold): add TieredGold schema dataclasses |
| `ad32eb5f` | feat(gold): add GoldEvaluator with tiered verdict logic |
| `4b59dcca` | feat(benchmark): add HeldOutQuery schema and DomainPlugin ABC |
| `9159f9f8` | fix(benchmark): remove unused field import |
| `bc2cdad8` | fix(foundation): safe eval sandbox, cache isolation, error handling, docs |

#### 최종 리뷰에서 발견 및 수정된 이슈

| 등급 | 이슈 | 수정 |
|------|-----|-----|
| Critical | `eval()` MRO 우회 RCE 가능 | AST 화이트리스트 기반 `_safe_eval()`로 교체 |
| Important | `lru_cache` 공유 뮤터블 객체 — 캐시 오염 위험 | `_load_domain_tsr_cached()` private 분리 + `deepcopy()` 반환 |
| Important | `_eval_criterion()` 비수치 output 시 `TypeError` 미처리 | `try/except (TypeError, ValueError): return False` 추가 |
| Important | alternative 매칭 비대칭성 미문서화 | `evaluate()` docstring에 의도적 비대칭 설명 추가 |
| Important | `__pycache__` git 추적 | `git rm --cached` + `.gitignore` 추가 |

---

## 3. 다음 단계 (Plan 2~6)

| Plan | 내용 | 상태 |
|------|-----|-----|
| Plan 1 | Foundation (TSR + Gold + Benchmark 인터페이스) | **완료** ✅ |
| Plan 2 | CS2: ComfyTranscriptomics | 미시작 |
| Plan 3 | CS3: ComfyChem | 미시작 |
| Plan 4 | CS4: ComfyProteomics | 미시작 |
| Plan 5 | CS5: ComfyEpigenomics | 미시작 |
| Plan 6 | Cross-domain Meta-analysis pipeline | 미시작 |

### Plan 2 착수 전 확인 필요 사항 (Open Questions)

1. **CS1 TSR 소급 적용**: bioinformatics.yaml의 `biopython_pairwise2` canonical ↔ `biopython_align_pairwisealigner` 교체 여부 (deprecated API 이슈).
2. **각 도메인 fixture 공개 가능성**: Proteomics raw mzML 파일 용량 및 라이선스 — accession 번호 + cached output 대체 여부.
3. **Expert reviewer pool**: 5개 도메인 커버하려면 도메인별 전문가 필요. 모집 전략 사전 정의.
4. **ComfyChem docking fixture**: AutoDock Vina용 receptor PDB 선정 기준.

---

## 4. 기술 메모

### TSREngine 안전성

`_safe_eval()` 는 `ast.parse()` 후 `_SafeEvalVisitor`로 허용 노드만 통과시킨다.
허용: `Expression, BoolOp, And, Or, Compare, Eq, NotEq, Lt, LtE, Gt, GtE, Name, Constant, Load`
차단: `Attribute, Call, Subscript` 등 모든 미허용 노드 → `ValueError` raise → `False` 반환.

### GoldEvaluator 판정 로직

```
INVALID tool 포함 → CRITICAL_ERROR (최우선)
canonical tools 정확히 일치 AND output criteria 통과 → CORRECT_CANONICAL
alternatives.tools 중 하나라도 포함 AND functional_equivalence 통과 → CORRECT_ALTERNATIVE
그 외 → INCORRECT
```

canonical은 exact set equality, alternative는 최소 1개 포함 (의도적 비대칭).

### 테스트 실행 방법

```bash
cd /tmp && PYTHONPATH= python -m pytest \
  /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/tests/llm_core/ \
  --ignore=.../test_check_provider_readiness_script.py \
  --ignore=.../test_run_workflow_experiment_script.py \
  -q
# Expected: 95 passed
```
