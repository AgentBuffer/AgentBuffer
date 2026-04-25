# QA Audit Report — `chore/audit-and-fix`

**Date:** 2026-04-25
**Branch:** `chore/audit-and-fix`
**Auditor:** Devin (Senior QA & DevOps)

---

## 1. Static Analysis Findings

### 1.1 Ruff Lint (`ruff check services/ gateway/`)

| Rule | Count | Severity | Description |
|------|-------|----------|-------------|
| E501 | 22 | Warning | Line too long (>100 chars) |
| I001 | 4 | Auto-fixable | Unsorted / un-formatted import blocks |
| F401 | 3 | Auto-fixable | Unused imports (`asyncio` x2, `typing.Any` x1) |
| F841 | 1 | Warning | Unused local variable (`brand` in `head_agent/agent.py`) |
| **Total** | **30** | | |

**Affected files (E501):** `critic/agent.py`, `head_agent/agent.py`, `strategist/agent.py`, `publisher/agent.py`, `video_creator/agent.py`

### 1.2 Ruff Format (`ruff format --check services/ gateway/`)

9 files would be reformatted:
- `services/critic/agent.py`
- `services/head_agent/agent.py`
- `services/publisher/agent.py`
- `services/shared/models.py`
- `services/strategist/agent.py`
- `services/video_creator/agent.py`
- `services/video_creator/tests/test_trends.py`
- `services/video_creator/tests/test_veo_client.py`
- `services/video_creator/veo_client.py`

### 1.3 Mypy Type Checking (`mypy --explicit-package-bases --ignore-missing-imports`)

| File | Error | Category |
|------|-------|----------|
| `design_specialists/common/text_layout.py:13` | `load_font` return type mismatch (`FreeTypeFont \| ImageFont` vs `FreeTypeFont`) | return-value |
| `design_specialists/common/text_layout.py:52-53` | `float` assigned to `int` variable in `measure_text_block` | assignment |
| `carousel_creator/renderer.py:44` | Same `load_font` return type issue | return-value |
| `carousel_creator/renderer.py:56` | `Image.LANCZOS` attribute not found (Pillow stubs) | attr-defined |
| `design_specialists/common/canvas.py:24` | `Image.LANCZOS` attribute not found | attr-defined |
| `design_specialists/layout_specialist.py:85` | `Image.LANCZOS` attribute not found | attr-defined |
| `design_specialists/layout_specialist.py:100,137,144` | `float` assigned to `int` variable | assignment |
| `video_creator/veo_client.py:217` | `write()` arg type: `int` vs `Buffer` | arg-type |
| `video_creator/tests/test_veo_client.py:210,235,273,293,310` | Nullable field access without None-guard | union-attr, operator |
| `publisher/agent.py:76` | Missing type stubs for `requests` | import-untyped |

**Total mypy errors:** 22 (across 7 files)

---

## 2. Bug & Code Smell Inventory

### 2.1 Deprecated API Usage
- **`services/video_creator/agent.py:115,161`** — Uses Pydantic v1 `.dict()` instead of `.model_dump()`. Will emit deprecation warnings and may break on Pydantic v3.

### 2.2 Missing Error Handling
- **`services/head_agent/analysis.py`** — `extract_brand_kit()` and `generate_marketing_analysis()` do not catch `json.JSONDecodeError` from malformed LLM responses. A non-JSON response will crash the pipeline.
- **`services/strategist/agent.py`** — `generate_slate()` same issue.
- **`services/critic/agent.py`** — `critique_slate()` same issue.

### 2.3 Dead / Redundant Code
- **`services/design_director/planner.py:75`** — `execution_order` always set to `"sequential"` regardless of step count.
- **`services/design_director/main.py:36`** — `if request.task_type is None` can never be `True` since `DesignRequest.task_type` is a required `DesignTaskType` enum field.
- **`services/shared/envelope.py`** — Entire module is a placeholder (1-line docstring, no implementation).

### 2.4 Unused Variables / Imports
- `head_agent/agent.py` — Local variable `brand` assigned but never used (in one handler).
- `publisher/agent.py` — `asyncio` imported but unused.
- `strategist/agent.py` — `asyncio` imported but unused.
- `video_creator/tests/test_veo_client.py` — `typing.Any` imported but unused.

---

## 3. Test Coverage Baseline

**Existing tests:** 63 passing, 0 failing.

| Service | Test Files | Test Count | Coverage Gaps |
|---------|-----------|------------|---------------|
| `carousel_creator` | `test_pagination.py`, `test_renderer.py` | 13 | No agent-level integration test |
| `video_creator` | `test_veo_client.py`, `test_trends.py` | 30 | No test for `process_approved_slate` or `wrap_results_as_envelope` |
| `design_director` | `test_director.py` | 9 | No test for `handle_request` / `_execute_step` in `main.py` |
| `design_specialists` | `test_layout_specialist.py`, `test_e2e_flow.py` | 7 | Adequate for current scope |
| `shared` | — | 0 | No model validation / serialization tests |
| `head_agent` | — | 0 | No tests at all |
| `strategist` | — | 0 | No tests at all |
| `critic` | — | 0 | No tests at all |
| `publisher` | — | 0 | No tests at all |
| `gateway` | — | 0 | Placeholder module, no tests needed |

---

## 4. Changes Made (updated after Sub-Tasks 2-4)

_This section will be updated with the specific files modified and bugs fixed._
