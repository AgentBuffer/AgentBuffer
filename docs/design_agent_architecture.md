# Design Agent System — Architecture Blueprint

> Multi-agent sub-system for autonomous graphic-design tasks within AgentBuffer.

---

## 1. Overview

The Design Agent System extends the existing Strategist → Critic → Publisher
pipeline with a **Design Director** that interprets design requests and
delegates work to **Specialist Agents**. Each specialist owns a narrow
capability (layout rendering, logo generation, brand validation) and
communicates with the Director through the same `AgentEnvelope` protocol used
by the rest of AgentBuffer.

```
                         AgentEnvelope
  Strategist ──────────────────────────────▶ Design Director
  (or any parent agent)                          │
                                                 ▼
                                          DesignPlan (plan.json)
                                         ┌───────┴────────┐
                                         │  PlanStep[]     │
                                         │  execution_order│
                                         └───────┬────────┘
                            ┌────────────────────┼────────────────────┐
                            ▼                    ▼                    ▼
                     Layout Specialist    Logo Maker (future)   Brand Validator
                            │                                    (future)
                            ▼
                      rendered asset
                            │
                            ▼
                    Design Director  ──AgentEnvelope──▶  caller
```

---

## 2. Directory Structure

```
services/
├── design_director/
│   ├── pyproject.toml            # uv workspace member
│   ├── __init__.py
│   ├── main.py                   # Director entry-point: handle_request()
│   ├── planner.py                # classify_task() → DesignPlan
│   ├── registry.py               # Specialist look-up registry
│   └── tests/
│       ├── __init__.py
│       └── test_director.py
│
├── design_specialists/
│   ├── pyproject.toml            # uv workspace member
│   ├── __init__.py
│   ├── layout_specialist.py      # First specialist — marketing assets
│   ├── common/
│   │   ├── __init__.py
│   │   ├── brand_presets.py      # BrandPreset: fonts, colours, logo rules
│   │   ├── canvas.py             # Pillow helpers (create, draw, place)
│   │   └── text_layout.py        # Dynamic text wrapping & spacing
│   └── tests/
│       ├── __init__.py
│       ├── test_layout_specialist.py
│       └── test_e2e_flow.py
│
├── shared/
│   ├── models.py                 # ← new design models added here
│   └── ...
```

---

## 3. Data Models

All models live in `services/shared/models.py` so every agent imports from a
single source of truth.

### 3.1 DesignTaskType (Enum)

| Value              | Triggers when request contains               |
|--------------------|-----------------------------------------------|
| `logo_variation`   | "logo", "icon", "mark"                        |
| `marketing_header` | "header", "banner", "cover"                   |
| `infographic`      | "infographic", "data visual"                  |
| `social_rebrand`   | "rebrand", "refresh", "redesign"              |

### 3.2 DesignRequest

```json
{
  "task_description": "Create a LinkedIn banner for our spring campaign",
  "task_type": "marketing_header",
  "brand_kit": { "...BrandKit fields..." },
  "platform": "linkedin",
  "inputs": {
    "headline": "Spring Into Savings",
    "body": "Up to 40% off all plans this April.",
    "cta": "Start Free Trial",
    "background_image": "path/to/spring_bg.png"
  }
}
```

### 3.3 PlanStep

```json
{
  "step_id": "step-001",
  "agent": "layout",
  "action": "render_header",
  "params": {
    "headline": "Spring Into Savings",
    "body": "Up to 40% off all plans this April.",
    "cta": "Start Free Trial",
    "platform": "linkedin",
    "brand_kit": { "..." }
  },
  "depends_on": []
}
```

### 3.4 DesignPlan

```json
{
  "task_id": "dtask-a1b2c3",
  "request": { "...DesignRequest..." },
  "steps": [ "...PlanStep[]..." ],
  "execution_order": "sequential"
}
```

### 3.5 SpecialistResult

```json
{
  "task_id": "dtask-a1b2c3",
  "step_id": "step-001",
  "agent": "layout",
  "success": true,
  "output_paths": ["output/designs/dtask-a1b2c3.png"],
  "error": null
}
```

---

## 4. Envelope Types

| `envelope_type`      | `from_agent`       | `to_agent`          | Payload              |
|----------------------|--------------------|---------------------|----------------------|
| `design_request`     | strategist / user  | design_director     | `DesignRequest`      |
| `design_plan`        | design_director    | (internal log)      | `DesignPlan`         |
| `specialist_task`    | design_director    | layout / logo / …   | `PlanStep`           |
| `specialist_result`  | layout / logo / …  | design_director     | `SpecialistResult`   |
| `design_complete`    | design_director    | strategist / user   | `SpecialistResult[]` |

---

## 5. Design Director — Processing Pipeline

```
1.  Receive AgentEnvelope (envelope_type = "design_request")
2.  Validate payload → DesignRequest
3.  classify_task(request.task_description) → DesignTaskType
4.  decompose(request, task_type) → DesignPlan
        • logo_variation   → [logo_maker]
        • marketing_header → [layout]
        • infographic      → [layout]
        • social_rebrand   → [logo_maker, layout]  (sequential)
5.  For each PlanStep in execution_order:
        a. Look up specialist in registry
        b. Call specialist.execute(step)
        c. Collect SpecialistResult
6.  Bundle results → return AgentEnvelope (envelope_type = "design_complete")
```

### Error handling

- If a specialist returns `success=false`, the Director retries once with the
  same params.
- If the retry also fails, the Director returns a partial result with the
  error attached. The parent agent decides whether to retry or degrade.

---

## 6. Specialist Registry

`services/design_director/registry.py` maintains a dict mapping agent names
to callable classes:

```python
SPECIALIST_REGISTRY: dict[str, type[BaseSpecialist]] = {
    "layout": LayoutSpecialist,
    # "logo_maker": LogoMakerSpecialist,   # future
    # "brand_validator": BrandValidator,    # future
}
```

Adding a new specialist requires:
1. Create `services/design_specialists/<name>_specialist.py`
2. Implement the `BaseSpecialist` interface (`execute(step) → SpecialistResult`)
3. Register in the dict above

---

## 7. Layout Specialist — Dynamic Positioning Algorithm

Target: produce a pixel-perfect marketing asset without hardcoded coordinates.

### Platform presets

| Platform  | Width | Height | Use case           |
|-----------|-------|--------|--------------------|
| linkedin  | 1200  | 628    | Feed / header      |
| x         | 1200  | 675    | Card image         |
| instagram | 1080  | 1080   | Square post        |

### Rendering pipeline

```
1.  Load platform preset → (width, height)
2.  Build BrandPreset from BrandKit → colours, font paths, margins
3.  Create blank canvas (width × height, bg = brand primary colour)
4.  If background_image provided → composite onto canvas
5.  Calculate safe zone (canvas minus margins on all sides)
6.  Render headline:
      a. Wrap text to safe-zone width at heading font size
      b. Measure bounding box
      c. If bbox exceeds 40% of safe-zone height → shrink font, re-wrap
7.  Render body text:
      a. Wrap text at body font size
      b. If headline + body + CTA + spacing > safe-zone height → shrink body
         font iteratively (min 14px)
8.  Render CTA button:
      a. Pill shape, accent colour fill
      b. Centered horizontally, placed below body with fixed bottom margin
9.  Place logo per brand rules (default: top-right, 8% padding from edge)
10. Save PNG to output/designs/{task_id}.png
```

### Key constraint

All vertical positions are computed as **cumulative offsets** from the top of
the safe zone:
```
y_headline = margin_top
y_body     = y_headline + headline_height + gap
y_cta      = canvas_height - margin_bottom - cta_height
```

If `y_body + body_height > y_cta - gap`, the algorithm reduces `body_font`
until it fits. This guarantees no overlap regardless of input text length.

---

## 8. Common Utilities

### brand_presets.py

```python
@dataclass
class BrandPreset:
    primary_color: str      # hex from color_palette[0]
    secondary_color: str    # hex from color_palette[1]
    accent_color: str       # hex from color_palette[2] or fallback
    heading_font: str       # path to .ttf
    body_font: str          # path to .ttf
    heading_size: int       # default 48
    body_size: int          # default 24
    cta_size: int           # default 20
    margin: int             # default 60px
    logo_position: str      # "top-right" | "top-left"
    logo_max_scale: float   # 0.15 (15% of canvas width)
    logo_padding: int       # 30px from edge

    @classmethod
    def from_brand_kit(cls, kit: BrandKit) -> "BrandPreset": ...
```

### canvas.py

- `create_canvas(w, h, bg) → Image`
- `place_logo(canvas, logo_path, position, padding, max_scale) → Image`
- `draw_pill_button(canvas, text, font, x, y, w, h, fill, text_color) → Image`

### text_layout.py

- `wrap_text(text, font, max_width) → list[str]`
- `measure_text_block(lines, font, line_spacing) → (width, height)`
- `fit_text(text, font_path, start_size, min_size, max_width, max_height) → (lines, font, size)`

---

## 9. Testing Strategy

### Unit tests — Layout Specialist

| Test                          | Validates                                         |
|-------------------------------|---------------------------------------------------|
| `test_short_text_no_overlap`  | Single-word body positions correctly               |
| `test_long_text_font_shrinks` | 500-char body auto-reduces font, still fits        |
| `test_extreme_headline`       | 200-char headline wraps, doesn't overlap body      |
| `test_empty_body`             | Empty body → headline + CTA only, no crash         |
| `test_output_dimensions`      | LinkedIn preset → exactly 1200×628                 |
| `test_brand_colors_applied`   | Background pixel matches brand primary colour      |

### End-to-end mock test

```
Mock AgentEnvelope (design_request)
        │
        ▼
DesignDirector.handle_request()
        │
        ▼
Assert: DesignPlan has "layout" step
        │
        ▼
LayoutSpecialist.execute(step)
        │
        ▼
Assert: image file exists, correct dimensions, size > 0
        │
        ▼
Assert: Director returns AgentEnvelope (design_complete)
```

---

## 10. CI Integration

New job added to `.github/workflows/ci.yml`:

```yaml
test-design:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv run pytest services/design_director/tests/ services/design_specialists/tests/ -v
```

Ruff linting is already covered by the existing `lint-python` job which
targets `services/`.
