# Direct Generate API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PROMPT 탭에서 입력된 프롬프트를 `POST /comfybio/generate` API를 통해 직접 LLM에 전달하고, 생성된 워크플로우를 SSE 스트림으로 수신해 ComfyUI 캔버스에 로드한다.

**Architecture:** 현재 `BiopythonWorkflowGenerator` 캔버스 노드 → `app.queuePrompt()` 경로를 완전 제거하고, `POST /comfybio/generate` SSE 엔드포인트로 대체한다. 백엔드는 exec_log 구독 메커니즘을 통해 LLM 실행 중 발생하는 상태 메시지를 실시간으로 SSE 스트림에 포워딩한다. 프론트엔드는 SSE 스트림을 읽어 로그를 렌더링하고, `done` 이벤트에서 `app.loadGraphData()`로 캔버스에 직접 로드한다.

**Tech Stack:** Python/aiohttp (SSE), asyncio.Queue (exec_log subscriber), ComfyUI PromptServer, Vanilla JS (fetch + ReadableStream)

---

## File Map

| 파일 | 변경 |
|------|------|
| `llm_interface/harness_core/exec_log.py` | `subscribe()` / `unsubscribe()` 추가 |
| `llm_interface/harness_nodes/__init__.py` | `POST /comfybio/generate` SSE 엔드포인트 추가; `NODE_CLASS_MAPPINGS`, `ComfyBIOLLMExtension` 제거 |
| `llm_interface/harness_nodes/nodes.py` | 삭제 (`BiopythonWorkflowGenerator` 클래스 제거) |
| `llm_interface/harness_nodes/web/comfybio_test_load.js` | `triggerGeneration()` 교체; 폴링 인프라 제거 |
| `llm_interface/harness_nodes/web/workflow_loader.js` | 삭제 (캔버스 노드 onExecuted 훅 불필요) |
| `__init__.py` | `_collect_llm_nodes()` 제거 |
| `tests/harness_nodes/test_generate_api.py` | 신규 생성 — generate 엔드포인트 테스트 |

---

## Task 1: exec_log에 subscriber 메커니즘 추가

**Files:**
- Modify: `llm_interface/harness_core/exec_log.py`
- Test: `tests/harness_core/test_exec_log_subscriber.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/harness_core/test_exec_log_subscriber.py
import asyncio
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "llm_interface"))

from harness_core import exec_log


def test_subscriber_receives_written_entries():
    async def _run():
        exec_log.clear()
        q = exec_log.subscribe()
        try:
            exec_log.write("INFO", "hello")
            entry = await asyncio.wait_for(q.get(), timeout=1.0)
            assert entry["level"] == "INFO"
            assert entry["msg"] == "hello"
        finally:
            exec_log.unsubscribe(q)
    asyncio.run(_run())


def test_unsubscribed_queue_receives_nothing():
    async def _run():
        exec_log.clear()
        q = exec_log.subscribe()
        exec_log.unsubscribe(q)
        exec_log.write("INFO", "after unsub")
        assert q.empty()
    asyncio.run(_run())


def test_multiple_subscribers():
    async def _run():
        exec_log.clear()
        q1 = exec_log.subscribe()
        q2 = exec_log.subscribe()
        try:
            exec_log.write("WARN", "broadcast")
            e1 = await asyncio.wait_for(q1.get(), timeout=1.0)
            e2 = await asyncio.wait_for(q2.get(), timeout=1.0)
            assert e1["msg"] == e2["msg"] == "broadcast"
        finally:
            exec_log.unsubscribe(q1)
            exec_log.unsubscribe(q2)
    asyncio.run(_run())
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /home/ydj/main/ComfyUI/custom_nodes/ComfyBIO_biopython
python -m pytest tests/harness_core/test_exec_log_subscriber.py -v
```

Expected: `AttributeError: module 'harness_core.exec_log' has no attribute 'subscribe'`

- [ ] **Step 3: exec_log.py에 subscriber 구현**

```python
# llm_interface/harness_core/exec_log.py
"""
Module-level execution log buffer.
Shared between llm_runner and adapters; exposed via /comfybio/execution_log.
"""
import asyncio
import collections
import datetime

_buffer: collections.deque = collections.deque(maxlen=200)
_subscribers: list[asyncio.Queue] = []


def write(level: str, message: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    entry = {"ts": ts, "level": level, "msg": message}
    _buffer.append(entry)
    for q in _subscribers:
        q.put_nowait(entry)


def snapshot() -> list[dict]:
    return list(_buffer)


def clear() -> None:
    _buffer.clear()


def subscribe() -> asyncio.Queue:
    """Return a queue that receives every future write() call."""
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    try:
        _subscribers.remove(q)
    except ValueError:
        pass
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/harness_core/test_exec_log_subscriber.py -v
```

Expected: `3 passed`

- [ ] **Step 5: 커밋**

```bash
git add llm_interface/harness_core/exec_log.py tests/harness_core/test_exec_log_subscriber.py
git commit -m "feat(exec_log): add subscribe/unsubscribe for SSE forwarding"
```

---

## Task 2: `POST /comfybio/generate` SSE 엔드포인트 추가

**Files:**
- Modify: `llm_interface/harness_nodes/__init__.py` (상단 imports 아래, `api_execution_log` 다음에 추가)
- Test: `tests/harness_nodes/test_generate_api.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/harness_nodes/test_generate_api.py
"""
테스트 전략: generate_biopython_workflow 와 canonical_to_comfy_json 을 mock 처리해
SSE 스트림 형식과 workflow_history 기록만 검증한다.
"""
import asyncio
import json
import sys
import pathlib
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "llm_interface"))

import pytest
from aiohttp.test_utils import make_mocked_request
from aiohttp import web


FAKE_SPEC = {
    "goal": "test",
    "nodes": [{"id": "n1", "class_type": "SeqIO_read"}],
    "edges": [],
}

FAKE_COMFY = {
    "last_node_id": 1,
    "last_link_id": 0,
    "nodes": [{"id": 1, "type": "SeqIO_read"}],
    "links": [],
    "groups": [],
    "config": {},
    "extra": {},
    "version": 0.4,
}


def _collect_sse(body: bytes) -> list[dict]:
    events = []
    for line in body.decode().splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_generate_streams_status_and_done():
    from aiohttp.test_utils import TestServer, TestClient
    from server import PromptServer  # patched below

    # Build a minimal aiohttp app with only the generate route
    app = web.Application()

    with (
        patch("harness_core.llm_runner.generate_biopython_workflow", new_callable=AsyncMock, return_value=FAKE_SPEC),
        patch("harness_core.biopython_comfy_adapter.canonical_to_comfy_json", return_value=FAKE_COMFY),
        patch("harness_core.biopython_comfy_adapter.load_registry", return_value={}),
        patch("harness_core.workflow_history.append_record"),
    ):
        # Import route handler after patching
        # We test it directly by calling the handler with a mock request
        from harness_nodes import api_generate  # noqa: F401 — imported for side-effect

        async with TestClient(TestServer(app)) as client:
            # Direct handler call
            request_data = {
                "query": "parse fasta",
                "input_path": "/data/test.fasta",
                "output_dir": "/out",
                "provider": "claude",
                "model": "",
            }
            # Build mock request
            mock_req = MagicMock()
            mock_req.json = AsyncMock(return_value=request_data)

            # Collect SSE by monkey-patching StreamResponse
            written: list[bytes] = []

            mock_resp = MagicMock()
            mock_resp.prepare = AsyncMock()
            mock_resp.write = AsyncMock(side_effect=lambda b: written.append(b))
            mock_resp.write_eof = AsyncMock()

            with patch("aiohttp.web.StreamResponse", return_value=mock_resp):
                from harness_nodes._generate import api_generate_handler
                await api_generate_handler(mock_req)

            all_body = b"".join(written)
            events = _collect_sse(all_body)

            types = [e["type"] for e in events]
            assert "status" in types
            assert types[-1] == "done"
            done_event = next(e for e in events if e["type"] == "done")
            assert done_event["workflow"] == FAKE_COMFY
            assert done_event["node_count"] == 1
```

> **Note:** 테스트가 복잡하므로 Step 3에서 구현 후 단순화할 수 있다. 핵심 검증 포인트: (1) SSE 스트림에 `status` 이벤트 포함, (2) 마지막 이벤트가 `done`이고 `workflow` 키를 가짐.

- [ ] **Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/harness_nodes/test_generate_api.py -v 2>&1 | head -30
```

Expected: `ImportError` 또는 `ModuleNotFoundError`

- [ ] **Step 3: `POST /comfybio/generate` 엔드포인트 구현**

`llm_interface/harness_nodes/__init__.py` 에서 `api_execution_log` 핸들러 바로 다음에 추가:

```python
    @PromptServer.instance.routes.post("/comfybio/generate")
    async def api_generate(request: web.Request) -> web.StreamResponse:
        data        = await request.json()
        query       = data.get("query", "").strip()
        input_path  = data.get("input_path", "")
        output_dir  = data.get("output_dir", "./output")
        provider    = data.get("provider", "claude")
        model       = data.get("model", "").strip() or None

        from harness_core.llm_runner import generate_biopython_workflow
        from harness_core.biopython_comfy_adapter import canonical_to_comfy_json, load_registry

        resp = web.StreamResponse(headers={
            "Content-Type":    "text/event-stream",
            "Cache-Control":   "no-cache",
            "X-Accel-Buffering": "no",
        })
        await resp.prepare(request)

        async def send(event_type: str, msg: str = "", **extra) -> None:
            payload = {"type": event_type, "msg": msg, **extra}
            await resp.write(f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode())

        q = exec_log.subscribe()
        gen_task = asyncio.create_task(
            generate_biopython_workflow(provider, query, input_path, output_dir, model=model)
        )

        try:
            # 실시간으로 exec_log 메시지 포워딩
            while not gen_task.done():
                try:
                    entry = await asyncio.wait_for(q.get(), timeout=0.15)
                    level = entry.get("level", "INFO")
                    await send("log", entry["msg"], level=level)
                except asyncio.TimeoutError:
                    pass

            # 큐 잔여 항목 flush
            while not q.empty():
                entry = q.get_nowait()
                await send("log", entry["msg"], level=entry.get("level", "INFO"))

            spec = gen_task.result()  # 예외가 있으면 여기서 raise

            await send("status", "워크플로우 JSON 변환 중…")
            registry   = load_registry()
            comfy_json = canonical_to_comfy_json(spec, registry, input_path, output_dir)
            n_nodes    = len(spec.get("nodes", []))
            n_edges    = len(spec.get("edges", []))

            workflow_history.append_record({
                "query":         query,
                "input_path":    input_path,
                "output_dir":    output_dir,
                "provider":      provider,
                "model":         model or "",
                "status":        "success",
                "workflow_json": comfy_json,
                "workflow_spec": spec,
                "node_count":    n_nodes,
                "edge_count":    n_edges,
            })

            await send("done",
                       f"{n_nodes}개 노드, {n_edges}개 엣지 생성 완료",
                       workflow=comfy_json,
                       node_count=n_nodes)

        except Exception as exc:
            workflow_history.append_record({
                "query":         query,
                "input_path":    input_path,
                "output_dir":    output_dir,
                "provider":      provider,
                "model":         model or "",
                "status":        "error",
                "error_message": str(exc),
            })
            await send("error", str(exc))

        finally:
            exec_log.unsubscribe(q)
            await resp.write_eof()

        return resp
```

- [ ] **Step 4: 수동 연기 테스트 (ComfyUI 서버 실행 중인 경우)**

```bash
curl -s -N -X POST http://localhost:8188/comfybio/generate \
  -H "Content-Type: application/json" \
  -d '{"query":"parse fasta","input_path":"","output_dir":"./output","provider":"deterministic","model":""}' \
  | head -20
```

Expected: SSE 이벤트 스트림 (`data: {"type": "log", ...}` 라인들)

- [ ] **Step 5: 커밋**

```bash
git add llm_interface/harness_nodes/__init__.py
git commit -m "feat(api): add POST /comfybio/generate SSE endpoint"
```

---

## Task 3: `triggerGeneration()` SSE 클라이언트로 교체

**Files:**
- Modify: `llm_interface/harness_nodes/web/comfybio_test_load.js`

- [ ] **Step 1: 제거할 코드 범위 확인**

`comfybio_test_load.js` 에서 제거 대상:
- Line 492–506: 캔버스 empty 체크 및 genNode 체크 블록
- Line 514–521: 노드 widget 동기화 (`vals`, `for ... widget`)
- Line 521: `app.canvas?.draw(true, true)`
- Line 534: `startPolling()`
- Line 537–544: `app.queuePrompt()` try/catch 블록
- Setup 섹션 Line 1028–1075: `app.api.addEventListener("executing")`, `"execution_error"`, `"status"` 핸들러, `comfybio:workflow-loaded`, `comfybio:workflow-error` 이벤트 리스너

- [ ] **Step 2: `triggerGeneration()` 함수 전체 교체**

`comfybio_test_load.js` 의 `triggerGeneration` 함수(line 482~545)를 아래로 교체:

```javascript
async function triggerGeneration() {
    showPromptLog();
    clearPromptLog();

    const query = _el("cb-query")?.value.trim() ?? "";
    if (!query) {
        _appendPromptLine("ERROR", "Please enter a goal.");
        return;
    }

    const inputPath = getEffectiveInputPath();
    const outputDir = getEffectiveOutputDir();
    const provider  = _state.provider;
    const model     = _el("cb-model")?.value ?? _state.model;

    _generating = true;
    _el("cb-generate-btn").disabled = true;

    _appendPromptLine("INFO", `Provider: ${provider}  |  Model: ${model || "default"}`);
    _appendPromptLine("INFO", `Goal: ${query.slice(0, 100)}${query.length > 100 ? "…" : ""}`);

    try {
        const resp = await fetch("/comfybio/generate", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                query,
                input_path: inputPath,
                output_dir: outputDir,
                provider,
                model,
            }),
        });

        if (!resp.ok) {
            throw new Error(`Server error: HTTP ${resp.status}`);
        }

        const reader  = resp.body.getReader();
        const decoder = new TextDecoder();
        let   buffer  = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();  // 미완성 줄은 다음 청크와 합침

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                let event;
                try { event = JSON.parse(line.slice(6)); } catch { continue; }

                if (event.type === "log") {
                    const level = event.level === "ERROR" ? "ERROR"
                                : event.level === "WARN"  ? "WARN"
                                : "INFO";
                    _appendPromptLine(level, event.msg);
                } else if (event.type === "status") {
                    _appendPromptLine("INFO", event.msg);
                } else if (event.type === "error") {
                    _appendPromptLine("ERROR", `❌ ${event.msg}`);
                    _generating = false;
                    _el("cb-generate-btn").disabled = false;
                    return;
                } else if (event.type === "done") {
                    _appendPromptLine("INFO", `✅ ${event.msg}`);
                    try {
                        await app.loadGraphData(event.workflow);
                        const n = event.node_count ?? "?";
                        _appendPromptLine("INFO", `캔버스에 ${n}개 노드 로드 완료`);
                    } catch (loadErr) {
                        _appendPromptLine("ERROR", `캔버스 로드 실패: ${loadErr.message}`);
                    }
                    _generating = false;
                    _el("cb-generate-btn").disabled = false;
                    return;
                }
            }
        }

    } catch (err) {
        _appendPromptLine("ERROR", `생성 실패: ${err.message}`);
        _generating = false;
        _el("cb-generate-btn").disabled = false;
    }
}
```

- [ ] **Step 3: setup() 에서 불필요한 이벤트 리스너 제거**

`app.registerExtension` 의 `setup()` 함수 안에서 아래 블록 전체 삭제:

```javascript
// 삭제 대상 1: line ~1027–1035
app.api.addEventListener("executing", e => { ... });

// 삭제 대상 2: line ~1037–1046
app.api.addEventListener("execution_error", e => { ... });

// 삭제 대상 3: line ~1048–1054
app.api.addEventListener("status", e => { ... });

// 삭제 대상 4: line ~1057–1067
document.addEventListener("comfybio:workflow-loaded", async e => { ... });

// 삭제 대상 5: line ~1069–1075
document.addEventListener("comfybio:workflow-error", async e => { ... });
```

- [ ] **Step 4: 폴링 관련 함수/변수 정리**

`_pollTimer`, `_lastLogCount`, `_poll`, `startPolling`, `stopPolling` 제거:
- Line 26: `let _pollTimer = null;`
- Line 27: `let _lastLogCount = 0;`
- Lines 458–479: `_poll()`, `startPolling()`, `stopPolling()` 함수 블록 전체 삭제

- [ ] **Step 5: ComfyUI 재시작 후 수동 테스트**

```
1. ComfyUI 시작
2. 🧬 버튼 클릭 → 패널 열기
3. LLM 탭에서 provider: deterministic 선택
4. PROMPT 탭 이동 → "parse a fasta file and compute GC content" 입력
5. Generate Workflow 클릭
6. 로그에 상태 메시지가 순서대로 표시되는지 확인
7. 완료 후 캔버스에 노드들이 로드되는지 확인
```

- [ ] **Step 6: 커밋**

```bash
git add llm_interface/harness_nodes/web/comfybio_test_load.js
git commit -m "feat(ui): replace queuePrompt with direct SSE generate API"
```

---

## Task 4: `BiopythonWorkflowGenerator` 캔버스 노드 제거

**Files:**
- Delete: `llm_interface/harness_nodes/nodes.py`
- Delete: `llm_interface/harness_nodes/web/workflow_loader.js`
- Modify: `llm_interface/harness_nodes/__init__.py`
- Modify: `__init__.py`

- [ ] **Step 1: `nodes.py` 삭제**

```bash
git rm llm_interface/harness_nodes/nodes.py
```

- [ ] **Step 2: `workflow_loader.js` 삭제**

```bash
git rm llm_interface/harness_nodes/web/workflow_loader.js
```

- [ ] **Step 3: `harness_nodes/__init__.py` 에서 노드 등록 코드 제거**

아래 3개 블록 삭제:

```python
# 삭제: 파일 상단 import
from harness_nodes.nodes import BiopythonWorkflowGenerator, HAS_COMFY

# 삭제: 노드 매핑 딕셔너리
NODE_CLASS_MAPPINGS = {
    "BiopythonWorkflowGenerator": BiopythonWorkflowGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BiopythonWorkflowGenerator": "Biopython Workflow Generator",
}
```

파일 하단의 ComfyExtension 블록도 삭제:

```python
# 삭제: 파일 하단
if HAS_COMFY:
    from comfy_api.latest import ComfyExtension

    class ComfyBIOLLMExtension(ComfyExtension):
        async def get_node_list(self) -> list:
            return [BiopythonWorkflowGenerator]

    async def comfy_entrypoint() -> ComfyBIOLLMExtension:
        return ComfyBIOLLMExtension()
```

- [ ] **Step 4: 루트 `__init__.py` 에서 `_collect_llm_nodes` 제거**

`__init__.py` 에서 아래 함수 전체 삭제:

```python
def _collect_llm_nodes() -> list[type[io.ComfyNode]]:
    """Load the BiopythonWorkflowGenerator node from llm_interface."""
    try:
        from harness_nodes.nodes import BiopythonWorkflowGenerator
        return [BiopythonWorkflowGenerator]
    except Exception as exc:
        print(f"[ComfyBIO] LLM interface not available: {exc}")
        return []
```

`get_node_list()` 에서 `+ _collect_llm_nodes()` 제거:

```python
# 변경 전
return _collect_biopython_nodes() + _collect_llm_nodes()

# 변경 후
return _collect_biopython_nodes()
```

- [ ] **Step 5: ComfyUI 재시작 후 확인**

```
1. ComfyUI 재시작
2. 브라우저 콘솔에서 "BiopythonWorkflowGenerator" 관련 오류 없는지 확인
3. Right-click → Add Node → ComfyBIO/LLM 메뉴가 사라진 것 확인
4. PROMPT 탭에서 generate 여전히 동작하는지 확인
```

- [ ] **Step 6: 커밋**

```bash
git add __init__.py llm_interface/harness_nodes/__init__.py
git commit -m "refactor: remove BiopythonWorkflowGenerator canvas node and workflow_loader.js"
```

---

## Self-Review

**Spec coverage:**
- [x] PROMPT 입력 → 직접 LLM 호출: Task 2 (generate 엔드포인트), Task 3 (triggerGeneration)
- [x] 실시간 스트리밍 상태 메시지: Task 1 (exec_log subscriber) + Task 2 (SSE forward)
- [x] 에러/경고 별도 강조: Task 3 (`level === "ERROR"` → `_appendPromptLine("ERROR", ...)`)
- [x] 워크플로우 히스토리 저장: Task 2 (`workflow_history.append_record()` 성공/실패 모두)
- [x] 캔버스 노드 완전 제거: Task 4
- [x] `workflow_loader.js` 제거: Task 4

**Placeholder scan:** 없음. 모든 스텝에 실제 코드 포함.

**Type consistency:**
- `send()` 함수 시그니처: Task 2에서 정의 → Task 3 JS에서 매핑 일치
- SSE 이벤트 타입 (`log`, `status`, `error`, `done`): Task 2와 Task 3에서 동일
- `node_count` 필드: Task 2 `send("done", ..., node_count=n_nodes)` → Task 3 `event.node_count` 일치
