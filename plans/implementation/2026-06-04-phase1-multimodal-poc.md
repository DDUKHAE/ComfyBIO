# Phase 1 — 멀티모달 PoC 수직 슬라이스 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 표현형 이미지를 CLI 래퍼를 통해 멀티모달 LLM에 전달하여, 이미지 내용을 반영한 Biopython/육종 워크플로우 spec을 생성할 수 있음을 검증한다.

**Architecture:** 기존 3계층(노드/레지스트리·프롬프트/LLM 엔진)을 무수정 재활용하는 A 아키텍처. 멀티모달은 (1) gemini CLI 어댑터에 `image_paths` 인자 추가(`@경로` 인라인 참조 주입), (2) `image_paths`를 API → `llm_runner` → 어댑터로 관통시키는 배선, (3) 이미지 존재 시 프롬프트 보강, (4) 앵커 시나리오를 지탱할 최소 표현형 이미지 노드 1개로 구성한다. 가장 불확실한 가설(CLI가 이미지를 모델까지 통과시키는가)을 **Task 1 실측 프로브**로 먼저 해소한다.

**Tech Stack:** Python 3, asyncio subprocess, Gemini CLI (`gemini -p`, `@path` 멀티모달 참조), ComfyUI `comfy_api.latest.io` 노드, Pillow(PIL), pytest, aiohttp.

**참조 spec:** `docs/superpowers/specs/2026-06-04-breeding-multimodal-expansion-design.md`

**성공 기준 (spec §3 Phase 1):**
1. 이미지 첨부가 선택된 CLI를 통과해 모델에 도달한다 (Task 1로 검증).
2. LLM이 이미지 내용을 반영한 노드 선택을 한다 (Task 8로 검증).
3. 생성된 spec이 `parse_and_validate_llm_output(expected_type="biopython_workflow_spec")`를 통과한다 (Task 8로 검증).

---

## File Structure

| 파일 | 변경 | 책임 |
|------|------|------|
| `docs/superpowers/experiments/2026-06-04-cli-image-probe.md` | Create | Task 1 실측 프로브 절차·결과 기록 |
| `llm_interface/harness_core/llm_adapters/gemini_cli.py` | Modify | `build_multimodal_prompt` 헬퍼 + `generate`에 `image_paths` 인자 |
| `llm_interface/harness_core/llm_runner.py` | Modify | `generate_biopython_workflow`에 `image_paths` 관통 |
| `llm_interface/harness_core/biopython_prompts.py` | Modify | 이미지 존재 시(`has_images`) 프롬프트 보강 |
| `llm_interface/harness_nodes/__init__.py` | Modify | `/comfybio/generate`에서 `image_paths` 수신·전달 |
| `py/Phenotype_Image_Objects.py` | Create | 앵커용 최소 표현형 이미지 노드 1개 |
| `llm_interface/harness_core/node_registry.json` | Regenerate | 신규 노드 반영 |
| `tests/harness_core/test_gemini_multimodal.py` | Create | 헬퍼 단위 테스트 |
| `tests/harness_core/test_llm_runner_image_paths.py` | Create | 러너 관통 테스트 |
| `tests/harness_core/test_phenotype_prompts.py` | Create | 프롬프트 보강 테스트 |
| `tests/py/test_phenotype_image_node.py` | Create | 노드 스키마·실행 테스트 |
| `tests/harness_nodes/test_generate_api.py` | Modify | image_paths 배선 반영(기존 단언 갱신) |

**테스트 실행 기준 명령:** 저장소 루트(`custom_nodes/ComfyBIO_biopython`)에서
```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests -v
```

---

## Task 1: CLI 이미지 통과 실측 프로브 (가장 먼저 — 리스크 선해소)

> 이 Task는 자동 단위 테스트가 아니라 외부 CLI·인증·네트워크가 필요한 **수동 실측**이다. 결과(어떤 provider가 이미지를 통과시키는가, `@경로` 형식이 맞는가)를 문서에 기록하고, 이후 Task의 주입 형식을 확정한다.

**Files:**
- Create: `docs/superpowers/experiments/2026-06-04-cli-image-probe.md`

- [ ] **Step 1: 프로브 문서 생성**

`docs/superpowers/experiments/2026-06-04-cli-image-probe.md` 에 아래 내용을 작성한다.

````markdown
# CLI 이미지 통과 실측 프로브 (2026-06-04)

## 목적
gemini CLI(`-p` 헤드리스)가 프롬프트 내 `@경로` 참조로 이미지를 모델까지 전달하는지 확인한다.

## 절차
1. 테스트 이미지 생성 (빨간 사각형, 명확히 식별 가능한 색):
   ```bash
   cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
   python -c "from PIL import Image; Image.new('RGB',(64,64),(220,20,20)).save('/tmp/probe_red.png')"
   ```
2. 이미지 통과 호출:
   ```bash
   gemini -p "What is the dominant color in this image? Answer with one word. @/tmp/probe_red.png" --model gemini-2.5-pro --print
   ```
3. 대조군(이미지 없이 동일 질문):
   ```bash
   gemini -p "What is the dominant color in this image? Answer with one word." --model gemini-2.5-pro --print
   ```

## 판정 기준
- **통과**: 이미지 호출 응답에 "red"가 포함되고, 대조군은 색을 특정하지 못한다 → `@경로` 멀티모달 통과 확인.
- **실패**: 두 응답이 동일하거나 이미지 호출이 에러 → 다른 형식(`--image` 등) 또는 다른 provider(claude/codex) 재시도.

## 결과 (실행 후 기록)
- 사용 binary / 버전:
- 이미지 호출 응답:
- 대조군 응답:
- 판정:
- 확정된 주입 형식:  ___ (예: 프롬프트 끝에 `@<절대경로>` 줄 추가)
````

- [ ] **Step 2: 프로브 실행 및 결과 기록**

위 문서의 절차를 실제로 실행하고 "결과" 절을 채운다. (인증이 안 되어 있으면 먼저 `gemini auth login`.)
Expected: 이미지 호출 응답에 "red"가 포함되면 통과. 통과 형식(`@<절대경로>`)을 "확정된 주입 형식"에 기록.

> ⚠️ 만약 gemini가 통과하지 못하면, 같은 절차로 `claude`/`codex`를 시도하고 통과하는 provider와 형식을 기록한다. 이후 Task 2는 "확정된 주입 형식"을 따른다. 본 계획의 기본 가정은 **gemini `-p`에 `@<절대경로>` 인라인 참조**이다.

- [ ] **Step 3: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f docs/superpowers/experiments/2026-06-04-cli-image-probe.md
git commit -m "docs(experiment): CLI image pass-through probe results"
```

---

## Task 2: gemini 어댑터 — 멀티모달 프롬프트 헬퍼

`build_multimodal_prompt`는 외부 프로세스 없이 순수하게 테스트 가능한 헬퍼다. 이미지 경로 목록을 받아 프롬프트 끝에 `@<절대경로>` 참조를 덧붙인다(Task 1에서 확정한 형식).

**Files:**
- Modify: `llm_interface/harness_core/llm_adapters/gemini_cli.py`
- Test: `tests/harness_core/test_gemini_multimodal.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/harness_core/test_gemini_multimodal.py` 생성:

```python
import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "llm_interface"))

from harness_core.llm_adapters.gemini_cli import build_multimodal_prompt


def test_no_images_returns_prompt_unchanged():
    assert build_multimodal_prompt("hello", None) == "hello"
    assert build_multimodal_prompt("hello", []) == "hello"


def test_single_image_appends_absolute_path_reference():
    out = build_multimodal_prompt("describe", ["/tmp/leaf.png"])
    assert "describe" in out
    assert "@/tmp/leaf.png" in out


def test_relative_path_is_made_absolute():
    out = build_multimodal_prompt("describe", ["leaf.png"])
    expected = "@" + os.path.abspath("leaf.png")
    assert expected in out


def test_multiple_images_all_referenced():
    out = build_multimodal_prompt("describe", ["/a/x.png", "/b/y.jpg"])
    assert "@/a/x.png" in out
    assert "@/b/y.jpg" in out
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_gemini_multimodal.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_multimodal_prompt'`

- [ ] **Step 3: 헬퍼 구현**

`gemini_cli.py`의 import 블록 아래(예: `find_gemini_binary` 함수 위)에 추가:

```python
def build_multimodal_prompt(prompt: str, image_paths: list[str] | None) -> str:
    """Append gemini-cli @<path> references so images are loaded as multimodal input.

    Gemini CLI reads `@<path>` references inline in the -p prompt and attaches the
    referenced files (including images). Paths are made absolute for robustness.
    """
    if not image_paths:
        return prompt
    refs = "\n".join(f"@{os.path.abspath(p)}" for p in image_paths)
    return f"{prompt}\n\nAttached images:\n{refs}"
```

(`os`는 파일 상단에서 이미 import 되어 있다.)

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_gemini_multimodal.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f llm_interface/harness_core/llm_adapters/gemini_cli.py tests/harness_core/test_gemini_multimodal.py
git commit -m "feat(adapter): add build_multimodal_prompt helper for gemini image refs"
```

---

## Task 3: gemini 어댑터 `generate`에 `image_paths` 인자 연결

`generate`가 `image_paths`를 받아 헬퍼로 프롬프트를 보강한 뒤 CLI에 전달하도록 한다.

**Files:**
- Modify: `llm_interface/harness_core/llm_adapters/gemini_cli.py:135-148`

- [ ] **Step 1: `generate` 시그니처와 프롬프트 사용부 수정**

현재 (`gemini_cli.py` 135행 부근):

```python
    async def generate(self, prompt: str, expected_type: str = None, model: str = None) -> str:
        stat = await self.status()
        if not stat["ready"]:
            raise LLMContractError("provider_not_ready", "Gemini CLI is not authenticated or ready")

        model_to_use = model or "gemini-2.5-pro"
        exec_log.write("INFO", f"[gemini] model={model_to_use}")

        arg_variants = [
            [self.binary, "-p", prompt, "--model", model_to_use, "--print"],
            [self.binary, "run", "--prompt", prompt, "--model", model_to_use],
            [self.binary, "prompt", prompt, "--model", model_to_use],
            [self.binary, "-p", prompt],
        ]
```

다음으로 교체:

```python
    async def generate(self, prompt: str, expected_type: str = None, model: str = None,
                       image_paths: list[str] | None = None) -> str:
        stat = await self.status()
        if not stat["ready"]:
            raise LLMContractError("provider_not_ready", "Gemini CLI is not authenticated or ready")

        model_to_use = model or "gemini-2.5-pro"
        full_prompt = build_multimodal_prompt(prompt, image_paths)
        if image_paths:
            exec_log.write("INFO", f"[gemini] model={model_to_use}  |  images={len(image_paths)}")
        else:
            exec_log.write("INFO", f"[gemini] model={model_to_use}")

        arg_variants = [
            [self.binary, "-p", full_prompt, "--model", model_to_use, "--print"],
            [self.binary, "run", "--prompt", full_prompt, "--model", model_to_use],
            [self.binary, "prompt", full_prompt, "--model", model_to_use],
            [self.binary, "-p", full_prompt],
        ]
```

- [ ] **Step 2: 회귀 테스트 실행 (기존 테스트 깨지지 않음 확인)**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_gemini_multimodal.py -v`
Expected: PASS (변경은 시그니처 확장이며 헬퍼 동작은 그대로)

- [ ] **Step 3: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f llm_interface/harness_core/llm_adapters/gemini_cli.py
git commit -m "feat(adapter): thread image_paths into gemini generate"
```

---

## Task 4: `llm_runner`에 `image_paths` 관통

`generate_biopython_workflow`가 `image_paths`를 받아, 어댑터가 해당 인자를 지원하면 전달한다(기존 `model` 처리와 동일한 inspect 패턴). 프롬프트 빌더에는 이미지 존재 여부를 알린다.

**Files:**
- Modify: `llm_interface/harness_core/llm_runner.py:37-100`
- Test: `tests/harness_core/test_llm_runner_image_paths.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/harness_core/test_llm_runner_image_paths.py` 생성:

```python
import asyncio
import sys
import pathlib
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "llm_interface"))

from harness_core import llm_runner

FAKE_RAW = '{"goal":"g","nodes":[{"id":"n1","class_type":"SeqIO_read"}],"edges":[]}'


def test_image_paths_forwarded_to_adapter():
    async def _run():
        fake_adapter = AsyncMock()
        # generate accepts image_paths -> inspect must detect & pass it
        async def _gen(prompt, expected_type=None, model=None, image_paths=None):
            assert image_paths == ["/tmp/leaf.png"]
            return FAKE_RAW
        fake_adapter.generate = _gen

        with (
            patch("harness_core.llm_runner.get_adapter", return_value=fake_adapter),
            patch("harness_core.workflow_history.find_similar", return_value=[]),
        ):
            spec = await llm_runner.generate_biopython_workflow(
                "gemini", "measure leaf area", input_path="",
                image_paths=["/tmp/leaf.png"],
            )
        assert spec["nodes"][0]["class_type"] == "SeqIO_read"
    asyncio.run(_run())
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_llm_runner_image_paths.py -v`
Expected: FAIL — `generate_biopython_workflow() got an unexpected keyword argument 'image_paths'`

- [ ] **Step 3: 러너 수정**

`generate_biopython_workflow` 시그니처에 `image_paths` 추가 (37-44행):

```python
async def generate_biopython_workflow(
    provider: str,
    goal: str,
    input_path: str = "",
    output_dir: str = "./output",
    job_id: str | None = None,
    model: str | None = None,
    image_paths: list[str] | None = None,
) -> dict:
```

프롬프트 빌더 호출(72-74행)에 이미지 여부 전달:

```python
    prompt  = get_biopython_workflow_prompt(
        goal, input_path, output_dir, similar_workflow=similar_workflow,
        has_images=bool(image_paths),
    )
```

`_run` 내부 kwargs 구성(80-85행)에 image_paths 지원 시 전달 추가:

```python
        sig    = inspect.signature(adapter.generate)
        params = sig.parameters
        accepts_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        kwargs: dict = {"expected_type": "biopython_workflow_spec"}
        if "model" in params or accepts_kw:
            kwargs["model"] = model
        if image_paths and ("image_paths" in params or accepts_kw):
            kwargs["image_paths"] = image_paths
```

> Task 5에서 `get_biopython_workflow_prompt`에 `has_images` 인자를 추가한다. 본 Task의 테스트는 `find_similar`를 mock 하므로, `has_images` 인자가 아직 없으면 Step 4에서 실패한다 — Task 5를 먼저 적용하거나 두 Task를 함께 커밋해도 된다. 권장: **Task 5를 먼저 수행한 뒤 본 Step 4 실행.**

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_llm_runner_image_paths.py -v`
Expected: PASS (Task 5 적용 후)

- [ ] **Step 5: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f llm_interface/harness_core/llm_runner.py tests/harness_core/test_llm_runner_image_paths.py
git commit -m "feat(runner): forward image_paths to image-capable adapters"
```

---

## Task 5: 프롬프트 빌더 — 이미지 보강

이미지가 첨부되면 LLM에게 "첨부된 표현형 이미지를 해석해 노드 선택에 반영하라"고 명시한다.

**Files:**
- Modify: `llm_interface/harness_core/biopython_prompts.py:58-125`
- Test: `tests/harness_core/test_phenotype_prompts.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/harness_core/test_phenotype_prompts.py` 생성:

```python
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "llm_interface"))

from harness_core.biopython_prompts import get_biopython_workflow_prompt


def test_no_images_has_no_image_section():
    p = get_biopython_workflow_prompt("measure leaf area", has_images=False)
    assert "Attached Image" not in p


def test_images_add_instruction_section():
    p = get_biopython_workflow_prompt("measure leaf area", has_images=True)
    assert "Attached Image" in p
    assert "phenotyp" in p.lower()


def test_default_has_images_is_false():
    # backward-compatible: existing callers omit has_images
    p = get_biopython_workflow_prompt("parse fasta")
    assert "Attached Image" not in p
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_phenotype_prompts.py -v`
Expected: FAIL — `get_biopython_workflow_prompt() got an unexpected keyword argument 'has_images'`

- [ ] **Step 3: 프롬프트 빌더 수정**

`get_biopython_workflow_prompt` 시그니처(58-63행)에 `has_images` 추가:

```python
def get_biopython_workflow_prompt(
    goal: str,
    input_path: str = "",
    output_dir: str = "./output",
    similar_workflow: dict | None = None,
    has_images: bool = False,
) -> str:
```

`reuse_note` 정의 직후(82행 근처, `return f"""...` 앞)에 이미지 노트 구성 추가:

```python
    image_note = ""
    if has_images:
        image_note = """

## Attached Image(s)
One or more phenotype images are attached to this request (leaf, disease lesion, or seed photos).
Interpret the image content and let it drive node selection: choose nodes that measure or analyse
the phenotype shown. Prefer nodes in the Breeding/Phenotype category when the image is a plant trait.
"""
```

`return f"""..."""` 본문의 헤더 직후(예: `## Available Nodes` 줄 앞)에 `{image_note}`를 삽입한다. 구체적으로 83-87행:

```python
    return f"""You are a Biopython workflow designer for ComfyUI.

Given the user's analysis goal, select the minimum set of Biopython nodes that accomplish it and connect them in the correct data-flow order.
{image_note}
## Available Nodes
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_core/test_phenotype_prompts.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f llm_interface/harness_core/biopython_prompts.py tests/harness_core/test_phenotype_prompts.py
git commit -m "feat(prompts): add image-aware instruction section"
```

---

## Task 6: API 라우트 — `image_paths` 수신·전달

`/comfybio/generate`가 요청 body의 `image_paths`를 읽어 러너에 넘긴다. 기존 단위 테스트의 호출 단언을 갱신한다.

**Files:**
- Modify: `llm_interface/harness_nodes/__init__.py:257-283`
- Test: `tests/harness_nodes/test_generate_api.py:46-89`

- [ ] **Step 1: 기존 테스트를 image_paths 포함하도록 갱신 (실패 상태로)**

`tests/harness_nodes/test_generate_api.py`의 `request_data`(57-63행)에 image_paths 추가:

```python
            request_data = {
                "query": "parse fasta",
                "input_path": "/data/test.fasta",
                "output_dir": "/out",
                "provider": "claude",
                "model": "",
                "image_paths": ["/data/leaf.png"],
            }
```

그리고 호출 단언(87행)을 교체:

```python
            mock_gen.assert_called_once_with(
                "claude", "parse fasta", "/data/test.fasta", "/out",
                model=None, image_paths=["/data/leaf.png"],
            )
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_nodes/test_generate_api.py -v`
Expected: FAIL — 실제 호출에 `image_paths`가 없어 `assert_called_once_with` 불일치

- [ ] **Step 3: API 라우트 수정**

`api_generate`에서 body 파싱부(259-264행)에 추가:

```python
        data        = await request.json()
        query       = data.get("query", "").strip()
        input_path  = data.get("input_path", "")
        output_dir  = data.get("output_dir", "./output")
        provider    = data.get("provider", "claude")
        model       = data.get("model", "").strip() or None
        image_paths = data.get("image_paths") or []
```

러너 호출부(281-283행)를 교체:

```python
        gen_task = asyncio.create_task(
            generate_biopython_workflow(
                provider, query, input_path, output_dir,
                model=model, image_paths=image_paths,
            )
        )
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/harness_nodes/test_generate_api.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f llm_interface/harness_nodes/__init__.py tests/harness_nodes/test_generate_api.py
git commit -m "feat(api): accept image_paths in /comfybio/generate"
```

---

## Task 7: 앵커용 최소 표현형 이미지 노드

앵커 시나리오를 지탱할 노드 1개. 이미지 경로를 입력받아 기본 정보(크기)를 출력하며, `input_path`를 입력으로 가져 `build_registry`가 is_input_node로 인식한다. `Breeding/Phenotype` 카테고리로 카탈로그에 노출된다.

**Files:**
- Create: `py/Phenotype_Image_Objects.py`
- Test: `tests/py/test_phenotype_image_node.py`
- Regenerate: `llm_interface/harness_core/node_registry.json`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/py/test_phenotype_image_node.py` 생성:

```python
import sys
import pathlib
from unittest.mock import MagicMock

# Stub comfy_api so the node module imports without ComfyUI runtime
ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "py"))

import importlib.util
from PIL import Image


def _load_node_module():
    spec = importlib.util.spec_from_file_location(
        "Phenotype_Image_Objects", str(ROOT / "py" / "Phenotype_Image_Objects.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_schema_declares_node_id_and_category():
    mod = _load_node_module()
    schema = mod.PhenotypeImage_info.define_schema()
    assert schema.node_id == "PhenotypeImage_info"
    assert schema.category == "Breeding/Phenotype"


def test_execute_returns_image_dimensions(tmp_path):
    mod = _load_node_module()
    img_path = tmp_path / "leaf.png"
    Image.new("RGB", (40, 30), (10, 200, 10)).save(img_path)
    out = mod.PhenotypeImage_info.execute(str(img_path))
    # io.NodeOutput wraps positional results
    values = list(out) if not hasattr(out, "result") else out.result
    assert 40 in values  # width
    assert 30 in values  # height
```

> 참고: `io.NodeOutput` 내부 표현이 환경마다 다를 수 있으므로, Step 4에서 실패 메시지를 보고 `values` 추출부를 실제 형태에 맞춘다(아래 구현은 `io.NodeOutput(info, w, h)` 형태).

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/py/test_phenotype_image_node.py -v`
Expected: FAIL — `Phenotype_Image_Objects.py` 없음

- [ ] **Step 3: 노드 구현**

`py/Phenotype_Image_Objects.py` 생성:

```python
from __future__ import annotations
from typing_extensions import override
# pyrefly: ignore [missing-import]
from comfy_api.latest import io
from PIL import Image


class PhenotypeImage_info(io.ComfyNode):
    """Load a plant phenotype image and report basic geometry.

    Minimal anchor node for the multimodal PoC: gives the workflow a concrete
    Breeding/Phenotype entry point that consumes an image path.
    """
    OUTPUT_NODE = True

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PhenotypeImage_info",
            display_name="Phenotype image info",
            category="Breeding/Phenotype",
            inputs=[
                io.String.Input("input_path", multiline=False, default=""),
            ],
            outputs=[
                io.String.Output("info"),
                io.Int.Output("width"),
                io.Int.Output("height"),
            ],
        )

    @classmethod
    def execute(cls, input_path) -> io.NodeOutput:
        with Image.open(input_path) as im:
            w, h = im.size
            mode = im.mode
        return io.NodeOutput(f"{w}x{h} {mode}", w, h)
```

- [ ] **Step 4: 테스트 실행하여 통과 확인 (필요 시 추출부 보정)**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests/py/test_phenotype_image_node.py -v`
Expected: PASS. 만약 `io.NodeOutput` 언패킹이 실패하면, 테스트의 `values` 추출부를 실제 객체 속성(예: `out.args` 또는 인덱싱)에 맞춰 1회 수정 후 재실행.

- [ ] **Step 5: 레지스트리 재생성 및 확인**

Run:
```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython/llm_interface/harness_core
python build_registry.py
python -c "import json; r=json.load(open('node_registry.json')); n=r['PhenotypeImage_info']; print(n['category'], n.get('is_input_node'))"
```
Expected: `PhenotypeImage_info`가 출력되고 `Breeding/Phenotype True` (input_path 보유 → is_input_node).

- [ ] **Step 6: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f py/Phenotype_Image_Objects.py tests/py/test_phenotype_image_node.py llm_interface/harness_core/node_registry.json
git commit -m "feat(node): add PhenotypeImage_info anchor node + rebuild registry"
```

---

## Task 8: 엔드투엔드 앵커 시나리오 검증 (성공 기준 확정)

> 외부 CLI·인증·네트워크가 필요한 **수동 통합 검증**. spec §3 Phase 1의 성공 기준 3가지를 실제로 확인하고 결과를 프로브 문서에 추가 기록한다.

**Files:**
- Modify: `docs/superpowers/experiments/2026-06-04-cli-image-probe.md` (E2E 결과 절 추가)

- [ ] **Step 1: 전체 자동 테스트 통과 확인**

Run: `cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython && python -m pytest tests -v`
Expected: 모든 테스트 PASS (Task 2~7에서 추가/수정한 테스트 포함).

- [ ] **Step 2: 표현형 테스트 이미지 준비**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
python -c "from PIL import Image; Image.new('RGB',(256,256),(34,139,34)).save('/tmp/leaf.png')"
```

- [ ] **Step 3: 러너 직접 호출로 E2E 검증 스크립트 실행**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
python - <<'PY'
import asyncio, sys, pathlib
sys.path.insert(0, str(pathlib.Path("llm_interface")))
from harness_core.llm_runner import generate_biopython_workflow
from harness_core.llm_contracts import parse_and_validate_llm_output

async def main():
    spec = await generate_biopython_workflow(
        provider="gemini",
        goal="Analyse the attached plant phenotype image and propose a measurement workflow.",
        input_path="/tmp/leaf.png",
        image_paths=["/tmp/leaf.png"],
    )
    print("NODES:", [n["class_type"] for n in spec["nodes"]])
    print("VALID:", isinstance(spec.get("nodes"), list) and len(spec["nodes"]) >= 1)

asyncio.run(main())
PY
```

- [ ] **Step 4: 성공 기준 판정 및 기록**

3가지 성공 기준을 확인하고 프로브 문서에 기록:
1. **이미지 통과**: exec_log/응답상 이미지가 전달되었는가 (Task 1에서 이미 확인된 형식 사용).
2. **이미지 반영**: 선택된 노드에 `PhenotypeImage_info` 등 표현형/측정 노드가 포함되는가. (대조: `image_paths` 없이 동일 goal 실행 시와 노드 선택이 달라지는가.)
3. **계약 통과**: 위 스크립트가 예외 없이 spec을 반환했는가(`generate_biopython_workflow` 내부에서 이미 `parse_and_validate_llm_output` 통과).

Expected: 세 기준 모두 충족 → Phase 1 멀티모달 타당성 **검증 완료**. 미충족 항목이 있으면 프로브 문서에 원인과 후속 조치를 기록.

- [ ] **Step 5: 커밋**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
git add -f docs/superpowers/experiments/2026-06-04-cli-image-probe.md
git commit -m "docs(experiment): record Phase 1 multimodal E2E verification"
```

---

## 마무리

- Phase 1 완료 후 `superpowers:finishing-a-development-branch`로 통합 방식을 결정한다.
- 본 Phase에서 확정된 `image_paths` 배선·프롬프트 보강·앵커 노드 패턴은 Phase 2~5(육종 노드군, 표현형/필드 데이터, 외부 DB 연동, 엔진 도메인 인식)의 토대가 된다. 각 Phase는 별도 spec → plan 사이클로 상세화한다.
