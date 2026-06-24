# GitHub 유사 프로젝트 조사 및 개선안 분석

**작성일:** 2026-06-24  
**목적:** LLM 기반 생물정보학 워크플로우 탐색·평가 분야의 유사 오픈소스 프로젝트를 조사하고, ComfyBIO의 현재 상태와 비교하여 강화 방향을 도출한다.

---

## 1. 현재 프로젝트(ComfyBIO) 핵심 구조

### 평가 파이프라인
```
자연어 쿼리 (HeldOutQuery)
  → build_tool_selection_prompt (TSR + 쿼리 결합)
  → LLM 어댑터 (Claude / Codex / Gemini / Deterministic)
  → parse_tool_response (도구 목록 추출)
  → GoldEvaluator (Tiered Gold 비교)
  → EvalResult → BenchmarkReport
```

### 핵심 설계 특징
| 구성요소 | 설명 |
|----------|------|
| TSR (Tool Selection Reference) | 도구 유효성 YAML — canonical / alternative_valid / invalid + 조건 분기 |
| Gold 3-tier | CORRECT_CANONICAL / CORRECT_ALTERNATIVE / CRITICAL_ERROR / INCORRECT |
| DomainPlugin | CS1~CS6 플러그인 (전사체학·변이분석·후성유전학·메타게놈·게놈조립) |
| LLM 어댑터 | Claude CLI, Codex CLI, Gemini CLI, Deterministic(rule-based) |
| ComfyUI 통합 | 비주얼 노드 기반 — 타 프로젝트에 없는 독창적 UI 레이어 |
| `simulated_execution` | 실제 실행 없이 시뮬레이션 결과 반환 (현재 미완성 영역) |

---

## 2. 유사 GitHub 저장소 조사 결과

### 2-1. 벤치마크 / 평가 중심

#### [Future-House/BixBench](https://github.com/Future-House/BixBench)
- **유사도:** ★★★★★
- **특징:** 실제 생물정보학 연구 Jupyter notebook 54개, 약 300개 질문
- **평가 방식:** LLM 에이전트가 Jupyter notebook을 직접 작성·실행 → open-answer 정확도 측정
- **성능:** GPT-4o / Claude 3.5 Sonnet 모두 17% 정확도 (무작위 대비 미미)
- **ComfyBIO와 차이:**
  - BixBench: 코드 실행 능력 평가 (end-to-end)
  - ComfyBIO: 도구 선택 판단력 평가 (tool selection accuracy) → 더 세밀한 중간 단계 측정

#### [cinnnna/bioinfo-bench](https://github.com/cinnnna/bioinfo-bench)
- **유사도:** ★★★★
- **특징:** 지식 습득 / 지식 분석 / 지식 응용 3가지 관점으로 LLM 생물정보학 지식 평가
- **ComfyBIO와 차이:** 순수 Q&A 방식 vs ComfyBIO의 워크플로우 도구 선택 구조

#### [Future-House/LAB-Bench](https://github.com/Future-House/LAB-Bench)
- **유사도:** ★★★
- **특징:** 생물학 연구 AI 시스템 평가용 데이터셋

---

### 2-2. 워크플로우 자동화 에이전트

#### [EnteloBio/flowagent](https://github.com/EnteloBio/flowagent)
- **유사도:** ★★★★
- **특징:** 자연어 → Nextflow/Snakemake 파이프라인 자동 생성, HPC 실행 지원
- **지원 분석:** RNA-seq, ChIP-seq, ATAC-seq, Hi-C, 단세포
- **ComfyBIO와 차이:** 실제 실행 중심 vs ComfyBIO의 평가/벤치마크 중심

#### [interactivereport/CompBioAgent](https://github.com/interactivereport/CompBioAgent)
- **유사도:** ★★★
- **특징:** 단세포 RNA-seq 특화, LLM 에이전트의 reasoning chain 저장

#### [ArcInstitute/SRAgent](https://github.com/ArcInstitute/SRAgent)
- **유사도:** ★★★
- **특징:** SRA / NCBI 데이터베이스 실시간 접근용 LLM 에이전트

#### [bio-xyz/BioAgents](https://github.com/bio-xyz/BioAgents)
- **유사도:** ★★★
- **특징:** 문헌 분석 + 데이터 과학 멀티에이전트, 사용자 피드백 기반 반복 과학적 발견

---

### 2-3. 에이전트 스킬 / MCP 인프라

#### [GoekeLab/awesome-genomic-skills](https://github.com/GoekeLab/awesome-genomic-skills)
- **특징:** Claude Code / Copilot / Codex / Cursor용 게놈·생물정보학 에이전트 스킬 큐레이션
- **포함 MCP:** ChatSpatial (공간 전사체학), biomcp (임상시험·유전자), gget-mcp (Pachter Lab 13종 도구)

#### [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
- **특징:** 16만+ 과학자 사용, 140개 ready-to-use 스킬, 100+ 과학 DB 커버

---

## 3. ComfyBIO의 독창적 강점

1. **ComfyUI 비주얼 노드** — 다른 프로젝트에 없는 드래그·드롭 워크플로우 UI
2. **조건 분기 TSR** — 시퀀서 종류(illumina/nanopore), 분석 유형(germline/somatic)에 따른 도구 유효성 분기
3. **Adversarial override** — 의도적으로 잘못된 힌트를 주고 LLM이 올바른 선택을 하는지 테스트하는 구조
4. **Gold 3-tier 평가** — canonical 정답 / 기능적 동등 대안 / 절대 불가 도구를 구분한 세밀한 평가

---

## 4. 부족한 영역 분석

### 4-1. 쿼리 커버리지 부족 (가장 시급)
- **현황:** 전사체학 12개 패밀리 × 1개 쿼리, 총 ~72개 gold 파일
- **BixBench 수준:** 205개 질문
- **영향:** 통계적으로 유의미한 모델 비교 불가능, 특정 표현 방식에 대한 취약점 미탐지

### 4-2. 추론 과정 미캡처
- **현황:** `generated_tools: [STAR]` 결과만 저장
- **영향:** 오답 시 LLM이 왜 틀렸는지 분석 불가 → 프롬프트 개선 불가능

### 4-3. 멀티스텝 파이프라인 평가 없음
- **현황:** 단일 단계(step)별 독립 평가
- **BixBench 대비:** 전체 분석 파이프라인의 일관성 및 단계간 호환성 미검사

### 4-4. 실제 워크플로우 실행 없음
- **현황:** `run_simulated_workflow` — 항상 가짜 결과 반환
- **영향:** 도구 선택이 맞아도 실제 실행 가능한지 검증 불가

### 4-5. 결과 비교 인프라 없음
- **현황:** `BenchmarkReport.accuracy`는 계산되지만 멀티 모델 비교 시각화 없음
- **영향:** Claude vs Codex vs Gemini 비교 분석 수작업 필요

### 4-6. 외부 DB 연결 없음
- **현황:** TSR이 수동 작성 정적 YAML
- **SRAgent/gget-mcp 대비:** 실시간 도구 정보 업데이트 불가

---

## 5. 개선 로드맵 (우선순위)

```
즉시 착수 (이번 스프린트)
  ① 쿼리 다양성 확대 — 각 패밀리에 _002(medium) / _003(hard/adversarial) 추가
  ② 추론 trace 캡처 — EvalResult에 reasoning_trace, confidence_score, tool_rationale 추가

단기 (1-2개월)
  ③ 멀티스텝 파이프라인 gold 스키마 설계 + 평가 로직
  ④ 결과 비교 CLI 리포트 (`python -m llm_core.report --compare`)

중기 (분기 목표)
  ⑤ 실제 실행 통합 — Docker 기반 소형 데이터셋 실행
  ⑥ 외부 DB 동기화 — bio.tools API 연동

장기 (공개 벤치마크)
  ⑦ 공개 리더보드 — BixBench 수준의 공개 평가 데이터셋으로 발전
```

---

## 6. 참고 자료

- [BixBench 논문 (arXiv:2503.00096)](https://arxiv.org/abs/2503.00096)
- [Future-House/BixBench](https://github.com/Future-House/BixBench)
- [EnteloBio/flowagent](https://github.com/EnteloBio/flowagent)
- [GoekeLab/awesome-genomic-skills](https://github.com/GoekeLab/awesome-genomic-skills)
- [cinnnna/bioinfo-bench](https://github.com/cinnnna/bioinfo-bench)
- [interactivereport/CompBioAgent](https://github.com/interactivereport/CompBioAgent)
- [ArcInstitute/SRAgent](https://github.com/ArcInstitute/SRAgent)
- [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
