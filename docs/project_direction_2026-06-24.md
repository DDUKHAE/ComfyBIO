# ComfyBIO 프로젝트 방향 정립

**작성일:** 2026-06-24

---

## 핵심 프레이밍

**"LLM 기반 생물정보학 워크플로우 생성"이 아닌**  
**"자연어 기반 생물정보학 워크플로우 생성"**

### 왜 이 구분이 중요한가

"LLM 기반"이라고 하면 LLM이 생물정보학 지식을 갖고 있어야 한다는 오해를 만든다.
실제 ComfyBIO의 구조에서 도메인 지식은 TSR(Tool Selection Reference)에 있고,
LLM은 **사용자의 자연어를 해석하는 인터페이스 레이어**다.

```
사용자 (비전문가)
  "내 Nanopore long-read 데이터로 변이 분석 하고 싶어"
          ↓
    LLM (자연어 이해 레이어)
    → sequencer: nanopore
    → analysis_type: variant_calling
          ↓
    TSR (전문가 지식 레이어)
    condition: sequencer == nanopore → minimap2 (canonical)
                                     → BWA-MEM2 (invalid)
          ↓
    ComfyUI 워크플로우 (비주얼 노드 그래프)
```

---

## LLM의 두 가지 기능

### Function 1 — Context 추출 (이번 세션)

사용자의 자연어(`nl_text`)에서 TSR 조건 매핑에 필요한 구조화된 context를 추출한다.

```
입력: "I have Oxford Nanopore long reads from a bacterial genome for variant analysis"
출력: {sequencer: nanopore, analysis_type: wgs, organism: bacteria}
```

이 context가 TSR 엔진에 전달되어 올바른 도구 집합을 결정한다.
**Context 추출 정확도 = 시스템 성능의 핵심 지표**

### Function 2 — 워크플로우/도구 탐색·검증·추가 (다른 세션 진행 중)

TSR에 아직 작성되지 않은 워크플로우나 도구에 대해:
- 새 분석 요청을 받았을 때 적합한 도구 탐색
- 탐색 결과를 TSR 포맷으로 검증·추가

---

## 현재 구조의 문제점 (Function 1 관점에서)

`HeldOutQuery`의 `context` 필드가 gold 파일에 **미리 수동 작성**되어 있다.

```yaml
# 현재: NLU를 우회
nl_text: "I have Oxford Nanopore long reads..."
context:
  sequencer: nanopore   ← LLM이 추출해야 할 값이 이미 적혀 있음
```

`runner.py`가 이 context를 그대로 `build_tool_selection_prompt`에 넘기므로
LLM은 자연어를 실제로 해석할 필요가 없다.

**수정 방향:**
- `context`를 LLM이 `nl_text`에서 추출
- gold의 `context` 필드는 **추출 정답(ground truth)**으로 활용
- 평가 지표: context 추출 정확도 + 최종 워크플로우 일치율

---

## 평가 구조 재설계

### 기존 (단일 평가)
```
nl_text + context(미리 작성) → TSR → 도구 선택 → gold 비교
```

### 신규 (2단계 평가)
```
Stage 1: nl_text → LLM → extracted_context
         extracted_context vs gold.context → Context Extraction Score

Stage 2: extracted_context → TSR → 도구 선택
         generated_tools vs gold.tools → Workflow Match Score
```

Stage 1 실패(context 오추출) → Stage 2도 자동 실패
→ 어느 단계에서 오류가 발생했는지 명확히 식별 가능

---

## 타 프로젝트와의 차별점

| 항목 | BixBench | FlowAgent | ComfyBIO |
|------|----------|-----------|---------|
| LLM 역할 | 생물정보학 지식 보유 | 파이프라인 생성기 | **자연어 → context 변환기** |
| 도메인 지식 위치 | LLM 자체 | LLM 자체 | **TSR (전문가 큐레이션)** |
| 출력물 | Jupyter notebook | Nextflow/Snakemake | **ComfyUI 비주얼 노드** |
| 비전문가 접근성 | 낮음 | 낮음 | **높음 (드래그&드롭)** |
| 지식 갱신 | 모델 재훈련 필요 | 모델 재훈련 필요 | **TSR 파일 수정으로 즉시 반영** |
