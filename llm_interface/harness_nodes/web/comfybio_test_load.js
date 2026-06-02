import { app } from "../../scripts/app.js";

// ── State ──────────────────────────────────────────────────────────────────────
const _state = {
    provider: "claude",
    model: "",
    models: [],
    inputPath: "",
    outputDir: "",
    activeTab: "llm",
    browserTarget: "input",
    browserPath: "",
    browserPathByTarget: {
        input: "",
        output: "",
    },
    quickPaths: {
        home: "",
        root: "/",
        input: "",
        output: "",
    },
};

let _generating = false;
let _promptLines = [];

// status cache: {provider → {data, ts}}
const _statusCache = {};
const STATUS_TTL_MS = 30_000;

let _cachedStatus = null;
let _cachedModels = null;

// ── Helpers ────────────────────────────────────────────────────────────────────
function _el(id) { return document.getElementById(id); }
function _esc(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
function _now() {
    return new Date().toLocaleTimeString("en", { hour12: false });
}
function _capitalize(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}
function _fmtSize(bytes) {
    if (bytes == null) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
function _basename(path) {
    return String(path || "").split(/[\\/]/).filter(Boolean).pop() || path || "/";
}
async function _browsePath(path) {
    const url = `/comfybio/browse_path?path=${encodeURIComponent(path || "")}`;
    return fetch(url).then(r => r.json());
}

// ── Tab switching ──────────────────────────────────────────────────────────────
function switchTab(tabId) {
    _state.activeTab = tabId;
    document.querySelectorAll(".cb-tab-btn").forEach(btn =>
        btn.classList.toggle("active", btn.dataset.tab === tabId));
    document.querySelectorAll(".cb-tab-pane").forEach(pane =>
        pane.style.display = pane.dataset.pane === tabId ? "flex" : "none");
}

// ── LLM tab log ────────────────────────────────────────────────────────────────
function renderLLMLog(statusData, modelsData) {
    const box = _el("cb-llm-log");
    if (!box) return;

    const installed = statusData?.installed ?? false;
    const ready = statusData?.ready ?? false;
    const label = _capitalize(_state.provider);

    let html;
    if (!installed) {
        html = `<div class="cb-status-card cb-status-err">
            <span class="cb-status-icon">❌</span>
            <div class="cb-status-content">
                <div class="cb-status-msg">${label} CLI not installed</div>
                <button class="cb-btn cb-btn-secondary cb-status-action" id="cb-install-btn">
                    Install
                </button>
            </div>
        </div>`;
    } else if (!ready) {
        html = `<div class="cb-status-card cb-status-warn">
            <span class="cb-status-icon">⚠️</span>
            <div class="cb-status-content">
                <div class="cb-status-msg">${label} login required</div>
                <button class="cb-btn cb-btn-primary cb-status-action" id="cb-login-card-btn">
                    Login
                </button>
            </div>
        </div>`;
    } else {
        const model = _el("cb-model")?.value || modelsData?.default || label;
        html = `<div class="cb-status-card cb-status-ok">
            <span class="cb-status-icon">✅</span>
            <div class="cb-status-content">
                <div class="cb-status-msg">${_esc(model)} is ready</div>
            </div>
        </div>`;
    }

    box.innerHTML = html;
    _el("cb-install-btn")?.addEventListener("click", _triggerInstall);
    _el("cb-login-card-btn")?.addEventListener("click", _triggerLogin);
}

// ── Provider / Model UI ────────────────────────────────────────────────────────
async function _fetchStatusCached(provider) {
    const hit = _statusCache[provider];
    if (hit && Date.now() - hit.ts < STATUS_TTL_MS) return hit.data;
    const data = await fetch(`/comfybio/llm_status?provider=${encodeURIComponent(provider)}`).then(r => r.json());
    _statusCache[provider] = { data, ts: Date.now() };
    return data;
}

function _invalidateStatusCache(provider) {
    delete _statusCache[provider];
}

function _applyStatus(statusData) {
    const badge = _el("cb-provider-badge");
    if (!statusData.installed) {
        badge.textContent = "Not installed"; badge.className = "cb-badge cb-badge-error";
    } else if (!statusData.ready) {
        badge.textContent = "Not logged in"; badge.className = "cb-badge cb-badge-warning";
    } else {
        badge.textContent = "Ready"; badge.className = "cb-badge cb-badge-ok";
    }
}

async function _triggerLogin() {
    const btn = _el("cb-login-card-btn");
    if (btn) btn.disabled = true;
    try {
        const data = await fetch("/comfybio/llm_login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider: _state.provider }),
        }).then(r => r.json());

        if (data.login_url) {
            window.open(data.login_url, "_blank");
            let tries = 0;
            const poll = setInterval(async () => {
                tries++;
                _invalidateStatusCache(_state.provider);
                const s = await _fetchStatusCached(_state.provider);
                if (s.ready || tries > 40) {
                    clearInterval(poll);
                    _cachedStatus = s;
                    _applyStatus(s);
                    renderLLMLog(s, _cachedModels);
                }
            }, 3000);
        } else {
            setTimeout(() => {
                _invalidateStatusCache(_state.provider);
                refreshProvider(_state.provider);
            }, 4000);
        }
    } catch { }
    finally {
        const btn2 = _el("cb-login-card-btn");
        if (btn2) btn2.disabled = false;
    }
}

async function _triggerInstall() {
    const box = _el("cb-llm-log");
    const label = _capitalize(_state.provider);

    if (box) {
        box.innerHTML = `<div class="cb-status-card cb-status-warn">
            <span class="cb-status-icon">⏳</span>
            <div class="cb-status-content">
                <div class="cb-status-msg">Installing ${label} CLI…</div>
            </div>
        </div>`;
    }

    try {
        const data = await fetch("/comfybio/llm_install", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider: _state.provider }),
        }).then(r => r.json());

        if (data.status === "success") {
            _invalidateStatusCache(_state.provider);
            await refreshProvider(_state.provider);
        } else {
            if (box) {
                box.innerHTML = `<div class="cb-status-card cb-status-err">
                    <span class="cb-status-icon">❌</span>
                    <div class="cb-status-content">
                        <div class="cb-status-msg">Install failed: ${_esc(data.message || "Unknown error")}</div>
                        <button class="cb-btn cb-btn-secondary cb-status-action" id="cb-install-btn">
                            Retry
                        </button>
                    </div>
                </div>`;
                _el("cb-install-btn")?.addEventListener("click", _triggerInstall);
            }
        }
    } catch (err) {
        if (box) {
            box.innerHTML = `<div class="cb-status-card cb-status-err">
                <span class="cb-status-icon">❌</span>
                <div class="cb-status-content">
                    <div class="cb-status-msg">Install failed: ${_esc(err.message)}</div>
                    <button class="cb-btn cb-btn-secondary cb-status-action" id="cb-install-btn">
                        Retry
                    </button>
                </div>
            </div>`;
            _el("cb-install-btn")?.addEventListener("click", _triggerInstall);
        }
    }
}

function _populateModelDropdown(models, defaultModel) {
    const modelSel = _el("cb-model");
    modelSel.innerHTML = "";
    if (models.length === 0) {
        modelSel.innerHTML = '<option value="">(no models found)</option>';
        return;
    }
    for (const m of models) {
        const opt = document.createElement("option");
        opt.value = m; opt.textContent = m;
        if (m === defaultModel) opt.selected = true;
        modelSel.appendChild(opt);
    }
}

async function refreshProvider(provider) {
    const badge = _el("cb-provider-badge");
    badge.textContent = "…";
    badge.className = "cb-badge cb-badge-loading";

    // ① Models: hardcoded on server → instant response
    const modelsData = await fetch(`/comfybio/llm_models?provider=${encodeURIComponent(provider)}`).then(r => r.json());
    _state.models = modelsData.models ?? [];
    _state.model = modelsData.default ?? (_state.models[0] ?? "");
    _cachedModels = modelsData;
    _populateModelDropdown(_state.models, _state.model);

    // ② Status: subprocess call → async, badge shows spinner until done
    _fetchStatusCached(provider).then(statusData => {
        _cachedStatus = statusData;
        _applyStatus(statusData);
        renderLLMLog(statusData, modelsData);
    });
}

// ── File browser ───────────────────────────────────────────────────────────────
// ── File browser ───────────────────────────────────────────────────────────────
function _setBrowserTarget(target) {
    const prevTarget = _state.browserTarget;
    if (prevTarget) {
        _state.browserPathByTarget[prevTarget] = _state.browserPath || _state.browserPathByTarget[prevTarget] || "";
    }

    _state.browserTarget = target;
    document.querySelectorAll(".cb-io-target").forEach(btn =>
        btn.classList.toggle("active", btn.dataset.target === target));

    const inputEl = _el("cb-input-path");
    const outputEl = _el("cb-output-path");
    const inputErr = _el("cb-input-error");
    const outputErr = _el("cb-output-error");
    const label = _el("cb-io-selected-label");
    const pathInput = _el("cb-io-current-path-display");

    inputErr.style.display = target === "input" ? "" : "none";
    outputErr.style.display = target === "output" ? "" : "none";
    label.textContent = target === "input" ? "Selected Input Path" : "Selected Output Directory";

    const currentValue = target === "input" ? inputEl.value.trim() : outputEl.value.trim();
    const rememberedPath = _state.browserPathByTarget[target] || "";
    const startPath = target === "output"
        ? (rememberedPath || currentValue || _state.quickPaths[target] || _state.browserPath || "")
        : (currentValue || rememberedPath || _state.quickPaths[target] || _state.browserPath || "");

    _el("cb-selected-path-val").textContent = currentValue || "Not selected";
    if (pathInput) pathInput.value = startPath;

    _loadBrowser(startPath, target);
}

async function _loadBrowser(path, targetOverride = _state.browserTarget) {
    const list = _el("cb-browser-list");
    if (list) list.innerHTML = '<div class="cb-ib-loading">Loading...</div>';
    try {
        const data = await _browsePath(path);
        if (data.status !== "success") {
            if (_state.browserTarget === targetOverride) {
                _updateCurrentPathDisplay(path || "");
            }
            if (list) list.innerHTML = `<div class="cb-ib-empty">${_esc(data.error || "Unable to browse path")}</div>`;
            return;
        }
        _state.browserPathByTarget[targetOverride] = data.path;
        if (_state.browserTarget === targetOverride) {
            _state.browserPath = data.path;
            _updateCurrentPathDisplay(data.path);
            _renderBrowserEntries(data);
        }
    } catch (err) {
        if (list) list.innerHTML = `<div class="cb-ib-empty">Browse failed: ${_esc(err.message)}</div>`;
    }
}

function _updateCurrentPathDisplay(path) {
    const display = _el("cb-io-current-path-display");
    if (display) {
        display.value = path || "";
        display.title = path || "";
    }
}

function _renderBrowserEntries(data) {
    const list = _el("cb-browser-list");
    const entries = data.entries || [];
    const parentRow = data.parent
        ? `<div class="cb-browser-row cb-browser-parent" data-action="open" data-path="${_esc(data.parent)}">
             <span class="cb-browser-icon">⬆️</span>
             <span class="cb-browser-name" title="Up to parent folder">.. (Parent)</span>
           </div>`
        : "";

    if (!entries.length && !parentRow) {
        list.innerHTML = '<div class="cb-ib-empty">No readable entries</div>';
        return;
    }

    list.innerHTML = parentRow + entries.map(entry => {
        // Advanced domain-specific file icons
        let icon = "📄";
        if (entry.kind === "dir") {
            icon = "📁";
        } else if (entry.kind === "blocked") {
            icon = "🚫";
        } else {
            const ext = (entry.name || "").split(".").pop().toLowerCase();
            if (["fasta", "fa", "fna", "faa"].includes(ext)) {
                icon = "🧬"; // FASTA dna helix
            } else if (["gb", "gbk", "genbank"].includes(ext)) {
                icon = "🏷️"; // Genbank annotations
            } else if (["fastq", "fq"].includes(ext)) {
                icon = "📊"; // Quality control sequencing data
            } else if (ext === "xml") {
                icon = "🕸️"; // Blast XML / structure
            } else if (["json", "txt"].includes(ext)) {
                icon = "📝";
            }
        }

        const action = entry.kind === "dir" ? "open" : entry.kind === "file" ? "select-file" : "blocked";
        const meta = entry.kind === "file" ? _fmtSize(entry.size) : entry.kind === "dir" ? "Folder" : entry.kind;
        const currentTargetVal = _state.browserTarget === "input" ? _el("cb-input-path").value : _el("cb-output-path").value;
        const isActive = currentTargetVal === entry.path ? "active" : "";

        return `<div class="cb-browser-row ${isActive}" data-action="${action}" data-path="${_esc(entry.path)}" data-kind="${_esc(entry.kind)}">
            <span class="cb-browser-icon">${icon}</span>
            <span class="cb-browser-name" title="${_esc(entry.name)}">${_esc(entry.name)}</span>
            <span class="cb-browser-meta">${_esc(meta)}</span>
        </div>`;
    }).join("");

    list.querySelectorAll(".cb-browser-row").forEach(row =>
        row.addEventListener("click", () => _handleBrowserRow(row)));
}

function _handleBrowserRow(row) {
    const action = row.dataset.action;
    const path = row.dataset.path;
    if (action === "open") { _loadBrowser(path); return; }
    if (action === "select-file" && _state.browserTarget === "input") {
        _selectBrowserPath(path);

        // Visual active state update in list
        document.querySelectorAll(".cb-browser-row").forEach(r => r.classList.remove("active"));
        row.classList.add("active");
    }
}

function _selectBrowserPath(path) {
    if (_state.browserTarget === "input") {
        _el("cb-input-path").value = path;
        _el("cb-input-error").textContent = "";
    } else {
        _el("cb-output-path").value = path;
        _el("cb-output-error").textContent = "";
    }
    _el("cb-selected-path-val").textContent = path;
}

// ── Effective path helpers ─────────────────────────────────────────────────────
function getEffectiveInputPath() {
    return _el("cb-input-path")?.value.trim() ?? "";
}

function getEffectiveOutputDir() {
    return _el("cb-output-path")?.value.trim() || "./output";
}

// ── PROMPT tab log ─────────────────────────────────────────────────────────────
function _appendPromptLine(level, msg) {
    _promptLines.push({ ts: _now(), level, msg });
    _renderPromptLog();
}

function _renderPromptLog() {
    const box = _el("cb-prompt-log");
    if (!box) return;
    const l = _promptLines[_promptLines.length - 1];
    if (!l) { box.innerHTML = ""; return; }
    const cls = level2cls(l.level);
    box.innerHTML = `<div class="cb-pl ${cls}">` +
        `<span class="cb-pl-ts">${l.ts}</span>` +
        `<span class="cb-pl-lv">${l.level}</span>` +
        `<span class="cb-pl-msg">${_esc(l.msg)}</span>` +
        `</div>`;
}

function showPromptLog() {
    const box = _el("cb-prompt-log");
    if (box) box.hidden = false;
}

function level2cls(level) {
    if (level === "ERROR") return "cb-pl-error";
    if (level === "WARN") return "cb-pl-warn";
    return "cb-pl-info";
}

function clearPromptLog() {
    _promptLines = [];
    _renderPromptLog();
}

// ── Generate ───────────────────────────────────────────────────────────────────
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

// ── CSS ────────────────────────────────────────────────────────────────────────
const PANEL_CSS = `
#cb-panel {
    position: fixed; top: 60px; right: 20px;
    width: 360px; max-height: calc(100vh - 80px);
    background: rgba(13, 13, 20, 0.94);
    backdrop-filter: blur(20px) saturate(190%);
    -webkit-backdrop-filter: blur(20px) saturate(190%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.65);
    color: #f3f4f6;
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    font-size: 12px; z-index: 10000;
    display: flex; flex-direction: column; overflow-x: hidden; overflow-y: auto;
    transition: opacity 0.25s ease, transform 0.25s ease;
    transform-origin: top right;
}
#cb-panel.cb-hidden { transform: scale(0.94); opacity: 0; pointer-events: none; }

/* header */
.cb-header {
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.12));
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
    cursor: grab; user-select: none;
}
.cb-header:active { cursor: grabbing; }
.cb-header-title {
    margin: 0; font-size: 13px; font-weight: 700;
    background: linear-gradient(90deg, #10b981, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.01em;
}
.cb-dna-btn {
    cursor: pointer; font-size: 18px; flex-shrink: 0;
    border: none; background: transparent; padding: 2px 4px; line-height: 1;
    border-radius: 6px; transition: background 0.15s, transform 0.15s;
}
.cb-dna-btn:hover { background: rgba(255,255,255,0.08); transform: scale(1.12); }
.cb-dna-btn:active { transform: scale(0.9); }

/* body layout */
.cb-body { display: flex; flex: 0 0 auto; overflow: visible; }
.cb-tabs {
    display: flex; flex-direction: column;
    width: 52px; flex-shrink: 0;
    background: rgba(0, 0, 0, 0.3);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    padding: 12px 0; gap: 4px; align-items: center;
}
.cb-tab-btn {
    width: 42px; padding: 10px 4px;
    display: flex; align-items: center; justify-content: center;
    border: none; background: transparent; border-radius: 8px; cursor: pointer;
    font-size: 9px; font-weight: 700; letter-spacing: 0.05em; color: #6b7280;
    text-transform: uppercase; line-height: 1; position: relative;
    transition: background 0.15s, color 0.15s;
}
.cb-tab-btn:hover { background: rgba(255, 255, 255, 0.06); color: #d1d5db; }
.cb-tab-btn.active { background: rgba(16, 185, 129, 0.18); color: #34d399; }
.cb-tab-btn.active::before {
    content: ''; position: absolute; left: -1px; top: 50%; transform: translateY(-50%);
    width: 3px; height: 50%; border-radius: 0 3px 3px 0; background: #10b981;
}
.cb-right { flex: 1; display: flex; flex-direction: column; overflow: visible; min-width: 0; }
.cb-content { flex: 0 0 auto; overflow: visible; padding: 14px; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.cb-tab-pane { flex-direction: column; gap: 11px; }
.cb-pane-title {
    font-size: 10px; font-weight: 800; color: #10b981;
    text-transform: uppercase; letter-spacing: 0.08em;
    padding-bottom: 6px; border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

/* form */
label { font-size: 10px; font-weight: 700; color: #9ca3af; display: block; margin-bottom: 4px; }
select, input[type="text"], textarea {
    background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 8px; padding: 6px 9px; color: #f3f4f6; font-size: 11px;
    outline: none; width: 100%; box-sizing: border-box;
    transition: border-color 0.15s, box-shadow 0.15s;
}
select:focus, input[type="text"]:focus, textarea:focus { 
    border-color: #10b981; 
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15);
}
textarea { resize: vertical; min-height: 100px; font-family: inherit; }

/* badges */
.cb-badge {
    display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 10px; font-weight: 600; white-space: nowrap; flex-shrink: 0;
}
.cb-badge-ok      { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.25); }
.cb-badge-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.25); }
.cb-badge-error   { background: rgba(239, 68, 68, 0.15);  color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); }
.cb-badge-loading { background: rgba(6, 182, 212, 0.12); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.22); }

/* buttons */
.cb-btn {
    border: none; border-radius: 8px; cursor: pointer;
    font-size: 11px; font-weight: 600; padding: 6px 12px;
    transition: opacity 0.15s, transform 0.1s, background 0.15s; white-space: nowrap;
}
.cb-btn:active { transform: scale(0.97); }
.cb-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.cb-btn-primary { background: linear-gradient(135deg, #10b981, #059669); color: #fff; }
.cb-btn-primary:hover:not(:disabled) { opacity: 0.9; }
.cb-btn-secondary { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); color: #d1d5db; }
.cb-btn-secondary:hover:not(:disabled) { background: rgba(255, 255, 255, 0.1); }
.cb-btn-generate {
    background: linear-gradient(135deg, #10b981, #06b6d4);
    color: #fff; width: 100%; padding: 10px; font-size: 12px; font-weight: 700;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}
.cb-btn-generate:hover:not(:disabled) { opacity: 0.95; }

/* toggle */
.cb-row { display: flex; align-items: center; gap: 8px; }
.cb-toggle {
    flex: 1; padding: 5px; border: 1px solid rgba(255, 255, 255, 0.08);
    background: transparent; color: #9ca3af; cursor: pointer;
    font-size: 10px; font-weight: 600; transition: background 0.15s, color 0.15s;
}
.cb-toggle:first-child { border-radius: 6px 0 0 6px; }
.cb-toggle:last-child  { border-radius: 0 6px 6px 0; border-left: none; }
.cb-toggle.active { background: rgba(16, 185, 129, 0.18); color: #34d399; border-color: rgba(16, 185, 129, 0.3); }
.cb-file-name { font-size: 10px; color: #9ca3af; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.cb-auth-msg  { font-size: 10px; color: #fbbf24; flex: 1; line-height: 1.4; }

/* ── LLM tab log ── */
#cb-llm-log { margin-top: 4px; }

.cb-status-card {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 12px; border-radius: 8px;
    border: 1px solid transparent;
}
.cb-status-ok   { background: rgba(16, 185, 129, 0.08);  border-color: rgba(16, 185, 129, 0.2); }
.cb-status-warn { background: rgba(245, 158, 11, 0.08);  border-color: rgba(245, 158, 11, 0.2); }
.cb-status-err  { background: rgba(239, 68, 68, 0.08);   border-color: rgba(239, 68, 68, 0.2); }
.cb-status-icon    { font-size: 15px; flex-shrink: 0; line-height: 1.5; }
.cb-status-content { display: flex; flex-direction: column; gap: 7px; flex: 1; min-width: 0; }
.cb-status-msg     { font-size: 11px; font-weight: 600; line-height: 1.4; }
.cb-status-ok   .cb-status-msg { color: #34d399; }
.cb-status-warn .cb-status-msg { color: #fbbf24; }
.cb-status-err  .cb-status-msg { color: #f87171; }
.cb-status-action  { align-self: flex-start; font-size: 10px; padding: 4px 10px; }

/* ── PROMPT tab log ── */
#cb-prompt-log {
    min-height: 120px; max-height: 260px; overflow-y: auto;
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px; padding: 10px;
    display: flex; flex-direction: column; gap: 4px;
    font-family: "SF Mono", "Consolas", monospace; font-size: 10px;
}
#cb-prompt-log[hidden] { display: none; }
.cb-pl { display: flex; gap: 6px; line-height: 1.5; word-break: break-all; }
.cb-pl-ts  { color: #52525b; flex-shrink: 0; }
.cb-pl-lv  { font-weight: 700; flex-shrink: 0; width: 36px; }
.cb-pl-msg { color: #e4e4e7; flex: 1; }
.cb-pl-info  .cb-pl-lv { color: #3b82f6; }
.cb-pl-warn  .cb-pl-lv { color: #f59e0b; }
.cb-pl-warn  .cb-pl-msg { color: #fbbf24; }
.cb-pl-error .cb-pl-lv { color: #ef4444; }
.cb-pl-error .cb-pl-msg { color: #f87171; }

/* toggler */
#cb-toggler {
    position: fixed; top: 60px; right: 20px;
    background: linear-gradient(135deg, #10b981, #06b6d4);
    border: none; border-radius: 50%; width: 42px; height: 42px;
    color: white; font-size: 18px; cursor: grab;
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
    z-index: 9999; display: flex; align-items: center; justify-content: center;
    transition: transform 0.2s, box-shadow 0.2s;
    user-select: none;
}
#cb-toggler:hover { transform: scale(1.08); box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45); }
#cb-toggler:active { cursor: grabbing; transform: scale(1.0); }

/* resize handles */
.cb-resize-handle { position: absolute; z-index: 20; }
.cb-resize-n  { top: 0;    left: 12px; right: 12px; height: 6px; cursor: ns-resize; }
.cb-resize-s  { bottom: 0; left: 12px; right: 12px; height: 6px; cursor: ns-resize; }
.cb-resize-e  { top: 12px; right: 0; bottom: 12px; width: 6px;  cursor: ew-resize; }
.cb-resize-w  { top: 12px; left: 0;  bottom: 12px; width: 6px;  cursor: ew-resize; }
.cb-resize-nw { top: 0; left: 0;   width: 14px; height: 14px; cursor: nwse-resize; z-index: 21; }
.cb-resize-ne { top: 0; right: 0;  width: 14px; height: 14px; cursor: nesw-resize; z-index: 21; }
.cb-resize-se { bottom: 0; right: 0; width: 14px; height: 14px; cursor: nwse-resize; z-index: 21; }
.cb-resize-sw { bottom: 0; left: 0;  width: 14px; height: 14px; cursor: nesw-resize; z-index: 21; }

/* ── Simple I/O File Browser Redesign ── */
.cb-io-target-selector {
    display: flex;
    gap: 4px;
}
.cb-target-btn {
    flex: 1;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 6px;
    color: #9ca3af;
    cursor: pointer;
    font-weight: 700;
    font-size: 10px;
    transition: all 0.15s;
}
.cb-target-btn.active {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.35);
}

.cb-io-path-row {
    display: flex;
    gap: 6px;
    align-items: center;
}

.cb-browser-list {
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    height: 220px;
    max-height: 220px;
    overflow-y: auto;
    background: rgba(0, 0, 0, 0.35);
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(76px, 1fr));
    gap: 8px;
    padding: 10px;
    align-content: start;
}

.cb-browser-row {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 10px 4px 6px 4px;
    border-radius: 8px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, transform 0.12s;
    min-width: 0;
    text-align: center;
}
.cb-browser-row:hover {
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.15);
    transform: translateY(-2px);
}
.cb-browser-row.active {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.35);
}
.cb-browser-name {
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #e4e4e7;
    font-weight: 500;
    font-size: 10px;
    margin-top: 4px;
}
.cb-browser-icon {
    font-size: 26px;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 32px;
}
.cb-browser-meta {
    display: none; /* Hide size meta to keep visual explorer simple and clean */
}

.cb-io-error {
    font-size: 10px;
    color: #f87171;
    margin-top: 4px;
    min-height: 14px;
}

.cb-io-selected-summary {
    background: rgba(16, 185, 129, 0.04);
    border: 1px solid rgba(16, 185, 129, 0.12);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 11px;
}
.cb-selected-path-val {
    font-family: monospace;
    color: #34d399;
    word-break: break-all;
    font-size: 10px;
    margin-top: 2px;
}

    border-radius: 6px;
    max-height: 150px;
    overflow-y: auto;
}
.cb-ib-item {
    padding: 6px 9px; font-size: 10px; color: #d1d5db; cursor: pointer;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    transition: background 0.12s;
}
.cb-ib-item:hover { background: rgba(99,102,241,0.22); color: #e2e8f0; }
.cb-ib-loading, .cb-ib-empty {
    padding: 10px; font-size: 10px; color: #6b7280; text-align: center;
}
`;

// ── HTML ───────────────────────────────────────────────────────────────────────
const PANEL_HTML = `
<div class="cb-header">
  <button class="cb-dna-btn" id="cb-dna-btn" title="Minimize">🧬</button>
  <span class="cb-header-title">ComfyBIO Biopython</span>
</div>
<div class="cb-body">

  <div class="cb-tabs">
    <button class="cb-tab-btn active" data-tab="llm"    title="LLM Provider">LLM</button>
    <button class="cb-tab-btn"        data-tab="io"     title="Input / Output">I/O</button>
    <button class="cb-tab-btn"        data-tab="prompt" title="Prompt">PROMPT</button>
  </div>

  <div class="cb-right">
    <div class="cb-content">

      <!-- ── LLM tab ── -->
      <div class="cb-tab-pane" data-pane="llm" style="display:flex">
        <div class="cb-pane-title">LLM</div>

        <div>
          <label>LLM</label>
          <div class="cb-row">
            <select id="cb-provider" style="flex:1">
              <option value="claude">Claude</option>
              <option value="codex">Codex</option>
              <option value="gemini">Gemini</option>
              <option value="deterministic">Deterministic (Test)</option>
            </select>
            <span id="cb-provider-badge" class="cb-badge cb-badge-loading">…</span>
          </div>
        </div>

        <div>
          <label>Model</label>
          <select id="cb-model"><option value="">Loading…</option></select>
        </div>

        <!-- LLM status log -->
        <div id="cb-llm-log"></div>
      </div>

      <!-- ── I/O tab ── -->
      <div class="cb-tab-pane" data-pane="io" style="display:none">
        <div class="cb-pane-title">Input / Output</div>

        <!-- Target Switcher -->
        <div class="cb-io-target-selector">
          <button class="cb-target-btn active cb-io-target" id="cb-io-target-input" data-target="input">Input</button>
          <button class="cb-target-btn cb-io-target" id="cb-io-target-output" data-target="output">Output</button>
        </div>

        <!-- Path Bar & Up button -->
        <div class="cb-io-path-row">
          <input type="text" id="cb-io-current-path-display" style="flex: 1; font-family: monospace; font-size: 10px;" placeholder="Type a path, then press Enter or Up">
          <button class="cb-btn cb-btn-secondary" id="cb-browser-up" style="padding: 6px 10px;">Up</button>
        </div>

        <!-- Browser List -->
        <div id="cb-browser-list" class="cb-browser-list">
          <div class="cb-ib-loading">Loading files...</div>
        </div>

        <!-- Current Selection -->
        <div class="cb-io-selected-summary">
          <label id="cb-io-selected-label">Selected Input Path</label>
          <div id="cb-selected-path-val" class="cb-selected-path-val">Not selected</div>
          
          <!-- Hidden fields for compatibility -->
          <input type="text" id="cb-input-path" style="display:none">
          <input type="text" id="cb-output-path" style="display:none">
          
          <div class="cb-io-error" id="cb-input-error"></div>
          <div class="cb-io-error" id="cb-output-error" style="display:none"></div>
        </div>

        <button class="cb-btn cb-btn-primary" id="cb-browser-select-current" style="width: 100%;">Apply Current Directory</button>
      </div>

      <!-- ── PROMPT tab ── -->
      <div class="cb-tab-pane" data-pane="prompt" style="display:none">
        <div class="cb-pane-title">Workflow Goal</div>
        <textarea id="cb-query"
          placeholder="e.g. Parse a FASTA file and calculate GC content for each sequence&#10;&#10;Ctrl+Enter to generate"></textarea>
        <button class="cb-btn cb-btn-generate" id="cb-generate-btn">⚡ Generate Workflow</button>
        <!-- Execution log -->
        <div id="cb-prompt-log" hidden></div>
      </div>

    </div>
  </div>

</div>
`;

// ── Drag & Resize ─────────────────────────────────────────────────────────────
function _makeDraggable(el, handle, skipSelector) {
    el._dragging = false;

    handle.addEventListener("mousedown", (e) => {
        if (e.button !== 0) return;
        if (skipSelector && e.target.closest(skipSelector)) return;
        e.preventDefault();
        el._dragging = false;

        const rect = el.getBoundingClientRect();
        const startX = e.clientX;
        const startY = e.clientY;
        const origLeft = rect.left;
        const origTop  = rect.top;

        const onMove = (e) => {
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            if (!el._dragging && Math.abs(dx) < 4 && Math.abs(dy) < 4) return;
            el._dragging = true;
            document.body.style.userSelect = "none";

            const w = el.offsetWidth;
            const h = el.offsetHeight;
            const left = Math.max(0, Math.min(window.innerWidth  - w, origLeft + dx));
            const top  = Math.max(0, Math.min(window.innerHeight - h, origTop  + dy));

            el.style.left   = left + "px";
            el.style.top    = top  + "px";
            el.style.right  = "auto";
            el.style.bottom = "auto";
        };

        const onUp = () => {
            document.body.style.userSelect = "";
            document.removeEventListener("mousemove", onMove);
            document.removeEventListener("mouseup",   onUp);
            // Reset after click event fires so same-element click suppression still works
            setTimeout(() => { el._dragging = false; }, 0);
        };

        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup",   onUp);
    });
}

function _makeResizable(el) {
    const handles = [
        { cls: "cb-resize-n",  dirs: ["n"]      },
        { cls: "cb-resize-ne", dirs: ["n", "e"] },
        { cls: "cb-resize-e",  dirs: ["e"]      },
        { cls: "cb-resize-se", dirs: ["s", "e"] },
        { cls: "cb-resize-s",  dirs: ["s"]      },
        { cls: "cb-resize-sw", dirs: ["s", "w"] },
        { cls: "cb-resize-w",  dirs: ["w"]      },
        { cls: "cb-resize-nw", dirs: ["n", "w"] },
    ];

    handles.forEach(({ cls, dirs }) => {
        const h = document.createElement("div");
        h.className = "cb-resize-handle " + cls;
        el.appendChild(h);

        h.addEventListener("mousedown", (e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            e.stopPropagation();

            const startX    = e.clientX;
            const startY    = e.clientY;
            const startW    = el.offsetWidth;
            const startH    = el.offsetHeight;
            const rect      = el.getBoundingClientRect();
            const startLeft = rect.left;
            const startTop  = rect.top;

            const onMove = (e) => {
                document.body.style.userSelect = "none";
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;

                if (dirs.includes("e")) {
                    el.style.width = Math.max(280, startW + dx) + "px";
                }
                if (dirs.includes("w")) {
                    const newW = Math.max(280, startW - dx);
                    el.style.width = newW + "px";
                    el.style.left  = (startLeft + startW - newW) + "px";
                    el.style.right = "auto";
                }
                if (dirs.includes("s")) {
                    el.style.maxHeight = "none";
                    el.style.height    = Math.max(200, startH + dy) + "px";
                }
                if (dirs.includes("n")) {
                    const newH = Math.max(200, startH - dy);
                    el.style.maxHeight = "none";
                    el.style.height    = newH + "px";
                    el.style.top       = (startTop + startH - newH) + "px";
                    el.style.bottom    = "auto";
                }
            };

            const onUp = () => {
                document.body.style.userSelect = "";
                document.removeEventListener("mousemove", onMove);
                document.removeEventListener("mouseup",   onUp);
            };

            document.addEventListener("mousemove", onMove);
            document.addEventListener("mouseup",   onUp);
        });
    });
}

// ── Extension ──────────────────────────────────────────────────────────────────
app.registerExtension({
    name: "ComfyBIO.Panel",

    async setup() {
        const style = document.createElement("style");
        style.textContent = PANEL_CSS;
        document.head.appendChild(style);

        const panel = document.createElement("div");
        panel.id = "cb-panel";
        panel.className = "cb-hidden";
        panel.innerHTML = PANEL_HTML;
        document.body.appendChild(panel);

        const toggler = document.createElement("button");
        toggler.id = "cb-toggler";
        toggler.innerHTML = "🧬";
        toggler.title = "Open ComfyBIO panel";
        document.body.appendChild(toggler);

        // ── Drag & Resize setup ───────────────────────────────────────────────
        _makeDraggable(panel, panel.querySelector(".cb-header"), ".cb-dna-btn");
        _makeResizable(panel);
        _makeDraggable(toggler, toggler);

        // ── Panel toggle ──────────────────────────────────────────────────────
        toggler.addEventListener("click", () => {
            if (toggler._dragging) return;
            const tr  = toggler.getBoundingClientRect();
            const tcx = tr.left + tr.width  / 2;   // toggler center X
            const tcy = tr.top  + tr.height / 2;   // toggler center Y
            const panelW = panel.offsetWidth || 360;

            // Measure DNA button's offset relative to panel while panel is still in DOM.
            // Temporarily unhide (off-screen) to get accurate layout values.
            panel.style.visibility = "hidden";
            panel.style.left = "0px";
            panel.style.top  = "0px";
            panel.style.right = "auto";
            panel.classList.remove("cb-hidden");

            const dr  = _el("cb-dna-btn").getBoundingClientRect();
            const pr  = panel.getBoundingClientRect();
            const dnaRelX = dr.left - pr.left + dr.width  / 2;  // DNA center X from panel left
            const dnaRelY = dr.top  - pr.top  + dr.height / 2;  // DNA center Y from panel top

            panel.classList.add("cb-hidden");
            panel.style.visibility = "";

            // Place panel so its DNA center lands on toggler center
            let left = tcx - dnaRelX;
            let top  = tcy - dnaRelY;
            left = Math.max(8, Math.min(window.innerWidth  - panelW - 8, left));
            top  = Math.max(8, Math.min(window.innerHeight - 200,        top));

            panel.style.left = left + "px";
            panel.style.top  = top  + "px";
            panel.classList.remove("cb-hidden");
            toggler.style.display = "none";
        });
        function _collapsePanel() {
            const dr  = _el("cb-dna-btn").getBoundingClientRect();
            const dcx = dr.left + dr.width  / 2;
            const dcy = dr.top  + dr.height / 2;
            const tw  = toggler.offsetWidth  || 42;
            const th  = toggler.offsetHeight || 42;
            let tLeft = Math.round(dcx - tw / 2);
            let tTop  = Math.round(dcy - th / 2);
            tLeft = Math.max(0, Math.min(window.innerWidth  - tw, tLeft));
            tTop  = Math.max(0, Math.min(window.innerHeight - th, tTop));
            toggler.style.left   = tLeft + "px";
            toggler.style.top    = tTop  + "px";
            toggler.style.right  = "auto";
            toggler.style.bottom = "auto";
            panel.classList.add("cb-hidden");
            toggler.style.display = "";
        }

        _el("cb-dna-btn").addEventListener("click", _collapsePanel);

        panel.querySelector(".cb-header").addEventListener("click", (e) => {
            if (panel._dragging) return;
            if (e.target.closest(".cb-dna-btn")) return;
            _collapsePanel();
        });

        // ── Tab buttons ───────────────────────────────────────────────────────
        document.querySelectorAll(".cb-tab-btn").forEach(btn =>
            btn.addEventListener("click", () => switchTab(btn.dataset.tab)));

        // ── Provider / model ──────────────────────────────────────────────────
        _el("cb-provider").addEventListener("change", e => {
            _state.provider = e.target.value;
            refreshProvider(_state.provider);
        });
        _el("cb-model").addEventListener("change", e => {
            _state.model = e.target.value;
            if (_cachedStatus) renderLLMLog(_cachedStatus, _cachedModels);
        });

        // ── I/O Browser controls ──────────────────────────────────────────────
        document.querySelectorAll(".cb-io-target").forEach(btn =>
            btn.addEventListener("click", () => _setBrowserTarget(btn.dataset.target)));

        _el("cb-browser-up").addEventListener("click", async () => {
            const pathInput = _el("cb-io-current-path-display");
            const typedPath = pathInput?.value.trim() || "";
            if (typedPath && typedPath !== _state.browserPath) {
                _loadBrowser(typedPath);
                return;
            }
            const data = await _browsePath(_state.browserPath);
            if (data.parent) _loadBrowser(data.parent);
        });

        _el("cb-browser-select-current").addEventListener("click", () =>
            _selectBrowserPath(_state.browserPath));

        // ── Path input navigation ─────────────────────────────────────────────
        const pathInput = _el("cb-io-current-path-display");
        if (pathInput) {
            pathInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const typedPath = pathInput.value.trim();
                    if (typedPath) _loadBrowser(typedPath);
                }
            });
        }

        // ── Generate ──────────────────────────────────────────────────────────
        _el("cb-generate-btn").addEventListener("click", triggerGeneration);
        _el("cb-query").addEventListener("keydown", e => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                triggerGeneration();
            }
        });



        // ── Init ──────────────────────────────────────────────────────────────
        fetch("/comfybio/default_paths").then(r => r.json()).then(data => {
            _state.inputPath = data.input_dir || "";
            _state.outputDir = data.output_dir || "./output";
            _state.quickPaths.input = _state.inputPath;
            _state.quickPaths.output = _state.outputDir;
            _state.quickPaths.home = data.home_dir || _state.inputPath || "/";
            _state.browserPathByTarget.input = _state.inputPath || "";
            _state.browserPathByTarget.output = _state.outputDir || "";

            const elOutput = _el("cb-output-path");
            if (elOutput) elOutput.value = _state.outputDir;
            _state.browserPath = _state.inputPath;
            _loadBrowser(_state.inputPath);
        }).catch(() => {
            _loadBrowser("");
        });

        refreshProvider(_state.provider);
    },
});
