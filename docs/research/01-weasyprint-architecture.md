# 01 — WeasyPrint architecture (primary reference engine)

Date: 2026-10-14. Author: Phase-0 research agent (topic slug `weasyprint`).

All file paths are relative to the WeasyPrint checkout at
`/tmp/claude-0/src/weasyprint/WeasyPrint` unless stated otherwise. Code excerpts are copied
from that checkout. Anything not checked against source is marked **UNVERIFIED**.

## Sources inspected

| Name | Version / tag | Commit SHA | License | Last commit | Maintenance assessment |
|---|---|---|---|---|---|
| Kozea/WeasyPrint | `v70.0` (latest tag; released 2026-09-08 per `docs/changelog.rst`) | `4d3b7b6449e3494f59c7c2f36b512d129225679c` | BSD-3-Clause | 2026-09-08 | Very active. Maintained by CourtBouillon with NLnet funding. v70 is a security release (CVE-2026-55073) that also adds CSS Notes, COLR emoji and box-shadow, and lists about 18 contributors. |
| CourtBouillon/pydyf (WeasyPrint's low-level PDF writer) | `main` at version string `0.13.0` (latest tag `v0.13.0`) | `58e2a6d0bcb8e35ca33d375094411278dfb4fbfa` | BSD-3-Clause | 2026-10-14 | Active. Small (~700 lines). Only inspected for `write()` and `/ID` generation. |
| Runtime deps, **not** inspected (constraints taken from `pyproject.toml`) | tinyhtml5 ≥2.0.0b1, tinycss2 ≥1.5.0, cssselect2 ≥0.8.0, Pyphen ≥0.9.1, Pillow ≥9.1.0, fonttools[woff] ≥4.59.2, cffi; system libs: Pango, HarfBuzz (+hb-subset), Fontconfig, GObject, PangoFT2 (`weasyprint/text/ffi.py:503-524`) | — | — | — | — |
| GitHub issue search (titles only; issue bodies were not reachable from this session) | — | — | — | — | Used for the pain-point list in §6. |

Code size: about 33.6k lines of Python under `weasyprint/`. The largest files are
`css/validation/properties.py` (2164), `css/__init__.py` (1900), `layout/grid.py` (1453),
`formatting_structure/build.py` (1383), `layout/inline.py` (1246), `layout/block.py` (1126),
`layout/table.py` (1112) and `layout/page.py` (1076). Tests: 1701 `def test_` functions.

---

## 1. Pipeline map

Progress-log step names come from `PROGRESS_LOGGER.info('Step N - ...')` calls.

```
HTML(...)                        weasyprint/__init__.py:HTML.__init__
  └─ tinyhtml5.parse(file_obj)   → ElementTree; wrapped by cssselect2.ElementWrapper.from_html_root (__init__.py:177-181)
HTML.render() → Document._render (document.py:181)
  ├─ Document._build_layout_context (document.py:149)
  │    ├─ user stylesheets → CSS(...) objects (tinycss2 parse + preprocess_stylesheet, css/__init__.py:1495)
  │    └─ get_all_computed_styles (css/__init__.py:1866) → StyleFor           [Step 3 - Applying CSS]
  │          ├─ find_stylesheets: <style>, <link rel=stylesheet> (css/__init__.py:301)
  │          ├─ find_style_attributes: style="" + presentational hints (css/__init__.py:349, html5_ph.css)
  │          ├─ UA sheet css/html5_ua.css (256 lines), optional forms sheet
  │          ├─ cascade: per element, cssselect2 Matcher.match → cascaded dict {prop: (value, weight)}
  │          └─ ComputedStyle (lazy, computed on first key access via __missing__)
  ├─ LayoutContext(style_for, get_image_from_uri, font_config, counter_style, target_collector)   [Step 4]
  ├─ build_formatting_structure (formatting_structure/build.py:52) → root box tree
  │    ├─ element_to_box (recursive): ::marker, ::before, text, children, ::after, counters,
  │    │   footnote-call/marker, note-call/marker/callback, string-set, bookmark-label
  │    ├─ html.handle_element: <img>, <embed>, <object>, <svg>, <col>, <colgroup>, <a> → replaced boxes / links
  │    ├─ target_collector.check_pending_targets()   (re-parse forward target-* references)
  │    ├─ process_whitespace / process_text_transform
  │    └─ create_anonymous_boxes: anonymous_table_boxes → flex_boxes → grid_boxes → inline_in_block → block_in_inline
  ├─ layout_document (layout/__init__.py:105) → generator of PageBox            [Step 5 - Creating layout]
  │    ├─ initialize_page_maker
  │    ├─ loop ≤ max_loops=8: make_all_pages → remake_page → make_page → block_level_layout(root)
  │    ├─ second pass: page-based counters in bookmark-label / string-set; collect string-set per page
  │    └─ per page: fixed boxes, margin boxes (make_margin_boxes), layout_backgrounds
  └─ Document(pages=[Page(page_box)...])   Page.__init__ runs gather_anchors (links, anchors, bookmarks, forms)
Document.write_pdf → pdf.generate_pdf (pdf/__init__.py:120)                     [Step 6 - Creating PDF]
  ├─ per page: Stream (pdf/stream.py) ← Page.paint → draw.draw_page → StackingContext → draw/*
  ├─ add_links / add_annotations / add_forms (pdf/anchors.py), outlines (add_outlines)
  ├─ metadata, XMP, attachments                                                   [Step 7 - Adding PDF metadata]
  ├─ build_fonts_dictionary (pdf/fonts.py:308) → subset via hb-subset (or fontTools fallback)
  ├─ add_tags (pdf/tags.py) when pdf_tags / PDF/UA / PDF/A-a
  └─ variant function (pdf/pdfa.py, pdf/pdfua.py, pdf/pdfx.py) → pydyf.PDF.write()
```

### 1.1 Module inventory (what lives where)

| Stage | Files | Notes |
|---|---|---|
| HTML | `__init__.py` (HTML, CSS, Attachment), `html.py` (element handlers, `<meta>` metadata via `get_html_metadata`), `urls.py` (URL fetcher) | Parser is `tinyhtml5`, an html5lib fork. Element handlers use the `@handler(tag)` decorator in `html.py:190`. |
| CSS parsing / validation | `css/__init__.py`, `css/tokens.py`, `css/validation/{__init__,properties,expanders,descriptors}.py`, `css/functions.py`, `css/units.py`, `css/media_queries.py`, `css/counters.py` (`@counter-style`), `css/targets.py` | Validators are keyed by property name. Shorthands go through `expanders.py`. Values containing `var()` are kept as `Pending` and solved at compute time. |
| Cascade / computed values | `css/__init__.py:StyleFor`, `ComputedStyle`, `AnonymousStyle`, `InitialStyle`; `css/computed_values.py` (`@register_computer`); `css/properties.py` (`INITIAL_VALUES`: 221 properties, `INHERITED`, `INITIAL_NOT_COMPUTED`) | See §1.2. |
| Box tree | `formatting_structure/boxes.py` (class hierarchy), `build.py`, `text.py` | §2.1 |
| Layout | `layout/__init__.py` (driver + `LayoutContext`), `page.py`, `block.py`, `inline.py`, `float.py`, `absolute.py`, `table.py`, `flex.py`, `grid.py`, `column.py`, `preferred.py` (min/max-content), `percent.py`, `min_max.py`, `replaced.py`, `leader.py`, `background.py` | Every in-flow layout function returns a fragment and a `resume_at` (§2.2). |
| Stacking / painting | `stacking.py` (`StackingContext`), `draw/__init__.py` (CSS2 Appendix E paint order), `draw/border.py`, `draw/text.py`, `draw/color.py`, `svg/*` (own SVG renderer), `images.py` | Draws straight into a pydyf `Stream`. |
| PDF | `pdf/__init__.py:generate_pdf`, `pdf/stream.py` (Stream subclass: state, fonts, groups, marked content), `pdf/fonts.py` (subset, CID dicts), `pdf/anchors.py` (links, outlines, forms, attachments), `pdf/metadata.py` (XMP), `pdf/tags.py` (structure tree), `pdf/pdfa.py`, `pdf/pdfua.py`, `pdf/pdfx.py`, `pdf/debug.py` | Uses `pydyf` objects. The whole PDF object graph is kept in memory until `pdf.write()`. |

### 1.2 Cascade details worth copying

- **Lazy computed styles.** `ComputedStyle(dict).__missing__` (`css/__init__.py:1159`)
  computes a property only when layout first reads it: cascaded → `inherit`/`initial` →
  `Pending` (`var()`) resolution → math (`calc()`) → `COMPUTER_FUNCTIONS[key]`. Properties
  that are never read are never computed. `AnonymousStyle.__missing__` (`:1116`) inherits
  from the parent style for inherited properties and takes initial values otherwise.
- **Style sharing** (v70, PR #2813). In `StyleFor.__init__` (`css/__init__.py:111-160`),
  elements with the same parent computed style, the same style-attribute declarations and the
  same matched-rule set share one `ComputedStyle` object:
  ```python
  key = (parent_id, element_declarations, tuple(selectors_keys))
  if key in computed_cache:
      computed_styles[etree_element, None] = computed_cache[key]
  ```
  Because styles are shared, code that changes a style must `style.copy()` first; build.py
  does this for footnotes and notes. In Rust the equivalent is `Arc<ComputedStyle>` plus a
  style-sharing cache keyed by (parent style ptr, matched rule ids, inline-style hash), as in
  Servo/Blink.
- **Weights** are `(precedence(origin, importance), layer_order, specificity)` tuples compared
  lexicographically (`declaration_precedence`, `css/__init__.py:603`). `@layer` is supported
  (`_add_layer`, `_parse_layer`).
- **Page styles** are cascaded lazily per `PageType` (`StyleFor.add_page_declarations`,
  `:204`) and matched with `_page_type_match` (`:229`), which handles side, blank, first,
  name, and `nth(An+B [of name])` against page groups. Margin boxes are pseudo-elements of
  the page (`(page_type, '@top-left')`) and inherit from the page context, which inherits
  from the root element (`page.py:set_page_type_computed_styles`).
- After the element pass, the cascaded dict is cleared (`self._cascaded_styles.clear()`)
  except for page rules added later.
- Logical properties map to physical ones only for horizontal-tb, with `direction` deciding
  inline start/end (`PHYSICAL_FUNCTIONS`, `computed_values.py:131-210`). `writing-mode` is not
  supported.

---

## 2. Key data structures and the fragmentation model

### 2.1 Box classes (`formatting_structure/boxes.py`)

```
Box
├─ ParentBox (children: tuple/list)
│   ├─ BlockContainerBox ── BlockBox (+BlockLevelBox), InlineBlockBox (+AtomicInlineLevelBox),
│   │                       TableCellBox, MarginBox, (TableCaptionBox, FootnoteAreaBox are BlockBox)
│   ├─ LineBox
│   ├─ InlineBox (+InlineLevelBox)
│   ├─ TableBox (+BlockLevelBox) ── InlineTableBox
│   ├─ TableRowGroupBox (is_header / is_footer), TableRowBox, TableColumnGroupBox, TableColumnBox
│   ├─ PageBox (page_type, bleed, fixed_boxes)
│   ├─ FlexContainerBox ── FlexBox, InlineFlexBox
│   └─ GridContainerBox ── GridBox, InlineGridBox
├─ TextBox (+InlineLevelBox): text: str, later pango_layout, justification_spacing
└─ ReplacedBox ── BlockReplacedBox, InlineReplacedBox (replacement = image object)
```

- The `display` value maps to a class through `BOX_TYPE_FROM_DISPLAY` (`build.py:15`); the key
  is the outer/inner tuple, e.g. `('block','flow')`.
- One class serves before and after layout. Layout never mutates the source tree's
  structure. It creates fragments with `box.copy()` (shallow `__dict__` copy) or
  `copy_with_children(new_children)`, then sets used values on the copy (`position_x/y`,
  `width`, `height`, margins and so on). Lengths are untyped Python floats or the string
  `'auto'`.
- The flags `is_table_wrapper`, `is_flex_item`, `is_grid_item`, `is_column`, `is_leader`,
  `is_outside_marker` and `force_fragmentation` are class defaults that instances override.
- Flow predicates (`boxes.py:296-343`): `is_floated()` (float is left/right/inline-start/end),
  `is_footnote()` (`float: footnote`), `is_note()` (`position: note()`), `is_running()`
  (`position: running()`), `is_in_normal_flow()` (none of those and not absolute),
  `is_monolithic()` (atomic inline, replaced, `overflow: auto|scroll`, or `overflow: hidden`
  with a fixed height), and `establishes_formatting_context()`.
- `page_values()` returns the start and end page names, propagated from the first and last
  in-flow (or floated) children, as css-break-4 break propagation specifies
  (`ParentBox.page_values`, `:462`).
- Anonymous boxes come from `Box.anonymous_from(parent, ...)`, which uses
  `parent.style.anonymous_style`.
- **Outside `::marker`** is built as an anonymous `BlockBox` with `position: absolute` and
  `is_outside_marker = True` (`build.py:marker_to_box`). In block layout it is placed at
  `box.border_box_x()` (`block.py:330`). When the list item has no other content, a
  zero-width-space `TextBox` is added so the item gets a line (`build.py:228`).
- `::before`/`::after` are real boxes tagged `element_tag='p::before'`
  (`before_after_to_box`, `build.py:279`).
- Table fixups (`anonymous_table_boxes` → `table_boxes_children` / `wrap_table`,
  `build.py:759-1000`) follow CSS2.1 §17.2.1. Rows are wrapped in groups, a `TableBox` gets a
  block **table wrapper** box (`is_table_wrapper`) holding captions, columns are resolved,
  and each cell gets a grid position (`grid_x`, `colspan`, `rowspan`). Collapsed borders are
  precomputed here (`collapse_table_borders`, imported from `layout/table.py:922`).
- Inline/block wrapping: `inline_in_block` (`build.py:1097`) wraps inline runs inside block
  containers into one `LineBox` per run; that one LineBox is split into real lines later.
  `block_in_inline` (`build.py:1209`) splits inlines that contain blocks (CSS2.1 §9.2.1.1).
- `blockify` (`build.py:1000`) blockifies flex/grid items and similar cases.

### 2.2 The skip stack / `resume_at`

A position in the box tree is a **nested single-entry dict**:

```python
{child_index: {grandchild_index: {...: {utf8_byte_offset: None}}}}
```

- `None` means "start from the beginning of this box".
- `{i: None}` means "resume at child `i`, from its start".
- In a `TextBox`, the key is the **UTF-8 byte offset** into `box.text`
  (`inline.py:split_inline_level`, lines 474-489; `split_text_box` returns `resume_index` in
  bytes because Pango indices are byte offsets).
- In tables, a resume point **can hold several cells**:
  `resume_at = {index_row: {index_cell: cell_resume_at, ...}}` (`table.py:197-200`). This is
  how parallel flows (cells in one row) fragment together. A cell missing from the dict on
  resume is treated as finished: `cell_skip_stack = {len(cell.children): None}`
  (`table.py:147-151`).
- Consumers unpack it with `(skip, skip_stack), = skip_stack.items()`, which asserts a single
  entry in most places (`block.py:304`).

A Rust engine can carry the same idea as `enum BreakToken { Child { index: u32, inner:
Option<Box<BreakToken>> }, Text { byte_offset: u32 }, Parallel(Vec<(u32, BreakToken)>) }`.
This is close to Blink LayoutNG's `BreakToken`.

### 2.3 Layout function contract

`block_level_layout(context, box, bottom_space, skip_stack, containing_block,
page_is_empty, absolute_boxes, fixed_boxes, adjoining_margins, first_letter_style,
first_line_style, discard, max_lines)` (`block.py:17`) returns a **6-tuple**:

```python
(new_box,            # laid-out fragment, or None = "nothing fits / abort, push whole box to next page"
 resume_at,          # skip stack for the continuation, or None = finished
 next_page,          # {'break': 'any'|'page'|'left'|'right'|'recto'|'verso'|'column', 'page': name|None}
 adjoining_margins,  # list of margins still collapsing through the bottom edge
 collapsing_through, # bool: the box collapsed through (empty), margins carried on
 max_lines)          # remaining line budget for line-clamp/max-lines
```

Table, flex, grid and replaced layouts return a 5-tuple; `block_level_layout_switch` appends
`None` for `max_lines` (`block.py:85`). Float and absolute layouts return
`(new_box, resume_at)`.

The other parameters:

- **`bottom_space`**: space that must stay free at the bottom of the page (parent bottom
  padding and border when `box-decoration-break: clone`, table footers, and so on).
  `-inf` means "unconstrained", used for margin boxes, the footnote area and intrinsic
  measurement. The overflow test is
  `LayoutContext.overflows_page(bottom_space, y) = y > (page_bottom - bottom_space) * (1+1e-9)`
  (`layout/__init__.py:240-247`). The relative epsilon is there for float error.
- **`page_is_empty`**: the progress guarantee. When `True`, a box **must** place something
  even if it overflows, so layout cannot loop forever.
- **`absolute_boxes` / `fixed_boxes`**: out-parameters. Abspos children are recorded as
  `AbsolutePlaceholder`s (`absolute.py`) during flow and laid out after their containing
  block is known (`block.py:462-467` for `position: relative` containers; `page.py` for page-level ones).
  Whenever children are discarded during backtracking, `remove_placeholders()`
  (`block.py:669`) must undo these side effects: placeholders, footnotes
  (`context.unlayout_footnote`), broken out-of-flow entries, excluded float shapes, and
  running notes. The engine keeps this side-effect ledger by hand, and many bug fixes touch
  it (e.g. v70 "#2714 Remove nested placeholders").

### 2.4 How a block container fragments (`block.py:block_container_layout`, line 238)

1. `is_start = skip_stack is None`. If the box is resumed, its top decoration is removed with
   `box.remove_decoration(start=not is_start, end=False)`.
2. `draw_bottom_decoration = discard or box_decoration_break == 'clone'`. When it is true,
   `bottom_space` grows by the box's bottom padding, border and margin, so children break
   early enough to leave room for the cloned bottom edge.
3. The function iterates `box.children[skip:]`. For each child:
   - **Class A break between siblings**: `block_level_page_break(last_child, child)`
     combines every `break-after` value along the previous sibling's last-descendant chain
     with every `break-before` value along the next sibling's first-descendant chain
     (`_add_break_values`, `block.py:510`), using this priority:
     left/right/recto/verso > page > avoid > auto
     (`block.py:525-560`). If the result forces a break (`force_page_break`), or the
     named page changes (`block_level_page_name`), the loop stops with
     `resume_at = {index: None}` and `next_page = {'break': value, 'page': name}`.
   - Out-of-flow children go through `_out_of_flow_layout` (`:225`). Abspos children leave a
     placeholder. Floats are laid out now; if one overflows the page and the page is not
     empty, the box breaks before it, or uses `find_earlier_page_break` when breaks are avoided.
     Running elements and notes are registered with `context.add_running_element`.
   - The (single) `LineBox` child goes through `_linebox_layout` (`:286`), which iterates
     `iter_line_boxes` (one line per step) and handles orphans/widows and footnotes (§2.5).
   - Block-level children go through `_in_flow_layout` (`:60`), which recurses. Two overflow
     checks run after the recursive call:
     - If the content box overflows, the child is dropped (`new_child = None`).
     - If only the child's bottom border, padding or margin overflows, the child is laid
       out again with a larger `bottom_space` (`:155-166`).
4. When a child returns `new_child is None` ("nothing fits"):
   ```python
   page_break = block_level_page_break(last_child, child)
   if avoid_page_break(page_break, context):
       result = find_earlier_page_break(context, new_children, absolute_boxes, fixed_boxes)
       if result: new_children, resume_at = result; stop = True; return ...
       elif not page_is_empty: abort = True; return ...   # propagate failure upward
       # else ignore 'avoid' and break anyway
   if new_children: resume_at = {index: None}; stop = True
   else: abort = True    # first child didn't fit: cancel this box entirely
   ```
   (`block.py:179-222`). **Abort** returns `None` from the parent too
   (`block.py:378-389`), so the grandparent then tries an earlier break. This is how
   `break-inside: avoid` and `break-before/after: avoid` **backtrack up the tree**.
5. `break-inside: avoid` on the box itself: when the box would fragment and the page is not
   empty, it returns `None` (`block.py:409-416`) and the parent pushes the whole box to the
   next page.
6. The fragment is built with `new_box = box.copy_with_children(new_children)`, then
   `new_box.remove_decoration(start=not is_start, end=box_is_fragmented and not discard)`.
   `ParentBox.remove_decoration` does nothing when `box_decoration_break == 'clone'`
   (`boxes.py:431-437`). That is the entire box-decoration-break implementation: with
   `slice`, the top or bottom margin, border and padding are zeroed. Backgrounds are
   repeated per fragment rather than sliced, which the docs list as a known deviation.
7. A fragmented box with `height: auto` is stretched to the bottom of the fragmentainer:
   `new_box.height = page_bottom - bottom_space - position_y - ...` (`block.py:480-491`),
   following css-break-3 §box-splitting.
8. `margin-break` and truncation of margins at an unforced break: in
   `block_level_layout` (`:36-47`), when `context.current_page > 1 and page_is_empty`, the
   top margin is zeroed for `margin-break: discard`, and also for `auto` when
   `not context.forced_break`.

**`find_earlier_page_break(children)`** (`block.py:571`) scans the already placed
fragments from the end:

- If the children are `LineBox`es, it cuts at `len(children) - widows` lines, provided at
  least `orphans` lines remain, and returns `{0: line.resume_at}`. This works because each
  laid-out `LineBox` stores its own `resume_at` (`line.resume_at`, `block.py:310`).
- Otherwise it walks back through siblings looking for a Class A break that is not avoided
  (headers, footers and column boxes are skipped). It recurses into the last breakable
  child (`BlockBox`, `TableBox`, `TableRowGroupBox` without `break-inside: avoid`), returns
  `{child.index: inner_resume}`, and re-appends the table footer when it splits a row group.
- Each fragment's `index` attribute records its index in the **original** parent, so the
  skip stack can be rebuilt from fragments.
- Cost: backtracking re-uses fragments already built (no re-layout), but each abort level
  re-lays out the whole subtree on the next page. Worst case is quadratic per page in depth.

### 2.5 Lines, orphans/widows, footnotes (`block.py:_linebox_layout`, `_break_line`)

- `iter_line_boxes` (`inline.py:24`) yields `(line, resume_at)` one line at a time, lazily.
  Lines are therefore laid out only up to the overflow point plus `widows` look-ahead lines,
  which are laid out and thrown away (`for next_line, _ in lines_iterator: needed -= 1`).
- On overflow, `_break_line` (`block.py:252`) works as follows:
  - Fewer than `orphans` lines placed and the page is not empty: abort the whole box
    (return `None`, which pushes the paragraph to the next page).
  - `needed` (widows minus lines still available) greater than `over_orphans`: abort.
  - Otherwise, pop `needed` lines from this page to satisfy widows.
  - Resume at `{index: skip_stack}` of the first removed line.
- **Footnotes.** When a line containing a `::footnote-call` is placed,
  `context.layout_footnote(footnote)` (`layout/__init__.py:390`):
  - lays out the footnote area again with all current footnotes
    (`block_level_layout(... -inf ...)`);
  - shrinks `context.page_bottom` by the area's height.

  If the line now overflows, the footnote is **reported** to the next page
  (`report_footnote`). Then `footnote-policy` applies (`block.py:450-466`):
  - `line`: break before this line, honouring widows.
  - `block`: abort the whole block.
  - `auto`: keep the call here; the body moves to the next page.

  Before breaking, the code also tries reporting already-placed footnotes to make room
  (`block.py:397-409`, overflow branch of `_linebox_layout`). On the next page, `make_page` first places
  `context.reported_footnotes` (`page.py:615-624`).
- `max-lines` / `line-clamp` / `block-ellipsis` / `continue: discard` are threaded through
  the same return values (`max_lines` is the 6th tuple element).

### 2.6 Tables: repeated thead/tfoot, row/cell fragmentation (`layout/table.py:table_layout`)

- `has_header = table.children[0].is_header`, `has_footer = table.children[-1].is_footer`.
  Only the first header group and last footer group count.
- `all_groups_layout()` (`table.py:427-533`) **on every page fragment**:
  1. Lays out the header and the footer independently. Their own breaking is ignored: a
     header that would need a `resume_at` is dropped. They are measured with
     `header_footer_bottom_space = bottom_space` when the page is not empty, or `-inf` when
     it is.
  2. Tries body rows with both: start at `position_y + header_height` with
     `bottom_space + footer_height`. If no body row fits, it drops the footer and retries
     with the header only, then the footer only, then neither.
  3. The footer is translated to sit right under the last body row
     (`footer.translate(dy=end_position_y - footer.position_y)`).
- Because the header and footer are re-laid-out per fragment from the original box, they
  **repeat on every page**. There is no `-weasy-` switch; repetition is the default for
  `display: table-header-group` / `table-footer-group`.
- Row fragmentation (`group_layout`, `table.py:91`):
  - Each cell is laid out with `block_container_layout` using a per-cell skip stack.
  - Each cell's `height` is temporarily set to `'auto'`, keeping `computed_height` as a minimum.
  - If any cell has a `resume_at`, the row breaks. Its cells lose their bottom decoration,
    and on the next page they continue from their own skip stacks.
  - `break-inside: avoid` on the row or any of its cells triggers the table's own
    `_find_earlier_page_break` (it differs from block.py's).
  - If no cell could show anything, the row gives up (`next_position_y = inf`).
- Collapsed borders on split tables: `table.skip_cell_border_top/bottom` and
  `table.border_top_width` are recomputed from `collapsed_border_grid[skipped_rows]`
  (`table.py:55-75`).
- Column widths come from `table_wrapper_width` → `auto_table_layout` / `fixed_table_layout`
  (`table.py:626, 712`). They are cached in `context.tables[table]`
  (`preferred.py:452, 492, 707`) so later fragments do not measure again.

### 2.7 Flex, grid, multicol fragmentation

- **Flex** (`flex.py:flex_layout`, `:18`). It returns `resume_at = {first_level_skip + index:
  child_resume_at}` (`flex.py:908-942`), i.e. items are fragmented one at a time in order.
  This works for single-line column flex and for row wrap at line boundaries. Multi-line
  parallel fragmentation is limited (docs: "works for simple use cases but is not deeply
  tested").
- **Grid** (`grid.py`). Fragmentation is supported between rows but not inside rows (docs).
- **Multicol** (`column.py:columns_layout`). Columns are created as `is_column` blocks.
  Balancing is iterative: content is laid out repeatedly with a candidate height until it
  fits (`column.py:159-300`, `while True` loops). `column-span: all` is supported for
  direct children only. Docs say pagination inside columns is "not seriously tested".
  Reported slow cases: GitHub issues #1642 and #1689 ("Really slow rendering of a 3 column
  layout"), both closed.

### 2.8 Out-of-flow content broken across pages

`context.broken_out_of_flow[new_box] = (box, containing_block, bfc_root, resume_at)`
(`layout/__init__.py:269`). At the start of the next page, `make_page` lays those boxes out
first (`page.py:663-697`) and installs their excluded shapes in the right BFC. If in-flow
content makes no progress on a page that has only out-of-flow content, the root is
force-fragmented: `parent.force_fragmentation = True` (`page.py:712-728`) so the page still
covers its height.

### 2.9 Page loop, page_maker and re-layout for counters

`context.page_maker` is a list with one entry per page boundary:

```python
(resume_at,      # skip stack where page i starts
 next_page,      # {'break': ..., 'page': name}: forced-break side and named page for page i
 right_page,     # bool
 page_state,     # (quote_depth[1], counter_values{name:[stack]}, counter_scopes, page_groups)
 remake_state)   # {'content_changed', 'pages_wanted', 'anchors', 'content_lookups'}
```

`initialize_page_maker` (`layout/__init__.py:26`) seeds entry 0. Then:

- **`make_all_pages`** (`page.py:1046`) walks `i = 0..`. Page `i` is re-made only when
  `remake_state['content_changed'] or ['pages_wanted']`; otherwise the cached page is
  reused (`yield pages[i]`). It stops when `resume_at is None` and there are no reported
  footnotes.
- **`remake_page(index)`** (`page.py:968`):
  - Deep-copies `page_state`.
  - Decides blank-page insertion: `blank = (next side is left and we are on a right page)`
    and so on, or reported footnotes remain after the content has ended.
  - Computes the page name and groups (`_update_page_groups`, for `:nth(... of name)`).
  - Builds `PageType(side, blank, name, index, groups)`, cascades page styles, calls
    `make_page`, then compares the new `(resume_at, next_page, right_page, page_state)` with
    the cached `page_maker[index+1]`.
  - If anything differs, the next entry is replaced and its `content_changed` is set, so
    the cascade of re-makes continues only while results keep changing.
- **`make_page`** (`page.py:559`):
  1. Resolves page size and margins (`page_width`/`page_height` apply the block-width
     equations to the page box).
  2. Sets `context.page_bottom` and creates `FootnoteAreaBox` from `@footnote`.
  3. Places reported footnotes, the `@note-area`, and broken out-of-flow boxes.
  4. Runs `block_level_layout(root_box, resume_at)` and lays out the footnote area.
  5. Applies `counter-increment: page` (added implicitly by
     `_standardize_page_based_counters` unless the author touched `page`).
  6. Scans descendants for:
     - **anchors** → `target_collector.cache_target_page_counters(anchor, page_counter_values, ...)`
       records which page each target landed on, and marks every **referencing** box's page
       `content_changed` if the value changed;
     - **`missing_link`** boxes (content that used counters unknown at build time, e.g.
       `counter(page)`, `counter(pages)`, or `target-counter(..., page)`) →
       `counter_lookup.parse_again(page_counter_values)` **rebuilds that box's children
       in place** in the source tree and sets `content_changed` for this page.

     `pages` marks `pages_wanted`.
- **`layout_document`** (`layout/__init__.py:105`):
  ```python
  for loop in range(max_loops):            # max_loops = 8
      pages = list(make_all_pages(context, root_box, html, pages))
      actual_total_pages = len(pages)
      for page_data in context.page_maker:
          page_state[1]['pages'] = [actual_total_pages]
          if remake_state['content_changed']: reloop_content = True
          if remake_state['pages_wanted']: reloop_pages = initial_total_pages != actual_total_pages
      if not reloop_content and not reloop_pages: break
  ```
  So `counter(pages)` costs **one extra pass only if the total changed**, and only for pages
  that asked for it. A TOC with `target-counter(attr(href), page)` that points forward needs:
  - pass 1: lay out with blank or zero numbers (text width may differ);
  - targets record their pages; referencing pages are marked `content_changed`;
  - pass 2: re-make from the first changed page onward. The cascade stops once
    `page_maker[i+1]` stabilises.

  This is a fixpoint iteration capped at 8 loops; anything still unresolved stays wrong
  without an error. Docs link the limitations to issue #93 (content of #93 is
  **UNVERIFIED**; issue body not reachable).
- **Margin boxes are laid out after pagination is final** (`layout/__init__.py:200-219`). So
  `counter(pages)` in a footer **never causes re-layout of body content**. Only body content
  using page-based counters triggers loops. `string-set` and `bookmark-label` values that
  use page counters are also re-parsed once after the loop (`:150-197`).

**Implication for recto.** WeasyPrint keeps every page (full box trees) in memory and may
re-make pages from any index, so it cannot stream. For recto: emit pages as soon as no
forward-dependency can change them (see §7).

---

## 3. @page handling

| Feature | Implementation (file:function) | Notes |
|---|---|---|
| Selectors `:first`, `:left`, `:right`, `:blank`, named pages, `:nth(An+B)`, `:nth(An+B of name)` | `css/__init__.py:parse_page_selectors` (1378), `StyleFor._page_type_match` (229) | `:first` is `page_type.index == 0`. Specificity is (name, pseudo-classes, sides); a TODO in the code says "Specificity is probably wrong". Page groups (`page_groups` in `page_state[3]`) are maintained by `page.py:_update_page_groups` (863), following css-gcpm-3 document-sequence selectors. |
| Left/right progression | `initialize_page_maker` (root `break-before`, `direction`), `remake_page` (blank page if the forced side does not match) | Writing-mode-aware progression is a TODO. `recto`/`verso` depend on `direction` only. |
| Blank pages | `remake_page`: `blank=True` → `make_page` uses `root_box.copy_with_children([])` and keeps the previous `resume_at` | `:blank` styles apply. |
| `size` | validation in `css/validation/descriptors.py` / `properties.py`; used as `page.style['size']` (device size) in `make_page` | Named sizes and `landscape`/`portrait`. The first page size feeds `initial_page_sizes` for viewport units (`vw`, `vh`); `pvw`/`pvh` refer to the whole page (docs). |
| Margins / padding / border on the page | `page.py:page_width_or_height` (515) | Block-width equations; over-constraint resizes the containing block. |
| `bleed`, `marks` | `computed_values.py:bleed` (`auto` → 8px if `crop` in marks, else 0); `draw_page` → `draw_background(..., bleed=page.bleed, marks=marks)`; `pdf/__init__.py` sets MediaBox = bleed box, TrimBox = page box, BleedBox = TrimBox + min(10pt, bleed) | `crop` and `cross` marks are drawn in `draw/__init__.py:draw_background`. |
| 16 margin boxes | `page.py:make_margin_boxes` (397) | See below. |
| `@footnote` area | `make_page`: `FootnoteAreaBox(page, style_for(page_type,'@footnote'))`, placed at page bottom and translated up by its height | `footnote-display: block` / `inline` (`compact` unsupported; the build turns it into inline: `build.py:121-126`). `footnote-policy: auto` / `line` / `block`. |
| `@note-area` (CSS Notes draft, new in v70) | `make_page` (`page.py:630-661`) | In-flow, floated or absolute. `note()` position, `::note-call`, `::note-marker`, `::note-callback`. Experimental. |

**Margin box sizing** (`page.py`):

- For each side (top, bottom, left, right), three boxes are made with
  `make_box('@{side}-{left|center|right}')` (or `top/middle/bottom` for left and right
  sides).
- A box is "generated" when `content` is not `normal`, `inhibit` or `none`. Content is
  built with `content_to_boxes(..., context, page)` from a **deep copy of the page's counter
  state** (margins must not change page counters).
- `compute_variable_dimension(context, side_boxes, vertical, available_size)` (line 170)
  implements css-page-3 §margin-dimension:
  - If B (center) is **not generated** and A and C are both `auto`, space is distributed
    by **max-content** widths when they fit; otherwise by `(max-min)` flex factors over the
    min-content widths; otherwise proportionally to min-content.
  - If B is generated and `auto`, B's width is resolved against
    `2 * max(outer_max(A), outer_max(C))` using the same three tiers, and A and C get
    `(available - B) / 2` each, which keeps B centred.
  - Min- and max-content come from `preferred.min_content_width/max_content_width`
    (`HorizontalBox`, line 75). For vertical sides, min-content is 0 and max-content is
    1e6 (`VerticalBox` TODO, line 64-70).
- `compute_fixed_dimension` (line 107) implements the css-page-3 §margin-constraints rules
  2–6 for the other axis. It includes a non-spec clamp, `inner=0` when over-constrained, with
  a link to the www-style thread.
- Corner boxes get `margin_left/top` × the corner's size.
- `margin_box_content_layout` (line 487) lays out with `bottom_space=-inf`. It asserts
  `resume_at is None`: margin box content never fragments and silently overflows. It then
  applies `vertical-align: middle|bottom` by translating children.
- `min/max-width/height` on margin boxes are not supported (docs).

**Running elements** (`position: running(name)`, `content: element(name[, first|start|last|first-except|all-once])`):

- During body layout, a running box is out of flow. `_out_of_flow_layout` calls
  `context.add_running_element(child)` (`block.py:246`), which appends the box to
  `context.running_elements[name][page_number]`.
- `get_string_or_element_for` (`layout/__init__.py:305`) resolves the keyword:
  - `first`: the first assignment on the current page, else the last from previous pages;
  - `start`: walks down the page's first-descendant chain; approximate;
  - `last`, `first-except`, `all-once`.
- The margin box then gets `new_box.deepcopy()` with `position: relative` (v70 #2888), and
  page counters are re-substituted in its content (`build.py:535-554`).
- Docs: "the `start` parameter of `element()` is not supported". The code has a `start`
  branch, so treat it as partial.
- Re-make trigger: if this page's running elements differ from the previous layout's
  (`page.py:733-739`), the previous page is marked `content_changed`.

**`string-set` / `string()`**:

- `string-set` is computed at **build time** into `box.string_set` (`build.py:compute_string_set`).
  It supports `content()`, `content(before|after|first-letter|text)`, `attr()`, counters and
  target functions.
- After pagination, `layout_document` collects
  `context.string_set[name][page_number].append(text)` from every page's descendants in
  tree order (`layout/__init__.py:190-195`).
- `string()` resolves with the same keyword machinery as `element()`.
- `string()` outside the page context logs a warning and is ignored (`build.py:450-456`).

**`counter(page)` / `counter(pages)`**:

- The page counter lives in `page_state[1]` (`counter_values`). It is incremented by the
  implicit `counter-increment: page` in `@page` and can be reset or set from `@page` rules.
- `pages` is filled after each loop (`page_counter_values['pages'] = [actual_total_pages]`).
- Margin boxes see them directly (`make_margin_boxes(context, page, state)`). Body content
  sees them through `missing_counters` → `parse_again` (§2.9).
- Open issues show gaps: #2114 "Apply counter-increment on page counter when counter-reset
  is used", #1480 "Document defined counter not available in margin-box", #1205 "Use page
  counter style and value in PDF page numbers" (PDF `/PageLabels` not emitted).

**`target-counter()` / `target-counters()` / `target-text()`**:

- `css/targets.py:TargetCollector` keeps two maps:
  - `target_lookup_items[anchor] = TargetLookupItem(state='pending'|'up-to-date'|'undefined',
    target_box, parse_again_functions{(source_box, css_token): fn}, page_maker_index,
    cached_page_counter_values)`;
  - `counter_lookup_items[(box, css_token)] = CounterLookupItem(parse_again,
    missing_counters, missing_target_counters, page_maker_index, pending,
    cached_page_counter_values)`.
- Anchors are collected while computing styles (`StyleFor.set_computed_styles` →
  `collect_anchor`). The `anchor` property is internal; it is fed from `id`/`name` by the
  UA sheet (**UNVERIFIED** exact UA rule).
- `store_target` snapshots the target's counter values **after its `::before` and before
  `::after`** (`build.py:166-170`).
- Forward references: `lookup_target` returns `pending`, and `compute_content_list` stops
  the content list there (`break`). After the whole tree is built, `check_pending_targets()`
  calls every registered `parse_again` (`build.py:73`), which rebuilds the referring box's
  children in place.
- Page-based targets are then handled by the page loop (§2.9).
- `target-text(attr(href), content|before|after|first-letter)` uses
  `target_box.extract_text`.

**`leader()`**:

- `compute_content_list` creates an `InlineBox` with `is_leader=True`, `white-space: pre`,
  and one `TextBox` of the leader string (`build.py:555-566`).
- After a line is laid out, `layout/leader.py:handle_leader` computes
  `extra_width = containing_block.width - sum(widths)`, minus overlapping float widths.
- It then fills the leader box with N copies of the text box, **aligned from the right
  edge** so the dots line up across lines, and translates the following siblings right by
  `extra_width`. One leader per line (the first one found).

**Bookmarks**:

- `bookmark-level`, `bookmark-label` (content list, computed at build), and
  `bookmark-state: open|closed`.
- `anchors.py:gather_anchors` (line 30) records `(level, label, (x, y), state)` per page.
- `Document.make_bookmark_tree` and `pdf/anchors.py:add_outlines` build `/Outlines`.
- Duplicates across fragments are suppressed: only the first fragment per element keeps its
  label (`layout/__init__.py:162-175`, issue #1145).
- The UA sheet gives `h1`–`h6` bookmarks by default.

**Links / anchors**:

- `anchors.py:gather_anchors` collects them per page.
- `pdf/anchors.py:resolve_links` → `add_links` creates `/Link` annotations and named
  destinations, sorted into the `/Dests` name tree (`pdf/__init__.py:310-318`).

---

## 4. CSS feature catalog (v70.0)

Sources: `docs/api_reference.rst` §"Supported Features" (lines 84–900), checked against
`css/properties.py:INITIAL_VALUES` (221 properties) and the code. Where docs and code
disagree, the code is authoritative and the row is marked *(doc stale)*.

| Area | Supported | Not supported / partial |
|---|---|---|
| CSS 2.1 | Almost everything for print. Passes Acid2 (`tests/test_acid2.py`). | `visibility: collapse` on tables; min/max-height on table boxes; min/max on margin boxes; conforming font matching (font-family passed to Pango/fontconfig); system colors and fonts. The docs also say "RTL / bidi text" is unsupported; Pango does bidi shaping and `direction` exists, but full bidi box reordering is not done. |
| Selectors 3/4 | All of level 3. Level 4 except below. `:hover`, `:active`, `:focus`, `:target`, `:visited` parse but never match. | `:dir()`, input validity pseudo-classes, column combinator `\|\|`, `:nth-col()`. |
| Cascade | `!important`, origins, `@layer`, `@import`, `@media` (`css/media_queries.py`), CSS nesting (`tests/css/test_nesting.py`), custom properties + `var()` | `unset` keyword (docs say unsupported). `revert`: **UNVERIFIED**. |
| Values & units | All length units incl. `cap`, `ic`, `lh`, viewport and `pv*` units; all math functions (`calc`, `min`, `max`, `clamp`, trig...) (`css/__init__.py:resolve_math`); `attr()` in `content` and `string-set` | `attr()` elsewhere. |
| Box model / sizing | `box-sizing`; logical properties (horizontal-tb only) | `min-content`, `max-content`, `fit-content()` keywords; `writing-mode`. |
| Fragmentation (css-break-3/4) | `break-before/after/inside` (+`page-break-*` aliases), `orphans`, `widows`, `box-decoration-break` (slice/clone), `margin-break` | `slice` repeats backgrounds instead of slicing them; column breaks are only partial in multicol; no regions. |
| Paged media (css-page-3) | `@page` with all selectors, `size`, page margins/padding/border, `bleed`, `marks`, 16 margin boxes, named pages (`page`), page counters | Page-based counter edge cases (#93). `@page` `page-orientation`: **UNVERIFIED**. |
| GCPM-3 | `:nth()` page selectors incl. `of <name>`; running elements; `string-set`/`string()`; footnotes (`float: footnote`, `::footnote-call`, `::footnote-marker`, `@footnote`, `footnote-display: block\|inline`, `footnote-policy`); `bookmark-*`; `leader()`; `target-counter(s)`, `target-text` | `element(start)` partial; `footnote-display: compact`; page floats. |
| CSS Notes (unofficial draft) | `position: note()`, `@note-area`, `::note-call`, `::note-marker`, `::note-callback`, `element(..., all-once)` | `note-policy`. |
| Generated content | `content` with strings, `url()`, counters, `counters()`, quotes (`open-quote` etc. handled in `compute_content_list`, despite docs), `attr()`, `leader()`, `content()`; `::marker`, `::before`, `::after`, `::first-line`, `::first-letter`; `@counter-style` (`css/counters.py`) | The docs say quotes are "not implemented" *(doc stale: code handles `quote` items, `build.py:521-534`)*. |
| Lists | `list-style-*`, outside marker as abspos block, `counter-*`, `list-item` counter | — |
| Text (css-text-3/4) | `white-space`, `overflow-wrap`, `word-break: break-all`, `text-transform` incl. `full-width`, `text-align` (`start`/`end`/`justify-all`), `text-align-last`, `text-justify`, `tab-size`, `hyphens`, `hyphenate-character`, `hyphenate-limit-chars`, `hyphenate-limit-zone`, `letter-spacing`, `word-spacing`, `text-indent` (property exists; docs list it as unsupported, probably meaning `hanging`/`each-line`) | `line-break`, `match-parent`, `hanging-punctuation`, `text-wrap` / `wrap-*`, `text-spacing`, character alignment. |
| Text decoration | `text-decoration-line/style/color/thickness`, `text-underline-offset` | `text-shadow`, `text-emphasis-*`, `text-underline-position`. |
| Fonts | `@font-face` (incl. woff/woff2 via fontTools/brotli, `unicode-range`, `local()`), `font-*` from Fonts-3, `font-feature-settings`, `font-variation-settings`, `font-language-override`, COLR emoji (v70) | `@font-feature-values`, most `font-variant-alternates`. |
| Color | Color 4 fully (lab/lch/oklab/oklch/`color()`); Color 5: `light-dark()`, `device-cmyk()`, `@color-profile` (ICC output intents, `tests/draw/test_cmyk_color_profiles.py`) | `color-mix()`, `contrast-color()`. |
| Backgrounds & borders | Multiple backgrounds, all `background-*`, `border-radius`, `border-image-*`, `mask-border-*`, `box-shadow` (v70; blur approximated with gradients) | — |
| Images | `url()`, `linear-`/`radial-`/`repeating-radial-gradient()`, `object-fit`, `object-position`, `image-resolution` (resolution only), `image-rendering`, `image-orientation`; raster via Pillow; SVG via its own vector renderer (`svg/*`) | `image()`, `conic-gradient` (not listed: **UNVERIFIED**), `from-image`/`snap`. EPS rendering removed in v70 (security). |
| Transforms | 2D `transform`, `transform-origin` | 3D, `perspective`, `backface-visibility`. |
| Overflow | `overflow` (CSS2), `text-overflow`, `block-ellipsis`, `line-clamp`, `max-lines`, `continue` | `overflow-x/y`, `overflow-clip-margin`. |
| Positioning / floats | static, relative, absolute, fixed (repeated on every page via `layout_fixed_boxes`), floats, clear, `z-index` stacking (`stacking.py`) | `position: sticky`: **UNVERIFIED** (likely treated as relative). |
| Tables | auto and fixed layout, `border-collapse`, `border-spacing`, captions, colgroups, row/col spans, repeated thead/tfoot, row and cell fragmentation | `visibility: collapse`. |
| Flexbox | All properties ("simple use cases, not deeply tested") | — |
| Grid | Long list in docs §Grid. Main gaps: `inline-grid`, `auto-fill`/`auto-fit`, subgrid, `grid-auto-flow: column`, baseline alignment, fragmentation **in** rows. | — |
| Multicol | `column-width/count/gap/rule-*`, `column-fill` (balancing), `column-span` (direct children) | Constrained height; spanning in nested descendants; column breaks partial. |
| UI | `outline*`, `outline-offset`, `appearance: auto` → AcroForm fields (text, checkbox, textarea, select) | `accent-color`, `cursor`, `resize`, `caret-*`. |

---

## 5. Text stack

- **Library binding.** `text/ffi.py` declares a cffi `cdef` and `_dlopen`s these libraries
  at import time (`ffi.py:503-524`): gobject, pango, harfbuzz, harfbuzz-subset,
  harfbuzz-vector (optional), fontconfig, pangoft2.
- **FontConfiguration** (`text/fonts.py:77`):
  - `FcInitLoadConfigAndFonts()` (reads the system font config), then
    `pango_ft2_font_map_new()` with that config.
  - `@font-face` fonts are fetched, woff/woff2 are decoded with fontTools, and the result is
    **written to a temp dir** (`mkdtemp(prefix='weasyprint-')`).
  - Each face is registered by generating a fontconfig XML snippet
    (`FcConfigParseAndLoadFromMemory`) that prepends the family and assigns
    slant/weight/width/features/charset (unicode-range), then `FcConfigAppFontAddFile`.
  - Font matching is therefore **fontconfig's**, not CSS Fonts §5. Font fallback for
    missing glyphs is also fontconfig's (system-dependent; determinism hazard).
- **Layout object** (`text/line_break.py:Layout`, line 57):
  - One `PangoLayout` per text fragment with a `PangoFontDescription`
    (`get_font_description`), language (from `lang`), base dir, and OpenType features as
    `pango_attr_font_features_new`.
  - Letter-spacing, word-spacing and hyphen insertion are added as Pango attributes in
    `set_text`.
  - Strut metrics are cached per font key in `font_config.strut_layouts` (`strut()`, line 531).
- **Line breaking** (`split_first_line`, line 242). Pango is the line breaker (UAX #14 via
  `pango_layout_get_log_attrs_readonly`):
  1. Lay out a **prefix** of the text (`max_width / font_size * 4` chars) to avoid shaping
     huge strings, then take the first `PangoLayoutLine` and its `start_index` of line 2.
  2. Return early if it fits.
  3. Try to pull the next word back onto the line, since Pango may wrap early when trailing
     spaces collapse.
  4. Hyphenate: manual (`\xad`) or `hyphens: auto` with **Pyphen** dictionaries chosen by
     `pyphen.language_fallback(lang)`. Pyphen instances are cached in `context.dictionaries`.
     It tries hyphenation points from the end, re-laying out
     `prefix + hyphenate_character` each time, and respects `hyphenate-limit-chars` and
     `hyphenate-limit-zone`.
  5. `overflow-wrap` / `word-break` fallbacks.
- **Shaping result reuse.** `split_text_box` stores `box.pango_layout = layout`
  (`inline.py:949`). Drawing reads glyphs straight from the stored layout's
  `PangoGlyphItem`s (`draw/text.py:draw_first_line`, lines 145-230). It emits `<gid>` hex
  strings in `TJ` arrays with kerning offsets, records `font.widths[gid]` and
  `font.to_unicode[gid]` (first cluster seen wins), and handles `.notdef` with a warning.
- **Fonts in PDF** (`pdf/fonts.py`):
  - `Font.hash` is 6 letters from md5 of the Pango font description, so subset prefixes
    are deterministic ("Never use the built-in hash function here: it's not stable").
  - Subsetting uses **hb-subset** when HarfBuzz ≥ 4.1.0 (`_harfbuzz_subset`, line 219).
    It runs two passes: first with `RETAIN_GIDS` to keep only used glyphs, then a pass to
    drop trailing glyph IDs. GSUB, GPOS, SVG, JSTF, DSIG and similar tables are dropped.
    Hinting is optional.
  - fontTools subsetting is a deprecated fallback (v70 #2886 adds a warning).
  - Output is CID-keyed Type0 fonts with ToUnicode CMaps (`_build_vector_font_dictionary`);
    bitmap fonts become Type3 (`_build_bitmap_font_dictionary`).
- **Emoji**: COLR (v70) and raster emoji (`draw/text.py:draw_emojis`).

---

## 6. Performance characteristics, pain points, test suite

### 6.1 Structural costs (from code)

1. **No streaming, everything in memory.** `layout_document` materialises all pages
   (`pages = list(make_all_pages(...))`) before yielding margin boxes. `Document.pages`
   holds every page's full box tree. pydyf holds every PDF object until `PDF.write()`.
   Fonts are subset only at the end, because the full glyph set must be known first.
   Memory grows linearly with document size, plus Pango layouts kept on every `TextBox`.
   Related GitHub issue titles: #1104 "WeasyPrint consuming a lot of memory when rendering
   tables with 5000 rows" (closed), #1950 "Memory heavy to render a 900kB pdf" (closed),
   #578 "Performance issue on long documents" (**open since 2018**).
2. **Re-layout loops.** Any body-content use of `counter(page)`, `counter(pages)` or
   `target-counter(..., page)` can trigger re-making pages from the changed index onward,
   up to 8 full loops. `parse_again` mutates the source box tree, so the source tree is not
   immutable across passes.
3. **Backtracking re-layout.** `break-inside: avoid`, `orphans`/`widows` and
   `break-*: avoid` abort subtrees. The parent re-lays the subtree out on the next page from
   scratch, with no caching of measured fragments. The border/padding overflow case lays the
   child out twice (`block.py:154-166`). Multicol balancing loops re-lay out content.
4. **Intrinsic sizes are not cached** except for tables (`context.tables`). `preferred.py`
   recomputes min/max-content by shaping text through Pango each time, used for tables,
   floats, inline-blocks, flex and margin boxes. Table auto layout on multi-page tables is
   the documented slow path (`docs/common_use_cases.rst:580`: "Tables are known to be slow,
   especially when they are rendered on multiple pages").
5. **Cascade cost.** Selector matching runs for every element against every sheet
   (`sheet.matcher.match(element)`). The docs warn that large CSS frameworks "drastically"
   slow things down (`docs/common_use_cases.rst:577-579`). v70 added computed-style sharing.
6. **Text.** One `PangoContext` and `PangoLayout` are created per text fragment
   (`Layout.setup` calls `pango_font_map_create_context` each time). Shaping happens
   repeatedly during line fitting: prefix, then whole text, then hyphenation retries.
   Pango/fontconfig startup also adds cold-start cost; fontconfig scans system fonts unless
   cached. **UNVERIFIED**: no numbers measured here; WeasyPerf
   (https://kozea.github.io/WeasyPerf/) tracks time and memory per version.
7. **Floats.** `context.excluded_shapes` is a flat list per BFC, scanned linearly by
   `avoid_collisions` for each line or box.
8. **Security docs** (`docs/first_steps.rst:555-600`) recommend external time and memory
   limits (uWSGI harakiri, ulimit) because "even small documents may lead to really long
   rendering times". The engine has no internal caps.
9. Other title-only signals: #2336 "Long rendering times when grid items span" (open),
   #1642/#1689 slow multicol (closed), #1444 raster image perf regression (closed).
   External write-ups repeat the "tables are slow; use `table-layout: fixed`" advice
   ([sysreptor debugging docs](https://docs.sysreptor.com/designer/debugging)), and an Odoo
   thread reported wkhtmltopdf much faster on a ~2,250-page report
   ([odoo-community.org](https://odoo-community.org/groups/contributors-15/contributors-120063))
   (anecdotal).

### 6.2 Determinism (relevant to recto)

- The PDF `/ID` is md5 of the serialized content when `pdf_identifier=True`
  (`pydyf/__init__.py:612-617, 646-653`). Otherwise there is no `/ID`.
- The `CreationDate`/`ModDate` are only set from HTML `<meta>` (`pdf/__init__.py:266-271`);
  there is no wall-clock timestamp.
- Font subset tags are md5-derived. The `Producer` string embeds the version.
- So WeasyPrint output is deterministic **for a fixed system font set and library
  versions**. The main non-determinism source is fontconfig/system fonts, plus
  Pango/HarfBuzz versions changing glyph positions.

### 6.3 Test suite organisation (`tests/`)

- **Unit and layout tests** (`tests/layout/test_*.py`, `tests/test_boxes.py`,
  `tests/css/*`):
  - `render_pages(html)` (`tests/testing_utils.py:191`) returns `PageBox` trees.
  - Tests assert structure and used geometry directly, e.g.
    `html, = page.children; body, = html.children; assert div.position_y == ...`.
  - `parse()` / `parse_all()` test box-tree construction; `assert_tree` compares serialized
    trees; `_sanity_checks` validates the anonymous-box invariants.
  - `@assert_no_logs` makes any logged warning fail the test.
- **Pixel tests** (`tests/draw/*.py`, plus `tests/draw/svg`):
  - `assert_pixels(expected_ascii, html)` (`tests/draw/__init__.py:51`): the expected image
    is an ASCII grid where each char maps to an RGB value via `PIXELS_BY_CHAR`
    (`_` white, `R` red, `B` blue, `G` lime, `z` = don't care, ...).
  - HTML is written to PDF with `zoom=4/30`, then rasterized by **Ghostscript**
    (`gs -sDEVICE=png16m -r{96/zoom}`) in `tests/conftest.py:document_write_png`, so one CSS
    px is one output pixel. Multi-page output is stacked vertically.
  - Pages are tiny (`@page { size: 10px 4px }`).
  - Also available: `assert_same_renderings`, `assert_different_renderings`,
    `assert_pixels_equal(tolerance=...)`. Failures write `tests/draw/results/<name>.png` and
    `.expected.png`.
- **Test fonts**: `tests/resources/weasyprint.otf` (an Ahem-like font with deterministic
  metrics) is loaded by `tests_ua.css` (`@font-face { src: url(weasyprint.otf); font-family: weasyprint }`),
  which is a minimal UA sheet that sets `orphans: 1; widows: 1` so tests are not affected by
  defaults.
- **Others**: `test_api.py` (CLI and Python API), `test_pdf.py` (PDF structure, PDF/A/UA
  flags), `test_fonts.py`, `test_text.py`, `test_unicode.py`, `test_acid2.py`,
  `test_stacking.py`. 1701 test functions in total.

---

## 7. Lessons for recto

### Copy

1. **The fragment-and-resume contract.** Every layout function takes `(box, available
   block space, break token, page_is_empty)` and returns `(fragment | None, break token |
   None, forced-break info, carried margins)`. The **`page_is_empty` progress guarantee** is
   what makes pagination terminate. Keep the `None` = "abort, try earlier break" signal for
   avoid-break backtracking.
2. **Break tokens as paths with byte offsets for text** and multi-entry tokens for parallel
   flows (table cells, later flex lines/grid rows). Store a `resume_at` on every laid-out
   line so orphans/widows backtracking (`find_earlier_page_break`) needs no re-layout.
3. **Class A break resolution** by walking the first/last descendant chains
   (`_add_break_values`) and the priority table in `block_level_page_break`. Also
   page-name propagation via `page_values()`.
4. **Margin boxes laid out after body pagination is final**, from a snapshot of page
   counter state. `counter(pages)` in headers and footers then costs nothing extra. Copy
   `compute_variable_dimension` and `compute_fixed_dimension` almost verbatim; they are
   small, spec-traceable and tested (`tests/layout/test_page.py`, 57 tests).
5. **Repeated thead/tfoot by re-laying out header and footer per fragment**, with the
   drop-footer, drop-header, drop-both fallback ladder. Cache table column widths per table
   across fragments.
6. **Footnote area as a page-bottom box that shrinks `page_bottom`**, with explicit
   report-to-next-page and `footnote-policy`.
7. **Lazy computed styles and style sharing.** Compute on first access, or eagerly but
   share `Arc`s keyed by (parent style, matched rules, inline style).
8. **Leader alignment from the right edge** so dot columns line up.
9. **Deterministic naming**: md5/sha-derived font subset tags, content-hash `/ID`, no
   wall-clock dates unless provided.
10. **The `assert_pixels` ASCII-grid test style**, with a tiny `@page` size, 1 CSS px =
    1 device px, an Ahem-like test font, and fail-on-warning. For recto, replace
    Ghostscript (AGPL) with an in-tree rasterizer of our own PDF output (or a pure-Rust
    renderer such as hayro/pdf-render, to be evaluated separately) so tests have no system
    dependencies.

### Do differently

1. **Streaming page emission.** WeasyPrint's fixpoint loop re-makes pages arbitrarily
   late, which rules out streaming. Proposed recto design:
   - **Pre-pass** that, without layout, collects which counters each content item needs
     (WeasyPrint's `missing_counters` / `missing_target_counters` are exactly this
     analysis).
   - **Classify documents**:
     - No body-level page-dependent content: single pass, stream each page as soon as it
       is laid out, with footers resolved at emission time. `counter(pages)` in margin
       boxes still needs the total. Either emit page content streams immediately and the
       footer content stream (a separate content stream or Form XObject per page)
       **after** the total is known (PDF allows multiple `/Contents` streams per page and
       late objects), or lay out margin boxes at the end.
     - Body content with backward refs only (`target-counter` to earlier anchors): still
       streaming.
     - Forward page refs (TOC): two-pass. Pass 1 lays out with **width-stable
       placeholders** (reserve the max digit width of the final value class), records
       anchor pages, then re-lays out only pages whose referencing text changed width. In
       the common case, page numbers in a TOC do not change line breaking when using
       tabular figures. Cap iterations and **report** non-convergence, unlike
       WeasyPrint's silent 8-loop cap.
   - Keep only the **break token + counter/page state** per page boundary (WeasyPrint's
     `page_maker` tuple), not the page box trees. That snapshot is sufficient to resume or
     re-make from any page.
2. **Immutable source tree; no `parse_again` mutation.** Generated content that depends
   on page counters should be a deferred node resolved at fragment time (input to layout),
   not a mutation of the shared box tree. This also makes parallel or incremental layout
   possible.
3. **Make the side-effect ledger structural.** Instead of `remove_placeholders` undoing
   abspos lists, footnotes, floats, running elements and broken out-of-flow, collect those
   side effects in the returned fragment (or in a transactional per-page arena with
   checkpoints/rollback). Backtracking then drops the fragment and its effects at once.
   This bug class is the source of many WeasyPrint fixes (#2714, #2815, #2828, #2853 in v70
   alone).
4. **Typed lengths, not `'auto'` strings / floats.** Use fixed-point layout units
   (Blink-style 1/64 px or app units) for deterministic cross-platform results and no
   `1e-9` epsilons.
5. **Own font stack, no fontconfig.** Use a static binary with bundled default fonts plus
   user-provided directories, CSS Fonts §5 matching, and an explicit, deterministic
   fallback list. WeasyPrint's dependence on system fontconfig and temp files breaks
   `scratch` images and determinism. Shape with rustybuzz/harfrust and subset in-process.
   Keep CID-keyed fonts with ToUnicode, but build ToUnicode from cluster mapping and handle
   ligatures (1 glyph → n chars) and repeated glyphs with different chars via `ActualText`.
6. **Shape once, break many times.** Shape each paragraph's text run once into a glyph
   buffer with UAX#14 break opportunities and per-break advance sums (the Blink
   `NGInlineItem`/`ShapeResult` model). Line fitting is then arithmetic plus local reshape
   at the break, instead of WeasyPrint's repeated Pango layouts of prefixes and
   hyphenation candidates. Cache intrinsic min/max-content sizes per (box, style) because
   tables and flex call them heavily.
7. **Hyphenation**: embed compiled Liang patterns (hyphenation crate / typst-hyphenate,
   evaluated elsewhere), gated by `lang` like WeasyPrint/Pyphen.
8. **Tagging per element, not per fragment.** `pdf/tags.py:_build_box_tree` runs per page
   and creates a new `StructElem` per box **fragment**, so a paragraph split over two pages
   becomes two `/P` elements. Margin-box content is mapped but unlinked. recto should keep
   one StructElem per element with marked-content refs across pages (`/K` array of MCRs
   with `/Pg`), emit margin boxes and running headers as `/Artifact` (`/Pagination`
   subtype), and stream the struct tree incrementally: write StructElems for finished
   subtrees and the ParentTree at the end.
9. **PDF writer**: stream objects to the output as pages finish (xref offsets recorded as
   written). Defer only fonts (subset at end), the struct tree root and ParentTree, the
   outlines, and `/Pages`. pydyf's all-in-memory `PDF.objects` model is the opposite.
10. **Resource limits inside the engine**: max pages, max loops, max boxes, max
    nesting, per-document time budget, and a byte budget for images. WeasyPrint delegates
    all of these to the OS.
11. **Background slicing for `box-decoration-break: slice`**: paint backgrounds and
    border-images against the unfragmented box geometry, clipped per fragment. WeasyPrint
    repeats them. Cheap if fragments keep a "virtual full box" offset.
12. **Margin-box content overflow**: WeasyPrint asserts no fragmentation and lets it
    overflow. recto should do the same but warn.

---

## Findings that affect recto's design

1. Adopt the **(fragment, break token, next_page, carried margins, collapsed-through)** layout
   return contract plus a `page_is_empty` progress flag. This is the backbone of
   WeasyPrint's fragmentation and is proven on a large spec surface (`block.py:block_container_layout`).
2. Model break tokens as **index paths + UTF-8 byte offsets + multi-child tokens** for
   parallel flows (`table.py:197-200`), and store a break token on every line box.
3. `avoid` breaks are implemented by **abort-and-propagate** (`None` up the stack) plus
   `find_earlier_page_break` over already-built fragments. recto needs the same, with a
   transactional side-effect ledger instead of manual `remove_placeholders`.
4. Per page boundary, persist only `(break token, next_page, side, counter state, page
   groups)`. This is the `page_maker` tuple and it is enough to resume or re-make any page,
   so it enables streaming with bounded memory.
5. Lay out **margin boxes after** body pagination from snapshotted counters. `counter(pages)`
   in headers and footers then needs no body re-layout, only late emission of margin-box
   content streams.
6. **Forward page references** (TOCs) require a second pass. Do static dependency analysis
   (`missing_counters` / `missing_target_counters`), re-lay out only dirty pages, reserve
   stable widths, and **error or warn on non-convergence** instead of a silent 8-loop cap.
7. Repeated `thead`/`tfoot`: re-lay out per fragment with the drop-footer/drop-header
   fallback, and never break right after a header or before a footer.
8. Footnotes: page-bottom area that reduces available block size, with report-to-next-page
   and `footnote-policy` semantics; reported footnotes go first on the next page.
9. Margin-box sizing algorithm (`page.py:compute_variable_dimension`/`compute_fixed_dimension`)
   is directly portable and needs min/max-content of margin box content.
10. Running elements: register out-of-flow per page, resolve with
    first/start/last/first-except, deep-copy into the margin box as `position: relative`,
    and re-substitute page counters inside.
11. Avoid every system dependency WeasyPrint has (Pango, HarfBuzz .so, fontconfig, temp
    font files, Ghostscript in tests). Fontconfig fallback is WeasyPrint's main
    non-determinism source.
12. Shape once per paragraph and cache intrinsic sizes. WeasyPrint's documented slow paths
    (multi-page auto tables, large cascades, multicol balancing) come from repeated
    shaping and uncached measurement.
13. Tagging must be **per element across fragments**, with margin content as `/Artifact`.
    WeasyPrint's per-fragment StructElems are a PDF/UA quality gap.
14. Determinism techniques to copy: hash-derived subset tags, content-hash `/ID`, no
    implicit timestamps. Go further with fixed-point units and bundled fonts.
15. Test harness: ASCII pixel grids at 1 px = 1 CSS px, an Ahem-like test font, and
    fail-on-warning. Use an in-repo rasterizer instead of Ghostscript (AGPL).

## Recommendation

Use WeasyPrint as the **behavioural and algorithmic reference** for paged-media semantics.
Port its algorithms (page.py margin boxes, break-value resolution, orphans/widows,
table header/footer repetition, footnote area, page selectors with groups, target/counter
lookup bookkeeping) and its test cases. `tests/layout/test_page.py`, `test_table.py`,
`test_footnotes.py`, `tests/draw/test_page.py` and `tests/css/test_pages.py` are
high-value fixtures to translate into recto's test format; the license is BSD-3, so tests
can be adapted with attribution. **Do not** copy its global architecture:

- mutable shared box tree with `parse_again`;
- all-pages-in-memory fixpoint loop;
- manual side-effect rollback;
- Pango/fontconfig;
- whole-document PDF object graph.

Replace them with an immutable box tree, transactional per-page layout, a page-boundary
state snapshot, dependency-driven targeted re-layout, and a streaming PDF writer.

## Open questions / UNVERIFIED items

- Content of WeasyPrint issue #93 ("known limitations" of page-based counters) and #578.
  Only titles and docs references were seen; issue bodies were not accessible
  (GitHub MCP restricted to this repo; WebFetch blocked).
- No runtime measurements were taken: WeasyPrint was not executed (system Pango/HarfBuzz not
  installed here), so all performance statements come from code reading, docs and issue
  titles. Numbers would need a benchmark harness in a later phase.
- Exact UA rule feeding the internal `anchor` property (from `id`/`name`): not checked in
  `css/html5_ua.css`.
- `revert`/`revert-layer`, `position: sticky`, `conic-gradient()`, `page-orientation`
  support status not verified in code.
- `element(start)` behaviour: the docs say unsupported, but the code has a `start` branch
  (`layout/__init__.py:get_string_or_element_for`). The semantics look approximate
  (first-descendant chain only).
- Docs vs code discrepancies on `quotes` (implemented in code) and `text-indent` (property
  exists) were noted. Which sub-features the docs mean was not confirmed.
- pydyf was inspected at `main` (`58e2a6d`, version string 0.13.0), not at the exact
  version pinned by a WeasyPrint release (`pydyf >=0.11.0`).
