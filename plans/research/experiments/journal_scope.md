# 저널 연구 범위 및 목표 저널

- 문서 버전: 1.2
- 결정일: 2026-06-22
- 연구명: ComfyBIO Biopython 하이브리드 워크플로우 생성
- 상태: 저널 벤치마크용 연구 범위 고정; 변경 시 프로토콜 amendment 필요
- Amendments: `COMFYBIO-JOURNAL-001-A001`, `COMFYBIO-JOURNAL-001-A002`

## 목표 저널 결정

### 1차 목표: Briefings in Bioinformatics

- 저널: **Briefings in Bioinformatics (BIB)**
- 목표 manuscript 성격: **New Methods 중심의 original research / case study**
- 2024 Journal Impact Factor: **7.7**
- 2024 5-Year Impact Factor: **8.7**
- 2025 CiteScore: **13.6**

선정 근거:

1. BIB는 review뿐 아니라 new methods, case studies 및 analytical tool 활용 연구를 명시적으로 출판한다.
2. Scope에 sequence analysis, structural bioinformatics, systems biology와 AI/ML applications가 포함되어 본 연구 주제와 맞는다.
3. 12개 workflow family, 120개 held-out query, paired ablation, 실제 ComfyUI 실행 및 blinded expert review를 완결하면 단순 software 소개가 아닌 재현 가능한 방법론·case study로 제시할 수 있다.
4. 세 후보 중 공식 2024 IF가 가장 높다.

BIB 제출을 위한 추가 기준:

- 단순 ComfyUI/Biopython 통합이 아니라 일반화 가능한 template-guided workflow generation 방법을 입증한다.
- 실제 biological data fixture와 비자명한 다단계 workflow를 사용한다.
- 관련 LLM agent, workflow-generation 및 bioinformatics assistant와의 차별성을 명확히 한다.
- 실패 분석과 재현성 package를 통해 넓은 computational biology 독자층에 실용적 지침을 제공한다.

공식 출처: [Briefings in Bioinformatics 저널 소개 및 지표](https://academic.oup.com/bib/pages/About).

### 2차 목표: Bioinformatics

- 저널: **Bioinformatics**
- 논문 유형: **Original Paper**
- 우선 category: **Data and text mining**
- 보조 scope: Sequence analysis, Phylogenetics, Structural bioinformatics
- 2024 Journal Impact Factor: **5.4**
- 2024 5-Year Impact Factor: **7.1**
- 2025 CiteScore: **11.1**

Bioinformatics Original Paper는 최대 7쪽, 약 5,000단어이며 computational molecular biology의 새로운 model, algorithm 또는 new-method software를 대상으로 한다. 실제 biological data 사용과 state-of-the-art method 비교가 중요하다. 현재 설계와 직접적인 방법론 적합성은 BIB보다 높을 수 있으므로 BIB desk reject 또는 scope mismatch 시 2차 목표로 사용한다.

공식 출처:

- [Bioinformatics 저자 지침](https://academic.oup.com/bioinformatics/pages/General_Instructions)
- [Bioinformatics 저널 소개 및 지표](https://academic.oup.com/bioinformatics/pages/About)

### 3차 fallback: Bioinformatics Advances

- 논문 유형: **Original Article / Software**
- 2024 Journal Impact Factor: **2.8**

BIB와 Bioinformatics에서 요구하는 방법론적 신규성 또는 광범위한 영향력이 충분하지 않을 경우 사용한다. 이 fallback은 negative result를 숨기거나 endpoint를 변경하기 위한 용도가 아니다.

공식 출처: [Bioinformatics Advances 저자 지침](https://academic.oup.com/bioinformaticsadvances/pages/instructions-to-authors).

### 저널 선택 원칙

| 우선순위 | 저널 | 강점 | 주요 reject risk |
|---:|---|---|---|
| 1 | BIB | 가장 높은 IF, new methods·AI/ML·case study 범위 | 방법론 신규성·폭넓은 독자 가치 부족 |
| 2 | Bioinformatics | 현재 실험 설계와 직접적인 methods 적합성 | state-of-the-art 비교와 real biological data 부족 |
| 3 | Bioinformatics Advances | Software methods와 재현성 package 수용성 | 상대적으로 낮은 IF |

목표 저널 변경은 연구 결과의 방향과 무관하게 scope fit과 방법론 기여 수준으로만 결정한다. Held-out 결과 확인 후 저널을 변경하더라도 benchmark membership, endpoint, 제외 기준 또는 분석 방법은 변경하지 않는다.

## 연구 기여 문장

ComfyBIO Biopython은 자연어 생물정보학 목표를 ComfyUI에서 표현·실행 가능한 Biopython 워크플로우로 변환하는 template-guided hybrid 방법을 제공하며, deterministic normalization과 template-guided repair가 free-form LLM 생성보다 안정적인 과업 실행을 향상시키는지 평가한다.

이 문장이 목표 방법론적 기여다. ComfyUI, LLM 및 Biopython의 단순 결합만으로 신규성을 주장하지 않는다.

## Claim 단계

### 사전 지정 주 claim

> Template-guided hybrid 워크플로우 생성은 held-out 자연어 Biopython 워크플로우 과제에서 free-form LLM 생성보다 expected-output-verified ComfyUI 실행 성공률을 향상시킨다.

### 조건부 의미 정확성 claim

다음의 강한 claim은 blinded expert rating과 functional expected-output 평가가 모두 지지할 때만 허용한다.

> Template-guided hybrid 워크플로우 생성은 free-form 생성보다 생물학적 과업 정확성을 향상시킨다.

### 축소 claim

Primary effect가 불확실하거나 음수인 경우 결과를 그대로 보고하고, 다음과 같이 증거가 지지하는 수준으로 claim을 낮춘다.

> Hybrid 생성은 구조적 유효성 또는 template equivalence를 향상시키지만, 실행 및 의미 정확성은 변동성이 있다.

Null 또는 negative result는 보고할 연구 결과이며 benchmark case 제거 또는 분석 중단 사유가 아니다.

## 연구 질문

- RQ1: Hybrid 생성은 free 생성보다 robust expected-output-verified ComfyUI 실행 성공을 향상시키는가?
- RQ2: Normalization과 template-guided repair가 각각 어느 정도의 개선에 기여하는가?
- RQ3: 구조적 지표는 독립적으로 검토된 생물학적 과업 정확성과 일치하는가?
- RQ4: Workflow family와 난이도에 따라 성능 및 실패 유형이 어떻게 달라지는가?
- RQ5: 동일한 고정 모델과 설정을 반복 실행할 때 결과가 얼마나 안정적인가?

## 포함 Workflow Family

Primary study는 다음 12개 family를 포함한다.

1. `fasta_parse`
2. `pairwise_alignment`
3. `multiple_alignment`
4. `blast_search`
5. `searchio_analysis`
6. `phylogeny`
7. `annotation`
8. `pdb_structure_basic`
9. `motif_scan_basic`
10. `entrez_fetch`
11. `uniprot_lookup`
12. `kegg_pathway_basic`

Primary study의 family 목록은 고정한다. 추가 family 결과는 exploratory result로만 보고한다.

## 포함 비교

- Primary comparison: `hybrid` 대 `free`
- Secondary architecture comparison: `normalized` 대 `free`
- Secondary repair comparison: `hybrid` 대 `normalized`
- Deterministic provider: pipeline validation 전용이며 LLM effect estimate에서 제외
- 추가 LLM provider: held-out 실행 전 amendment로 승격하지 않는 한 secondary generalization analysis로만 보고

## 포함 근거

- Held-out 자연어 benchmark
- 독립 검토된 functional gold criteria와 허용 가능한 대안
- Expected output을 포함한 local/cached bioinformatics fixture
- Schema, graph, load, runtime 및 output 검증
- 실제 headless ComfyUI 실행
- LLM 반복 실행
- Blinded expert semantic review
- Failure taxonomy 및 representative case
- Immutable raw record 및 reproducibility metadata

## 제외 범위

Primary study에서 다음을 제외한다.

- Production-scale BLAST database benchmark
- Live external service availability를 모델 품질로 평가하는 것
- 재배포 가능한 fixture 또는 cached response를 제공할 수 없고 unrestricted network access가 필요한 workflow
- 식물 육종 및 multimodal extension
- 사전 지정된 12개 이외 family에 대한 성능 claim
- 문서화되고 합리적으로 동등한 환경에서 실행할 수 없는 외부 시스템과의 비교
- 별도 승인된 user study 없이 end-user productivity, usability 또는 clinical validity를 주장하는 것

Entrez, UniProt 및 KEGG 과제의 primary endpoint에는 cached response 또는 controlled fixture를 사용한다. Live API 실행은 수행하더라도 exploratory operational test로 분류한다.

## 모집단 및 일반화 범위

목표 모집단은 등록된 ComfyBIO node set으로 표현할 수 있고 재배포 가능한 local fixture 또는 controlled cached response로 실행 가능한 소규모·중간 규모 Biopython 과제에 대한 영어 자연어 요청이다.

본 연구는 임의의 생물정보학 소프트웨어, 대규모 production pipeline, 비영어 요청, clinical decision-making 또는 확인하지 않은 ComfyUI custom-node 생태계에 대한 성능을 입증하지 않는다.

## 전문가 평가 거버넌스

Expert review는 secondary evidence다. Reviewer 모집 전에 다음을 완료한다.

- 적용 가능한 기관의 윤리 심의 또는 면제 판단을 확인하고 기록한다.
- Reviewer 안내 및 동의 문구를 준비한다.
- 보상과 이해상충을 공개한다.
- Reviewer 자격, blinding, 배정 및 adjudication 규칙을 고정한다.
- 거버넌스 gate를 통과하기 전에는 rating을 수집하지 않는다.

이 문서는 윤리 승인이 불필요하다고 주장하지 않는다. 판단 권한은 관련 기관에 있다.

## 원고 Checklist 매핑

| 목표 저널 요건 | 계획된 근거 |
|---|---|
| BIB new methods / case study | 일반화 가능한 hybrid generation 방법, 12-family benchmark, 실제 biological fixture |
| 폭넓은 computational biology 가치 | Sequence·alignment·search·phylogeny·annotation·structure·database family 통합 평가 |
| Bioinformatics state-of-the-art comparison | Free/normalized/hybrid ablation 및 실행 가능한 외부 baseline 검토 |
| Real biological data | 출처·license·accession을 기록한 FASTA, GenBank, alignment, tree, search result, structure fixture |
| Methods rigor | Frozen protocol, paired design, sample-size rationale, e2e runner, statistical analysis |
| Software availability | Versioned ComfyBIO release, public source, license, 문서, tutorial/use case |
| Data availability | Archived benchmark, raw record, manifest, checksum, DOI |
| Reproducibility | Immutable raw run, model/config metadata, environment lock, analysis script |
| LLM research use | 연구 방법으로서 model 역할, prompt, 설정 및 제한 공개 |
| Limitations | Provider drift, held-out 작성 방식, fixture 범위, family 경계 |
| Human evaluation | 기관 판단, 동의, blinding, agreement |

## Scope 완료 기준

Task 1 scope는 다음을 만족하면 완료한다.

- 연구 기여와 claim 단계를 고정했다.
- 12개 primary family와 제외 범위를 고정했다.
- 공식 지침을 근거로 목표 저널과 논문 유형을 기록했다.
- 전문가 평가 거버넌스를 reviewer 모집 전 필수 gate로 명시했다.
- Freeze 이후 모든 변경은 amendment로 관리한다.
