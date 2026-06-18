# UI Style Cleanup Design — 2026-06-18

## Goal

간결하고 깔끔한 UI. 색상/스타일 통일, border-radius 완화, 중복 판 제목 제거.

## Changes

### 1. Accent color unification (`comfybio.css`)

| Variable | Before | After |
|---|---|---|
| `:root --cb-accent` | `#3b82f6` (blue) | `#10b981` (emerald) |
| `:root --cb-accent-2` | `#60a5fa` (blue) | `#34d399` (emerald-light) |
| `.cb-theme-light --cb-accent` | `#0f52ba` (blue) | `#059669` (emerald-dark) |
| `.cb-theme-light --cb-accent-2` | `#1e68d7` (blue) | `#10b981` (emerald) |

Hardcoded `rgba(16, 185, 129, ...)` values throughout the file already match emerald — no changes needed there.

### 2. Border-radius reduction (`comfybio.css`)

`--cb-radius: 14px` → `8px`

14px is excessive for small elements (badges, tab buttons, status cards). 8px gives a cleaner "data tool" aesthetic appropriate for bioinformatics tooling.

### 3. Tab button font-size (`comfybio.css`)

`.cb-tab-btn font-size: 9px` → `10px`

9px renders inconsistently across displays. 1px increase improves legibility without layout impact.

### 4. Remove redundant pane titles (`comfybio_test_load.js`)

Remove `<div class="cb-pane-title">` from PANEL_HTML in all three tabs:
- LLM tab
- I/O tab  
- PROMPT tab

Remove `.cb-pane-title` CSS rule from `comfybio.css` (no longer referenced).

Frees ~22px vertical space per tab and eliminates redundancy with the sidebar tab labels.

## Files Changed

- `llm_interface/llm_web/web/comfybio.css` — CSS variables + radius + font-size + remove .cb-pane-title rule
- `llm_interface/llm_web/web/comfybio_test_load.js` — remove 3 pane title divs from PANEL_HTML

## Non-changes

- No layout restructuring
- No functional changes
- No JavaScript logic changes
- Light theme green values already aligned with dark theme emerald palette
