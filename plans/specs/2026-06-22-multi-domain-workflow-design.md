# Multi-Domain NL Workflow Generation — Design Spec

- 작성일: 2026-06-22
- 상태: draft — 사용자 검토 대기
- 연관 프로토콜: `COMFYBIO-BIB-001` (task_01_scope_protocol/)
- 목표 저널: Briefings in Bioinformatics

---

## 1. 논문 재프레이밍

### 기존 framing
ComfyBIO라는 신규 소프트웨어를 bioinformatics workflow generation case study로 제시하는 단일 도메인 benchmark.

### 새 framing
ComfyUI를 visual workflow management system(WMS)으로 사용해 자연어 기반 분석 워크플로우를 생성하는 프레임워크를, 생명과학 5개 도메인에 걸쳐 multi-domain benchmark로 검증한다.

### 잠정 제목

> Natural Language-Driven Analysis Workflow Generation Using ComfyUI as a Visual Workflow Management System: A Multi-Domain Benchmark Across Life Sciences

### 논문 구조

| 섹션 | 내용 |
|-----|-----|
| 1. Introduction | ComfyUI as WMS, NL interface for non-expert scientists |
| 2. Review | NL-to-workflow approaches in life sciences |
| 3. Framework | Tool Selection Registry + multi-path gold criteria 아키텍처 |
| 4. Case Studies | CS1~CS5 독립 섹션 |
| 5. Cross-domain Meta-analysis | failure taxonomy, tool selection accuracy |
| 6. Discussion | method-selection guidance, limitation, generalization 경계 |

### 논문 기여

1. **5개 도메인 multi-domain benchmark** (600 queries, 60 workflow families)
2. **Tool Selection Registry** — 도메인 best-practice를 pre-registered rule로 코드화
3. **Multi-path gold criteria** — functional equivalence 기반 평가 프레임워크
4. **Cross-domain failure taxonomy** — 도메인 무관 패턴과 도메인 특이 패턴 분리
5. **ComfyBIO case study** — CS1, template-guided hybrid approach의 구체적 검증

---

## 2. Domain-as-Project 구조

각 도메인은 독립적인 소규모 프로젝트로 설계한다. 단일 linear pipeline이 아니라 step별 tool alternative를 포함한 tool landscape tree를 정의한다.

### Domain Project 구성요소

| 구성요소 | 설명 |
|---------|-----|
| `tool_landscape` | step별 canonical / alternative-valid / INVALID tool 목록 |
| `workflow_families` | analytical goal 기준 12개 패밀리 |
| `query_population` | 120 queries (tool 지정 / goal 지정 / 미지정 / adversarial) |
| `fixture_set` | 실제 biological data fixture |
| `gold_registry` | Tiered gold criteria (canonical / alternative / invalid) |

### Query 난이도 × Tool Specificity

| Difficulty | Tool Specificity | 비율 | NL 예시 |
|-----------|-----------------|-----|---------|
| Easy | tool 명시 | 30% (36) | "fastp으로 adapter 제거 후 STAR로 hg38에 정렬해줘" |
| Medium | goal 명시, tool 암묵 | 40% (48) | "paired-end reads를 DE 분석 전에 준비해줘" |
| Hard | 컨텍스트만 존재 | 20% (24) | "10x scRNA-seq 데이터 클러스터링 후 세포형 주석까지" |
| Adversarial | 잘못된 tool 힌트 | 10% (12) | "nanopore long-read를 STAR로 정렬해줘" |

Adversarial 기대 동작: registry INVALID tool을 요청받았을 때 모델이 올바른 tool로 교정하거나 경고를 포함한 workflow를 생성하면 correct.

---

## 3. Tool Selection Registry (TSR)

### 설계 원칙

- Tool 선택은 랜덤이 아니라 **데이터 컨텍스트 기반 deterministic rule**로 결정한다.
- 규칙 출처: nf-core 파이프라인, 공인된 tool benchmark 논문, 각 도구 공식 문서의 recommended use case.
- 모든 규칙은 held-out 실행 전 pre-register하고 hash로 freeze한다.
- Registry 자체가 독자에게 실무 가치를 제공하는 2차 기여물이다.

### TSR 규칙 구조 (예시: Transcriptomics)

```yaml
domain: transcriptomics
step: alignment
rules:
  - condition: "data_type == short_read AND read_length >= 75bp AND assay == rna_seq"
    canonical: STAR
    alternative_valid: [HISAT2]
    invalid: [minimap2, bwa]
    reason: "STAR is splice-aware; minimap2/bwa lack splice-junction detection"

  - condition: "data_type == long_read AND platform == nanopore"
    canonical: minimap2
    alternative_valid: []
    invalid: [STAR, HISAT2, HISAT2]
    reason: "Short-read aligners cannot handle long-read error profiles"

  - condition: "quantification_only == true"
    canonical: salmon
    alternative_valid: [kallisto]
    invalid: [STAR, HISAT2]
    reason: "Pseudo-alignment is sufficient and faster when genome alignment not needed"

step: differential_expression
rules:
  - condition: "n_samples_per_group < 6"
    canonical: edgeR
    alternative_valid: [DESeq2]
    invalid: []
    reason: "edgeR performs better with small sample sizes"

  - condition: "n_samples_per_group >= 6"
    canonical: DESeq2
    alternative_valid: [edgeR, limma-voom]
    invalid: []
    reason: "DESeq2 negative binomial model well-validated for typical bulk RNA-seq"
```

---

## 4. Multi-path Gold Criteria

### Tiered Gold Registry (query당 구조)

```yaml
query_id: TR_006
family: differential_expression
context:
  data_type: bulk_rna_seq
  n_samples_per_group: 4
  organism: homo_sapiens
  fixture: GSE_example_counts.tsv

gold:
  tier_1_canonical:
    tools: [edgeR]
    expected_output:
      top10_deg_ids: [GENE_A, GENE_B, ...]   # fixture 기반 pre-computed
      direction_concordance_min: 0.90

  tier_2_alternative:
    tools: [DESeq2, limma-voom]
    evaluation: functional_equivalence
    criteria:
      top10_overlap_with_canonical: ">= 0.80"

  tier_3_invalid:
    tools: [kallisto, STAR, fastp]
    result: CRITICAL_ERROR

  adversarial_override:
    bad_hint_tool: DESeq2
    correct_behavior: [use_edgeR, warn_sample_size]
```

### Gold 생성 프로세스

1. fixture 확정 (실제 biological data)
2. TSR로 canonical path 결정
3. canonical path 실행 → tier_1 expected output 생성
4. alternative path 모두 실행 → tier_2 functional equivalence 범위 산정
5. independent reviewer가 criteria 승인
6. hash와 함께 pre-register (held-out 실행 전 freeze)

### 평가 판정 규칙

| 생성 workflow | 판정 |
|-------------|-----|
| canonical tool path 사용, expected output 일치 | correct (tier_1) |
| alternative-valid tool 사용, functional equivalence 충족 | correct (tier_2) |
| alternative-valid tool 사용, functional equivalence 미충족 | incorrect |
| INVALID tool 사용 | CRITICAL_ERROR |
| adversarial hint → canonical로 교정 또는 경고 포함 | correct |
| adversarial hint → INVALID tool 그대로 사용 | CRITICAL_ERROR |

---

## 5. Case Study 도메인 정의

### CS1: ComfyBIO (서열 생물정보학)

기존 protocol `COMFYBIO-BIB-001`의 12개 workflow family를 유지한다. 본 설계의 primary quantitative benchmark.

Workflow families: fasta_parse, pairwise_alignment, multiple_alignment, blast_search, searchio_analysis, phylogeny, annotation, pdb_structure_basic, motif_scan_basic, entrez_fetch, uniprot_lookup, kegg_pathway_basic

---

### CS2: ComfyTranscriptomics (전사체학)

bulk RNA-seq와 scRNA-seq를 포괄하는 도메인.

| # | Family | Canonical | Alternative-valid | INVALID |
|---|--------|-----------|------------------|---------|
| 1 | raw_qc | FastQC+MultiQC | — | — |
| 2 | adapter_trimming | fastp | Trimmomatic, Cutadapt | — |
| 3 | genome_alignment | STAR (short-read) | HISAT2 | STAR (long-read nanopore) |
| 4 | pseudo_alignment | kallisto | salmon | — |
| 5 | read_quantification | featureCounts | HTSeq, RSEM | — |
| 6 | differential_expression | DESeq2 (n≥6) / edgeR (n<6) | limma-voom | — |
| 7 | pathway_enrichment | clusterProfiler | fgsea, GSEA | — |
| 8 | sc_preprocessing | Scanpy | Seurat | — |
| 9 | sc_clustering | Leiden | Louvain | k-means (연속형 데이터) |
| 10 | sc_annotation | SingleR | CellTypist, manual | — |
| 11 | sc_trajectory | PAGA/Scanpy | Monocle3 | — |
| 12 | visualization | ggplot2 | pheatmap, ComplexHeatmap | — |

핵심 NL 챌린지: bulk vs sc 분기 추론, sample size에 따른 DE tool 선택.

---

### CS3: ComfyChem (화학정보학 / 신약발굴)

데이터 타입이 SMILES/SDF로 서열 기반 도메인과 완전히 다름.

| # | Family | Canonical | Alternative-valid | INVALID |
|---|--------|-----------|------------------|---------|
| 1 | molecule_parsing | RDKit | OpenBabel | — |
| 2 | property_calculation | RDKit descriptors | mordred | — |
| 3 | fingerprinting | Morgan/ECFP4 | MACCS | — |
| 4 | similarity_search | RDKit BulkTanimoto | FPSim2 | — |
| 5 | substructure_search | RDKit SMARTS | OpenBabel SMARTS | — |
| 6 | scaffold_analysis | Bemis-Murcko | BRICS | — |
| 7 | admet_prediction | SwissADME | pkCSM, ADMETlab | — |
| 8 | conformation_gen | RDKit ETKDG | OpenBabel | — |
| 9 | docking | AutoDock Vina | Gnina | DOCK (클로즈드소스) |
| 10 | library_filtering | Lipinski RO5 | PAINS filter, QED | — |
| 11 | pharmacophore | RDKit ChemFeatures | Pharmer | — |
| 12 | reaction_enumeration | RDKit AllChem | — | — |

핵심 NL 챌린지: 화학 전문 어휘(SMILES, scaffold, Lipinski) 파싱.

---

### CS4: ComfyProteomics (질량분석 단백체학)

정량 방식(LFQ/TMT/SILAC)이 실험 설계에 따라 달라지는 구조.

| # | Family | Canonical | Alternative-valid | INVALID |
|---|--------|-----------|------------------|---------|
| 1 | raw_conversion | msconvert | ThermoRawFileParser | — |
| 2 | database_search_standard | MaxQuant | MASCOT | — |
| 3 | database_search_open | MSFragger | Comet | — |
| 4 | peptide_scoring | Percolator | PeptideProphet | — |
| 5 | fdr_control | MaxQuant FDR | pyteomics | — |
| 6 | lfq_quantification | MaxQuant LFQ | FlashLFQ | TMT pipeline (타입 불일치) |
| 7 | tmt_quantification | MaxQuant TMT | TMT-Integrator | LFQ pipeline (타입 불일치) |
| 8 | protein_inference | MaxQuant | ProteinProphet | — |
| 9 | statistical_analysis | MSstats | Perseus, limma | — |
| 10 | imputation | MinProb | kNN, QRILC | — |
| 11 | pathway_enrichment | clusterProfiler | STRING enrichment | — |
| 12 | ptm_analysis | MaxQuant PTM | PhosphoSitePlus lookup | — |

핵심 NL 챌린지: 실험 설계 타입(LFQ vs TMT) 추론 → 전혀 다른 pipeline 선택.

---

### CS5: ComfyEpigenomics (후성유전체학)

ChIP-seq / ATAC-seq / Bisulfite-seq를 포괄. 실험 기법에 따라 tool이 완전히 달라짐.

| # | Family | Canonical | Alternative-valid | INVALID |
|---|--------|-----------|------------------|---------|
| 1 | chip_alignment | Bowtie2 | BWA | minimap2 (short-read ChIP 부적합) |
| 2 | peak_calling_narrow | MACS3 | HOMER | SEACR (broad peak 전용) |
| 3 | peak_calling_broad | MACS3 --broad | HOMER --broad | — |
| 4 | atac_peak_calling | MACS3 | SEACR | — |
| 5 | peak_annotation | ChIPseeker | HOMER annotatePeaks | — |
| 6 | motif_analysis | HOMER | MEME-ChIP, STREME | — |
| 7 | differential_binding | DiffBind | DESeq2 on counts | — |
| 8 | atac_footprinting | TOBIAS | HINT-ATAC | — |
| 9 | bisulfite_alignment | Bismark | bwa-meth | STAR (methylation 인식 불가) |
| 10 | methylation_calling | Bismark extractor | MethylDackel | — |
| 11 | differential_methylation | methylKit | DSS | — |
| 12 | sc_atac_processing | ArchR | Signac | — |

핵심 NL 챌린지: 실험 기법 분류(ChIP vs ATAC vs bisulfite) 오분류 시 전혀 다른 pipeline 생성.

---

## 6. Cross-domain Meta-analysis 설계

5개 도메인 독립 benchmark 완료 후 다음 4개 분석을 수행한다.

| 분석 | 연구 질문 | 방법 |
|-----|---------|-----|
| Tool Selection Accuracy | 도메인별 canonical tool 선택률 | per-domain canonical hit rate 비교 |
| Adversarial Robustness | 잘못된 tool 힌트 제공 시 correction rate | adversarial 12 × 5 domains (60 queries) |
| Failure Taxonomy | 실패 원인이 도메인 무관인가, 도메인 특이인가 | cross-domain failure pattern clustering |
| NL Difficulty Calibration | tool specificity 감소에 따른 성공률 저하 기울기 | easy→hard slope 도메인별 비교 |

Meta-analysis가 논문의 primary claim을 domain-agnostic generalization으로 격상시킨다.

---

## 7. Benchmark 규모 요약

| 항목 | 값 |
|-----|---|
| 도메인 수 | 5 |
| 도메인당 workflow families | 12 |
| 총 workflow families | 60 |
| 도메인당 held-out queries | 120 |
| 총 held-out queries | 600 |
| 반복 횟수 (기존 protocol) | 5회/query |
| 총 invocations | 3,000 |
| Adversarial queries (meta-analysis) | 60 (12 × 5) |

---

## 8. 기존 Protocol과의 관계

기존 `COMFYBIO-BIB-001` protocol은 CS1(ComfyBIO)의 benchmark 설계 기준으로 유지한다. 본 설계는 그 위에 4개 도메인과 TSR/multi-path gold 레이어를 추가하는 **확장**이다.

기존 protocol의 다음 항목은 5개 도메인 모두에 적용된다:
- Invocation-level expected-output-verified execution success (§10)
- Query-level robust success (5회 중 4회 이상, §10)
- Raw data 저장 규칙 (§17)
- Held-out 실행 전 freeze 원칙 (§20)

본 설계가 기존 protocol을 변경하는 항목:
- Primary claim: CS1 단독 → 5개 도메인 cross-domain generalization
- Gold criteria: single gold → Tiered Gold Registry
- Query taxonomy: 기존 4단계 → tool specificity 축 추가

변경 사항은 `task_01_scope_protocol/amendments/` 에 dated amendment로 기록한다.

---

## 9. Open Questions (설계 확정 전 결정 필요)

1. **CS1 기존 12개 family에 TSR 소급 적용 여부** — Biopython 중심이라 alternative tool이 제한적. CS1은 단일 gold 유지하고 TSR은 CS2-CS5에만 적용할지 결정 필요.
2. **도메인별 fixture 공개 가능성** — proteomics raw 파일(mzML)은 용량이 크고 라이선스 제약이 있을 수 있음. Accession 번호 제공 + cached output으로 대체 여부 확인 필요.
3. **Expert reviewer pool** — 5개 도메인을 커버하려면 도메인별 전문가가 필요. 단일 reviewer가 모든 도메인을 평가할 수 없으므로 도메인별 reviewer 모집 전략 필요.
4. **ComfyChem docking fixture** — AutoDock Vina 실행에 receptor PDB 파일이 필요. PDB에서 가져오는 fixture 선정 기준 사전 정의 필요.
