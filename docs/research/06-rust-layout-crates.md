# 06 — Rust layout crates, taffy, and fragmentation strategy

Date: 2026-10-14 · Topic slug: `layout` · Author: Phase-0 research agent

Scope: Can recto build its layout on `taffy`, or does it need its own fragmentation-aware engine?
Evidence comes from source clones under `/tmp/claude-0/src/layout/`. Path references are
relative to each repo root unless noted otherwise.

## Sources inspected

| Name | Version / tag | Commit SHA (inspected) | License | Last commit | Maintenance assessment |
|---|---|---|---|---|---|
| `taffy` (DioxusLabs/taffy) | **0.15.0** (latest on sparse index; MSRV 1.71). **No `v0.15.0` git tag exists yet.** Inspected the release-prep commit "Prepare for v0.15 release (#1302)", whose `Cargo.toml` says `version = "0.15.0"` | `eb6450694f33e2b7413e40677f230ff63f0fc194` (2026-10-12). `main` HEAD is `6c2106e3` (2026-10-13), which Blitz pins | MIT | 2026-10-13 | Very active: 239 commits in the last 12 months, 100 of them in Aug 2026. Releases 0.10 (2026-03-31), 0.11 (06-12), 0.12 (07-03), 0.13 (08-08), 0.14 (08-24), 0.15 (~10-12). **Every minor release is BREAKING.** Bus factor ≈1: Nico Burns made 204 of the ~230 non-bot commits since 2025-10 |
| `parley` (linebender/parley) | v0.12.0 (latest on index; MSRV 1.88) | `6e1143dda817360dd3a2a64f9133c6e5dfabd881` (2026-10-09) | Apache-2.0 OR MIT | 2026-10-09 | Active (covered in depth by the text research doc; here only its line-breaker API) |
| `blitz` (DioxusLabs/blitz) | workspace `0.3.0-beta.3` (blitz-dom 0.3.0-beta.3 on index, MSRV 1.91) | `e72650a6e67941852fddf025295cfee30c39ea32` (HEAD, 2026-10-14) | MIT OR Apache-2.0 | 2026-10-14 | Active, pre-1.0, beta. Pins taffy by git rev `6c2106e3` (`Cargo.toml:101`); the published blitz-dom requires `taffy ^0.15` |
| `servo` `components/layout` | `servo-layout` (workspace version) | `777877f5f62a4866d6c40d683fc9510e609545a5` (HEAD, 2026-10-14) | MPL-2.0 | 2026-10-14 | Very active, browser engine. Uses `taffy 0.14.0` with features `grid` only (`Cargo.toml:254` of the workspace) |
| `typst` `crates/typst-layout` | **v0.15.1** (typst-layout 0.15.1 latest on index; MSRV 1.92) | `9dfd3a08500b7896045f907433cf7b4b02434fad` (tag v0.15.1, 2026-07-17) | Apache-2.0 | 2026-07-17 (tag) | Mature, commercial backing |
| `fulgur` (fulgur-rs/fulgur) | 0.40.0 (index) | `8477bfe9417731d9f2155eca97664d53c879ff6d` (HEAD, 2026-10-14) | MIT OR Apache-2.0 | 2026-10-14 | Very active, young (created ~2026-03). Direct competitor: Blitz + Parley + Krilla HTML→PDF. Pinned on **blitz-dom 0.2 / taffy 0.9 / parley 0.6** (`crates/fulgur-blitz/Cargo.toml:30-34`), so it is 6 taffy minors behind |
| `azul` `layout` (`azul-layout`, used by `printpdf` 0.12.8's HTML mode) | azul-layout 0.0.16 | `fbb9bff2b9fb4ffb44ff0c26f1633a569f4a6a45` (2026-10-08) | MIT | 2026-10-08 | Active, single maintainer. Uses `taffy ^0.10` for flex/grid only |
| CSS specs (w3c/csswg-drafts) | css-break-3, css-flexbox-1, css-tables-3 `Overview.bs` | `1c249b342ee7a0dfe0fcf7f7dc75272b1e794d52` (2026-10-14) | W3C | — | Editor's drafts |

Other Rust HTML→PDF crates found by WebSearch. I checked only their versions on the sparse index and read **no source**, so their architecture is UNVERIFIED: `ironpress` 1.7.0 (no taffy dep), `fullbleed` 2.5.22, and `ferropdf` (Python/PyPI; not on the crates.io index under that name). Sources: [fulgur docs.rs](https://docs.rs/crate/fulgur/0.2.0), [ironpress docs.rs](https://docs.rs/ironpress), [fullbleed docs.rs](https://docs.rs/crate/fullbleed/1.6.2), [ferropdf PyPI](https://pypi.org/project/ferropdf/), [printpdf](https://docsearch.algolia.com/mcp/docs/repo/fschutt/printpdf), [RUSTSEC-2026-0201 (fulgur blank-page amplification DoS)](https://osv.dev/vulnerability/RUSTSEC-2026-0201).

---

## 1. Taffy 0.15.0: architecture and what it implements

### 1.1 Crate shape, features, footprint

- `Cargo.toml` (at `eb645069`): `edition = "2021"`, `rust-version = "1.71"`, `license = "MIT"`.
- All dependencies are **optional**: `slotmap` (only for the `taffy_tree` feature, i.e. the built-in `TaffyTree`), `smallvec` (`grid`), `serde`, `cssparser` (`parse`), and `document-features`. `roxmltree` and `serde_json` are dev-deps only (the sparse index shows `kind: dev`).
  - With `default-features = false, features = ["std", "block_layout", "float_layout", "flexbox", "grid", "calc", "content_size"]` the only transitive dependency is `smallvec`. The footprint is negligible.
- Default features: `std, taffy_tree, flexbox, flexbox_balance, grid, block_layout, float_layout, calc, content_size, detailed_layout_info`.
  - `float_layout` is new and documented as a "sub-feature of block layout".
  - The no-alloc mode was removed in 0.15 (CHANGELOG "No-alloc support has been removed").
- Size: `src/` is ~29.6k lines including inline tests.
  - `compute/flexbox.rs` 3460, `compute/block.rs` 1824, `compute/float.rs` 797, `compute/oof.rs` 912, `compute/leaf.rs` 188.
  - `compute/grid/**` ≈ 8.1k. `style/**` ≈ 7k.
- `unsafe`: 43 occurrences. Most are in `style/alignment.rs` and `style/dimension.rs`; `style/compact_length.rs` does pointer tagging of `calc()` values.
  - `LayoutPartialTree::resolve_calc_value(&self, val: *const (), basis: f32)` (`tree/traits.rs:193`) means calc values are passed as raw tagged pointers.
  - Blitz has to keep the backing storage alive manually (`blitz-dom/src/layout/table.rs`, `TableContext::calc_values`, with the comment "Taffy stores calc values as raw pointers").
- Numeric type: **`f32` throughout** (`geometry.rs`, `LayoutOutput.size: Size<f32>`).
  - Servo bridges to its `Au` app units (`components/layout/taffy/layout.rs`, `Au::from_f32_px` / `to_f32_px`). Typst uses its own `Abs(Scalar)` (`typst-library/src/layout/abs.rs:12`, f64).
  - There are no `HashMap`s in taffy's non-test code (the only `rand` is a test closure in `flexbox.rs:3417`), so output is deterministic for a fixed binary.

### 1.2 The low-level trait API (`src/tree/traits.rs`)

Taffy works through traits. The host owns the tree; taffy algorithms see **one container and its direct children**.

| Trait | Methods | Role |
|---|---|---|
| `TraversePartialTree` (l.147) | `child_ids`, `child_count`, `get_child_id` | Child iteration of one node |
| `TraverseTree` (l.167) | marker | Promises full recursive access (needed by `RoundTree`, `PrintTree`) |
| `LayoutPartialTree` (l.173) | `get_core_container_style`, `resolve_calc_value`, `set_unrounded_layout(node, &Layout)`, **`compute_child_layout(node, LayoutInput) -> LayoutOutput`** | The central hook. Taffy algorithms call `compute_child_layout` for every child. **The host dispatches on display type**, so any custom layout mode plugs in here |
| `LayoutContainingBlock` (l.212) | `get_oof_item_style`, `clear_hoisted_children`, `add_hoisted_children`, `get_detailed_layout_info` | New in 0.15: abspos/fixed hoisting to the containing block (`compute_oof_layout`) |
| `CacheTree` (l.260) | `cache_get`, `cache_store`, `cache_clear` | Per-node cache keyed by `LayoutInput`. `tree/cache.rs:11` `CACHE_SIZE = 9` measure slots |
| `RoundTree` (l.275) | `get_unrounded_layout`, `set_final_layout`, `is_out_of_flow`, `hoisted_child_count`, `get_hoisted_child_id` | Pixel snapping (`round_layout`). Not wanted for PDF |
| `LayoutFlexboxContainer` (l.307) | `get_flexbox_container_style`, `get_flexbox_child_style` | Style getters returning trait objects (`FlexboxContainerStyle`, `FlexboxItemStyle`) |
| `LayoutGridContainer` (l.328) | `get_grid_container_style`, `get_grid_child_style`, `set_detailed_grid_info` | Same for grid. `DetailedGridInfo` exposes track sizes and item areas |
| `LayoutBlockContainer` (l.358) | `get_block_container_style`, `get_block_child_style`, **`compute_block_child_layout(node, inputs, Option<&mut BlockContext>)`** | Lets a child in the same BFC receive the BFC's float context. This is how a host-side inline layout can avoid floats |

Style is accessed through getter traits (`CoreStyle`, `BlockContainerStyle`, `BlockItemStyle`, `FlexboxContainerStyle`, `GridItemStyle`, …), so recto's computed-style struct can implement them directly and no `taffy::Style` copy is needed. Servo, Blitz (`stylo_taffy`) and Azul all do this.

Entry points (`compute/mod.rs`): `compute_root_layout`, `compute_block_layout(tree, node, inputs, Option<&mut BlockContext>)`, `compute_flexbox_layout`, `compute_grid_layout`, `compute_leaf_layout(inputs, &style, calc, measure_fn)`, `compute_hidden_layout`, `compute_cached_layout`, `compute_oof_layout` / `compute_oof_layout_for_area`, and `round_layout`.

### 1.3 `LayoutInput` / `LayoutOutput` (`src/tree/layout.rs`)

```rust
pub enum RunMode { PerformLayout, ComputeSize, PerformHiddenLayout }        // l.12
pub enum SizingMode { ContentSize, InherentSize }                           // l.25
pub struct CollapsibleMarginSet { positive: f32, negative: f32 }           // l.35  (max positive + min negative)
pub struct LayoutInput {                                                   // l.125
    run_mode, sizing_mode, axis: RequestedAxis,
    known_dimensions: Size<Option<f32>>,
    known_dimensions_are_definite: Size<bool>,
    parent_size: Size<Option<f32>>,          // percentage basis
    available_space: Size<AvailableSpace>,   // Definite(f32) | MinContent | MaxContent
    vertical_margins_are_collapsible: Line<bool>,
}
pub struct LayoutOutput {                                                  // l.472
    size: Size<f32>, scrollable_overflow_rect, baselines: Baselines{first,last},
    top_margin: CollapsibleMarginSet, bottom_margin: CollapsibleMarginSet,
    margins_can_collapse_through: bool,
    oof_candidates: OofCandidates, oof_positioning_area: Option<OofPositioningArea>,
}
```

Notes:
- The contract is **one box in, one box out**. A node has exactly one `Layout { location, size, … }` (`layout.rs:579`).
  - Nothing represents "the part of this box that fits", a continuation, or a resumption point.
  - `LayoutInput::transpose()` exists for vertical writing modes.

### 1.4 Layout modes implemented

`Display` (`style/mod.rs:251`) is `Block | FlowRoot | Flex | Grid | None`. There is **no `Inline`, `InlineBlock`, `Table*`, `ListItem`, `Contents`, or multicol**.

| Feature | Status in taffy 0.15.0 | Evidence |
|---|---|---|
| Flexbox (CSS Flexbox 1, §9 algorithm), incl. `flex-wrap: balance` / `flex-line-count` (Flexbox 2) | Implemented | `compute/flexbox.rs` (steps 9.1–9.6 marked in comments l.342–535); `collect_balanced_flex_lines` l.1271 |
| Grid (track sizing, placement, named areas, auto-fit collapsed tracks, subgrid?) | Implemented. Subgrid: no `subgrid` found in the style enums; **UNVERIFIED** whether partially supported | `compute/grid/*` |
| Block flow (block-level children only) | Implemented | `compute/block.rs:1` doc: "Computes the CSS block layout algorithm in the case that the block container being laid out contains **only block-level boxes**" |
| Inline formatting context / line boxes / text | **Not implemented.** Text is a leaf via a measure closure, or host-side inline layout. `compute_block_align_content_offset` is exported "for inline formatting contexts (line boxes) which are laid out externally to Taffy" (`block.rs:28-37`) | `compute/leaf.rs:20`; Blitz `layout/inline.rs` |
| Floats (left/right), float placement, shrink-wrapping beside floats | Implemented (new; feature `float_layout`). `FloatContext::place_floated_box`, `find_content_slot` (line-box slot beside floats), `find_bfc_slot` (BFC roots avoid floats), `FloatIntrinsicWidthCalculator` | `compute/float.rs:211-797`, `block.rs:167-232` |
| `clear` + clearance (CSS2.2 §9.5.2), including forced clearance for floats adjoining an unresolved margin strut | Implemented | `block.rs:1514-1554` ("Compute clearance (CSS2.2 9.5.2)"), `has_adjoining_float` l.232 |
| Margin collapsing | Implemented: sibling margins, parent/first-child top, parent/last-child bottom (only if `height` auto and not constrained by `min-height`, l.672 "CSS2 §8.3.1"), collapse-through of empty blocks based on *used* height (l.746), clearance stops collapsing (l.1757-1798), no collapsing across BFC roots (`vertical_margins_are_collapsible`) | `block.rs` `compute_inner`, `perform_final_layout_on_in_flow_children` |
| BFC establishment | `overflow` scroll container, `display: flow-root`, non-`normal` `align-content`, `contain: layout/paint`; floats, abspos, tables and non-block children always lay out as independent | `block.rs:385-391`, `generate_item_list` l.912 `is_in_same_bfc` |
| Floats inside **inline** content | Delegated to host: Blitz calls `place_floated_box` / `find_content_slot` from Parley's breaker loop | Blitz `layout/inline.rs:676-780` |
| `display: table` | **Not implemented.** `BlockItemStyle::is_table()` only disables stretch-fit width for table children of blocks (`style/block.rs`). Blitz emulates tables by mapping them to a grid (`TableTreeWrapper` + `compute_grid_layout`, `blitz-dom/src/layout/mod.rs:538`); there is no `border-collapse` (fulgur `docs/css-support.md`: "Taffy has no table layout algorithm") | |
| Absolute / fixed positioning | Implemented in 0.15: hoisting to containing block, static position, `align-self`/`justify-self` for abspos. `position: sticky` = static | CHANGELOG 0.15, `compute/oof.rs` |
| Multicol, regions, pages, fragmentation | **None** | `grep -i "fragment\|page\|break-"` over `src/` finds only grid "auto-repeated fragment" and flex `line_break_size`. No break tokens or fragmentainer anywhere |
| Writing modes | Host-side transpose only (`LayoutInput::transpose`) | `layout.rs:187` |
| Known TODOs | `block.rs:1093` "TODO: handle nested blocks with different widths"; `block.rs:1437` "TODO: account for auto margins"; `block.rs:1565/1604` "TODO: handle inset and margins"; `float.rs:427,470` | |

### 1.5 How a host plugs in leaves and custom modes

1. **Leaf measurement (text, images).** Call `compute_leaf_layout(inputs, &style, calc, |known_dims, avail| -> Size<f32>)` inside `compute_child_layout`.
   - Taffy applies padding, border, `box-sizing`, `aspect-ratio`, and min/max around the closure (`compute/leaf.rs:20-60`).
   - The example dispatcher is `examples/custom_tree_vec.rs:163-201`.
2. **Custom layout modes** (tables, inline, multicol, anything else). Taffy has no registry; the host's `compute_child_layout` simply `match`es on its own node kind and calls its own function, which returns a `LayoutOutput`. Blitz does exactly that (`blitz-dom/src/layout/mod.rs`):
   - inline roots go to `self.compute_inline_layout(...)`;
   - table roots go to `compute_grid_layout(&mut TableTreeWrapper{..})`;
   - otherwise `Display::Block => compute_block_layout(self, id, inputs, block_ctx)`, `Flex => compute_flexbox_layout`, `Grid => compute_grid_layout`.
3. **Inline content inside block flow.** The host must wrap runs of inline content in an anonymous "inline root" node.
   - `CoreStyle::is_block()` must be true only for `display: block` (`style/mod.rs:86-92`).
   - The host implements `LayoutBlockContainer::compute_block_child_layout` to receive the parent's `BlockContext` and then lays out lines around floats.
   - Blitz does this with Parley's resumable breaker (`break_lines()` / `break_next()` → `YieldData::{LineBreak, InlineBoxBreak, MaxHeightExceeded}`; `parley/src/layout/line_break.rs:531, 972-1028`).
4. **Intrinsic sizing.** Taffy asks children for sizes with `RunMode::ComputeSize` and `AvailableSpace::{MinContent, MaxContent}`. The host must answer these queries for its custom modes too. Caching uses the same `LayoutInput` key.
5. **Wrapping trick for per-feature interception.** fulgur wraps Blitz's `BaseDocument` in its own `LayoutPartialTree` that forwards everything except the nodes it wants to own: multicol (`crates/fulgur-blitz/src/multicol_layout.rs`) and pagination (`pagination_layout.rs`). Servo goes the other way: it owns the layout and implements `LayoutPartialTree` only for grid containers, with `compute_child_layout` calling back into Servo's own layout for grid items (`components/layout/taffy/layout.rs:90-230`).

---

## 2. Can taffy be driven for page fragmentation?

### 2.1 Verified: no fragmentainer concept

- The `LayoutInput` fields (§1.3) contain no fragmentainer block-offset, no remaining extent, and no break token.
- `LayoutOutput` returns one size and one set of margins per box. There is no "consumed block size", no break-before/after propagation, and no "fits / does not fit" signal.
- **`available_space.height` is ignored for breaking.** In block layout, children always get `available_space.height = AvailableSpace::MaxContent` (`compute/block.rs:1090-1091`), with the comment that vertical available space "in block flow is indefinite". A page-height constraint passed at the root therefore never reaches descendants.
  - fulgur confirmed this experimentally. Spike `fulgur-ik6o` (`fulgur/docs/plans/2026-04-28-pagination-layout-spike.md`, §"per-strip available_space constraint experiment"):
    > "All 10 comparison fixtures produced identical page counts under `StripMode::MaxContent` and `StripMode::Definite(page_height_px)` … Taffy's block layout does not use `available_space.height` to drive mid-element splitting … This rules out the 'free fragmentation by constraining available_space' hypothesis."
- Flexbox and grid size items against an indefinite or definite container height. Neither can split an item, line or row.

### 2.2 What CSS requires (it is more than slicing)

From `css-break-3/Overview.bs`:
- §"Breaking into Varying-size Fragmentainers" (l.863): "Layout is performed **per-fragmentainer**, with each fragmentainer continuing progress from the breakpoint on the previous, but **recalculating sizes and positions using its own size**."
  - It also says: "Intrinsic sizes are calculated and maintained across the entire element."
  - And: "fragments must not be positioned above the block-start edge of the fragmentainer".
- §"Adjoining Margins at Breaks" (l.974): margins adjoining an unforced break are **truncated to zero**. At a forced break, margins after the break are preserved.
- §"Splitting Boxes" (l.988): when a box breaks, its content box **extends to fill the remaining fragmentainer extent**, and that extra size counts toward block-size limits.
- §break-decoration (l.1015): `box-decoration-break: slice | clone`. With `clone`, padding and border are re-applied on each fragment.
- §widows-orphans (l.454) and §best-breaks (l.786): breaks are classed A/B/C, and the spec defines rules for choosing the "best" break (avoid `break-inside: avoid`, honor orphans/widows, fall back to relaxing constraints).
- `css-flexbox-1` §"Fragmenting Flex Layout" (l.4658) and the "Sample Flex Fragmentation Algorithm":
  - Break opportunities exist between flex lines (row containers) or between items (column containers).
  - `break-*` values propagate from items to lines.
  - "Run the flex layout algorithm (without regards to pagination) through Cross Sizing Determination, then lay out as many consecutive items or item fragments as possible … rerun the flex layout algorithm from Line Length Determination through Cross Sizing Determination with the next page's size."
- `css-tables-3` §Fragmentation (l.3264): repeated headers and footers, and the gap layout around them.

### 2.3 Strategy evaluation

#### (a) Lay out on an infinite canvas, then slice by y

This is what fulgur does in production (its `Pageable` tree plus the newer `pagination_layout.rs`, which "walks the body's direct block children's existing `final_layout` — descending into Parley line metrics for inline roots — and records the would-be page geometry", `pagination_layout.rs:1-30`). Azul's older path does it too (`azul/layout/src/solver3/paged_layout.rs:1-11`: "page_index is assigned to nodes DURING layout based on Y position … pages are split afterward by Y position").

Problems, all concrete:

1. **Pushing content moves everything after it.**
   - Pushing a line or a `break-inside: avoid` block to the next page inserts a gap. Every subsequent y must shift, and the shifted layout invalidates every later slice decision.
   - Slicing is therefore an iterative "split-and-shift" pass that re-implements block-flow positioning: margin truncation, float re-positioning, clearance. It does not replace that work.
   - fulgur's `pagination_layout.rs` has grown to **10,559 lines** doing this on top of taffy (its `Pageable` path is separate), and its spike doc lists the parity gaps (`break-*`, widows/orphans, string-set, running elements, bookmarks) as "6–10 issues, each individually non-trivial".
2. **Floats** placed on the canvas sit beside lines that end up on another page. After a shift, float/line overlap changes, but line widths were fixed during the first layout, so text wraps against floats that are no longer there. A correct result needs relayout.
3. **Margins and padding at breaks.**
   - Truncating a margin at an unforced break changes the position of everything below it.
   - `box-decoration-break: clone` adds padding and border per fragment, which changes available height and forces relayout of the remainder.
   - With slicing, padding-bottom lands on the last page only (slice semantics), and the content box does not "extend to fill remaining extent" unless backgrounds are synthesized.
4. **Repeated table headers and footers.** These reduce per-page content height and need extra copies of the header rows. Slicing has to duplicate geometry: fulgur's `PaginationGeometry::is_repeat` (`pagination_layout.rs:100-128`), `fragment_repeating_table` (l.2118). fulgur still cannot fragment nested tables or header bands (`docs/css-support.md`, "Not supported").
5. **Orphans/widows** need line granularity. That works by reading line metrics from Parley (fulgur `fragment_inline_root`, l.3450), but every push shifts all later content (problem 1).
6. **Flex item fragmentation (row flex).** All items on a line break at the same page edge. Each item's content must break at its own line boundaries, and the line's cross size (row height) per page is the max over its items' fragments. With canvas slicing a single y cut goes through all items, which cuts text lines in half unless each item is re-split, and then the items diverge.
7. **Percentage and `vh` heights per page, varying page sizes (named pages, `:first` with different margins), and page-width changes.**
   - The spec requires layout per fragmentainer size. A canvas has one width.
   - Named pages with a different width (e.g. a landscape page) need a full relayout of that segment, which a single canvas cannot express.
   - fulgur F1 notes that `vh` happens to resolve against one page size because the viewport is set to the page size. That only holds for uniform pages.
8. **Abspos with containing block = page, `position: fixed` repeated per page, and `float` page floats.** All need per-page treatment after the fact (fulgur `append_position_fixed_fragments`, l.3778).
9. **Determinism and drift.** fulgur found that re-driving taffy after its first layout "introduces sub-pixel floating-point drift that breaks `examples_determinism`'s byte-wise PDF comparison" (`pagination_layout.rs:15-20`), so it gave up on re-layout and only post-walks.
10. **Streaming.** The whole document must be laid out before page 1 is emitted, and memory is O(document) geometry. This conflicts with recto's streaming-page-emission and 1000-page goals.

Cost: cheap to start (days), with a good page-count match for simple docs. It is asymptotically **the most expensive to make correct**, because it accumulates special cases (fulgur: 10.5k LOC and still "Not supported" for several cases). Not recommended as the architecture. It is acceptable only as a fallback for monolithic content that overflows a page.

#### (b) Wrap taffy and re-run per page with a constrained available height

- Does not work by itself: taffy ignores `available_space.height` for splitting (§2.1, `block.rs:1090`, fulgur-ik6o).
- To make it work you must write the per-page child iteration yourself: decide which children fit, compute their consumed size, and re-issue `compute_child_layout` for the remainder with modified styles (e.g. zero top margin, reduced height, `known_dimensions`).
- Every taffy-laid-out descendant that needs to split (a paragraph inside a div inside a flex item) needs the same treatment at every level. You end up reimplementing block layout with a break token, and calling taffy only for leaf-level sizing.
- Taffy's cache is keyed on `LayoutInput` (`tree/cache.rs`, 9 slots), so per-page re-runs with different inputs cause cache thrash.
- Each continuation needs a "start from child k with consumed height h" input that taffy cannot express (no field for it), so the host has to fake it by building synthetic child lists per page.

Cost: high, fragile, and it converges to (c) with worse ergonomics.

#### (c) Own fragmentation-aware block/inline/table layout; taffy only for flex and grid placement

This is what **Servo** (own block/inline/table/flex, taffy for grid only, no fragmentation), **Azul** (own BFC/IFC/table in `solver3/fc.rs`, 13.3k lines, LayoutNG-style `BreakToken`, taffy for flex and grid via `solver3/taffy_bridge.rs:1683-1684, 1914-1915`) and **Blitz** (own inline, table-as-grid; taffy block, flex, grid) do in varying degrees.

- The host's `compute_child_layout` routes flex and grid items back into recto's own engine, as Servo does. Recto controls item contents fully.
- Flex and grid containers are laid out by taffy in an **unfragmented** measuring pass that yields item sizes and positions. Recto then fragments **at the container level**:
  - between flex lines (row flex) or items (column flex);
  - between grid rows;
  - inside items, by re-running recto's own fragmenting layout of an item with the taffy-resolved inline size.
- This matches the spec's informative flex algorithm (§2.2), which explicitly runs the unfragmented flex algorithm through cross sizing first.
- Flex and grid containers that fit on the page, or that have `break-inside: avoid`, are **monolithic**: one taffy call, no fragmentation logic at all. These are the majority in invoices, receipts and tickets (headers, address blocks, totals rows).
- Limitations: taffy's internal step functions are private (`fn determine_flex_base_size`, `fn collect_flex_lines`, …, all non-`pub` in `compute/flexbox.rs`).
  - "Rerun from Line Length Determination with the next page's size" is only possible by calling `compute_flexbox_layout` again with different `known_dimensions`, or by **vendoring** `flexbox.rs` (MIT, 3460 lines) and exposing the steps.
  - Same for grid: per-page row redistribution with `fr` rows in a definite-height grid is rare in documents. Treat it as a monolithic or "rows-as-units" case.
- Cost: block + float + inline + table + abspos + multicol fragmenting layout is real work. Reference sizes:
  - Servo: flow/ 4.9k + inline 8.3k + table 5.1k, without fragmentation.
  - Typst: flow 3.2k + inline 4.6k + grid/table 5.4k, with fragmentation.
  - Azul: `fc.rs` 13.3k.
  - Estimate for recto: 15–25k LOC. Flex and grid are saved (~11k LOC of taffy, well tested against WPT-style fixtures).

#### (d) Write everything ourselves (including flex and grid)

- Maximum control: per-page re-flex, fragmenting grid rows with `fr` redistribution, `f64` or fixed-point units throughout, and no f32↔unit bridging.
- Adds ~4k (flex) + ~8k (grid) LOC plus their test burden. Grid is a v1 stretch goal per the brief.
- Flex in documents is mostly 1-line row containers. A minimal own flex implementation is ~1.5–2.5k LOC (Servo `flexbox/` is 3.3k with full features).
- Worth considering **for flex only, later**, if taffy's API churn or f32 becomes a problem. Grid is the clearest case for reuse.

### 2.4 Cost summary

| Strategy | Initial cost | Cost to correct CSS fragmentation | Streaming pages | Determinism risk | Verdict |
|---|---|---|---|---|---|
| (a) canvas + slice | Low | Very high, open-ended (fulgur 10.5k LOC, still gaps) | No | Medium (drift on re-drive) | Reject as architecture |
| (b) re-run taffy per page | Medium | High, converges to (c) | Partial | Medium | Reject |
| (c) own fragmenting flow + taffy flex/grid | Medium-high | Bounded; flex/grid inner fragmentation approximated | **Yes** | Low (bridge f32 at one boundary) | **Recommend** |
| (d) all own | High | Bounded, best fidelity | Yes | Lowest | Optional later for flex |

---

## 3. Prior art in detail

### 3.1 Servo (`components/layout`, MPL-2.0)

- Layout modules: `flow/` (block + floats + `inline/`), `flexbox/` (own implementation, `flexbox/layout.rs` 2777 lines), `table/` (own, `table/layout.rs` 3154 lines), `taffy/` (grid only: `formatting_contexts.rs:62` `Grid(TaffyContainer)`), `positioned.rs`, `fragment_tree/`.
- "Fragment tree" = the **output geometry tree**, not fragmentation. `fragment_tree/fragment.rs:39` `enum Fragment { LayoutRoot, Box(Arc<BoxFragment>), Float, Positioning, AbsoluteOrFixedPositionedPlaceholder, Text, Image, IFrame }`.
  - A box normally produces one `BoxFragment`. Inline boxes split across lines produce several.
- **No fragmentation, no pagination.** `grep -i "fragmentation|fragmentainer|break_token|paginat"` finds only `layout_root.rs:48` ("Only accept previously known layout roots without fragmentation", which means "has exactly one fragment").
- Block `layout(...)` signatures take `ContainingBlock`, `PositioningContext`, and `Option<&mut SequentialLayoutState>` (float state) (`flow/mod.rs:431-443, 709-717`). There is no block-offset limit and no resume.
- Reusable idea: `CollapsedBlockMargins { collapsed_through, start, end }` (`fragment.rs`), plus the "parallel layout unless floats" switch (`flow/mod.rs:439`: sequential state only `if self.contains_floats || !allow_parallel_layout`).
- The taffy bridge pattern (`taffy/layout.rs:90-230`) is the template for recto's grid integration: an adapter implements `TraversePartialTree`/`LayoutPartialTree` over the grid's children, and `compute_child_layout` calls Servo's own `IndependentFormattingContext` layout and converts `Au`↔`f32`.

### 3.2 Blitz (`packages/blitz-dom`, MIT/Apache)

- Dispatch: `layout/mod.rs` `compute_child_layout_internal`. It routes replaced elements (`compute_replaced_layout`), tables (`is_table_root` → `TableTreeWrapper` → `compute_grid_layout`, l.538), inline roots (`compute_inline_layout`, l.~583), `Block`/`FlowRoot` → `compute_block_layout`, `Flex` → `compute_flexbox_layout`, and `Grid` → `compute_grid_layout`.
  - Text nodes are never laid out individually (l.244-257: "all text nodes should be wrapped in an 'inline layout context'").
- Inline: `layout/inline.rs` (1173 lines) drives Parley's `break_lines()` loop.
  - At each `YieldData::LineBreak` it asks `block_ctx.find_content_slot(min_y, Clear::None, None)` for the next line's x and width beside floats.
  - At `YieldData::InlineBoxBreak` (floats inside inline content) it lays out the float and calls `block_ctx.place_floated_box(...)` (l.676-780).
  - **`YieldData::MaxHeightExceeded(_) => { // TODO }`** (l.714). Parley can stop when a line exceeds `line_max_height` (`parley/src/layout/line_break.rs:71-75, 806`), but Blitz does not use it. That parley hook is a usable primitive for inline fragmentation: stop at the page edge, keep a `BreakerState` (`revert_to`, l.996).
- Tables: emulated as a CSS grid (`table.rs`, `TableContext { cells, rows, columns, border_collapse, … }`). No `border-collapse` (fulgur cites upstream `DioxusLabs/blitz#386`).
- No paged media. Blitz is a screen renderer.

### 3.3 Typst (`crates/typst-layout`, Apache-2.0): regions model

- `Regions<'a>` (`typst-library/src/layout/regions.rs:42`) has these fields:
  - `size` (remaining size of the first region);
  - `expand: Axes<bool>`;
  - `full: Abs` (full height, for relative sizing);
  - `backlog: &'a [Abs]` (heights of the next regions);
  - `last: Option<Abs>` (repeating final region).

  Methods: `next()`, `may_break()`, `may_progress()`, `is_full()`, `iter()`.
  - Doc l.36-40: "All regions within a `Regions` object have the **same width** … not currently possible to … have content wrap to the side of a floating element."
- `Fragment(Vec<Frame>)` (`typst-library/src/layout/fragment.rs:7`) is one frame per region.
- Flow (`flow/mod.rs`): `layout_flow(..., regions, columns, gutter, mode) -> Fragment` (l.191). Its pipeline:
  1. `collect` pre-processes children into `Child::{Tag, Rel, Fr, Line(LineChild), Single(SingleChild), Multi(MultiChild), Placed, Flush, Break}` (`collect.rs:348`).
  2. Loop: `compose(engine, &mut work, &config, …, regions)` per region, then `regions.next()`.
  3. `compose` (`compose.rs:25-35`) handles out-of-flow insertions (top/bottom floats, footnotes) and **reruns** when a float is added (`Stop::Relayout`).
  4. `distribute` (`distribute.rs:14`) fills one region: `line()` checks `regions.size.y.fits(line.need)`, `single()` handles unbreakable blocks, `multi()` handles breakable blocks with spill. Results are `Stop::Finish(forced)` or `Stop::Relayout(scope)`.
  - Resume state is `Work { children: &[Child], spill: Option<MultiSpill>, floats, footnotes, footnote_spill, tags, … }` (`flow/mod.rs:294`). This is a **flow-level cursor**: the index into the children slice plus a spill.
- Widows/orphans: precomputed per line as `LineChild.need` (`collect.rs:193-229`): the height of the line plus the lines that must accompany it. Elegant and cheap.
- Sticky blocks (keep-with-next, e.g. headings) migrate via `DistributionSnapshot` restore (`distribute.rs:32-67`). This is the equivalent of `break-after: avoid`.
- Breakable nested blocks: `MultiChild::layout(engine, regions) -> (Frame, Option<MultiSpill>)` lays the **whole child out into all regions at once** (memoized via `comemo` + `CachedCell`), takes the first frame, and keeps the rest as spill.
  - Typst's own comment (`collect.rs:591-600`): "the whole region juggling here is fundamentally not ideal: It is a **compatibility layer between the old (all regions provided upfront) & new (each region provided on-demand, like an iterator) layout model**. This approach is not 100% correct, as in the old model later regions could have an effect on earlier frames."
  - Lesson for recto: **design on-demand per-fragmentainer resumption (break tokens) from day 1**. Do not hand all regions to a child up front.
- Grid/table fragmentation with repeating headers/footers, orphan prevention of headers, and rowspans across regions: `grid/layouter.rs` (1875 lines), `repeated.rs`, `rowspans.rs` (1283 lines). Fields such as `unbreakable_rows_left`, `repeating_headers`, `pending_headers`, `lrows_orphan_snapshot` (`layouter.rs:42-145`) are a good checklist for recto's table fragmenter.
- Breakable block insets and fills are applied to **every** fragment (`flow/block.rs` around l.199-240; `skip_first` when the first frame is empty). This corresponds to `box-decoration-break: clone`. CSS defaults to `slice`, so recto must support both.
- Inline: Knuth–Plass optimized line breaking (`inline/linebreak.rs:210-239`). This is relevant if recto wants high-quality justification; the text research doc covers it.
- Typst is not CSS: no margin collapsing, no CSS floats wrapping text, no BFC. The regions model is the transferable part, not the semantics.

### 3.4 fulgur (Blitz + Parley + Krilla HTML→PDF, MIT/Apache)

- This is the closest competitor to recto. Its architecture is strategy (a) plus a growing set of post-layout fragmenters:
  - `pagination_layout.rs` (10,559 lines), `multicol_layout.rs` (3,777), `render.rs` (7,458), `blitz_adapter.rs` (9,794).
- Spike conclusions (`docs/plans/2026-04-28-pagination-layout-spike.md`):
  - F2: inline wrapping is the real divergence. It was fixed by reading Parley line metrics.
  - F3: the "LayoutPartialTree wrapper" pattern is reusable.
  - F4: replacing post-layout paging needs break-*, widows/orphans, string-set, running elements, bookmarks re-done inside the hook.
  - **ik6o: constrained `available_space.height` changes nothing.**
- It quotes a Blitz maintainer comment saying the goal is to get fragmented layout into Taffy/Parley (blitz#128 comment). That is **future intent, not existing code** (UNVERIFIED: issue not readable from this environment).
- Lag: fulgur is pinned to taffy 0.9 / blitz-dom 0.2 / parley 0.6, while upstream is at 0.15 / 0.3-beta / 0.12. Taffy breaking churn makes downstream upgrades costly.
- Security: RUSTSEC-2026-0201 / CVE-2026-68537 is a DoS via amplification into thousands of blank pages, fixed in 0.26.0 (WebSearch, [osv.dev](https://osv.dev/vulnerability/RUSTSEC-2026-0201)). Lesson: a fragmenter needs a hard page cap and "no-progress" guards.

### 3.5 Azul `azul-layout` 0.0.16 (printpdf's HTML engine, MIT)

- Strategy (c): own BFC/IFC/table (`solver3/fc.rs`: `layout_bfc` l.1214, `layout_ifc` l.3570, `layout_table_fc` l.6282). Flex and grid go through taffy 0.10 (`solver3/taffy_bridge.rs`).
- `solver3/break_token.rs` documents a **LayoutNG-shaped pure contract**:
  `(node, constraint_space { remaining_extent }, break_token?) -> (fragment, break_token?)`.
  - `BreakToken::{Block(BlockBreakToken), Inline(InlineBreakToken)}` (l.40).
  - `BlockBreakToken { node, consumed_block_size, children: Vec<ChildBreakEntry>, generation }` (l.52).
  - `ChildBreakEntry::{ResumeIn{child, token}, BreakBefore{child, forced}}`. The `forced` flag exists so the margin-truncation rule can be applied on resume.
  - `InlineBreakToken { next_item_index, partial_remainder: Vec<ShapedItem> }` covers a hyphenated remainder.
  - `FitDecision::{Fits, BreakBeforeHere, MonolithOverflow}` (l.151).
  - Two stated laws: **determinism** (equal input ⇒ equal output token) and **progress** (outgoing token ≠ incoming token, asserted by the page loop to prevent infinite loops).
- Its older `paged_layout.rs` (y-position page assignment) is kept as a "fossil" explaining why the mutable approach failed (`break_token.rs` header).
- Maturity is UNVERIFIED (version 0.0.x). The design is the reference shape recto should adopt.

---

## 4. Taffy: performance, dependencies, MSRV, license, maintenance

- **Performance**: README benchmarks against Yoga (M1 Pro, layout only). Examples:
  - 10,000 nodes, depth 4: 2.69 ms;
  - 100,000 nodes, depth 5: 32.9 ms;
  - deep auto-size 100k nodes: 164 ms.
  - 0.15 CHANGELOG: "Grid layout is now ~60% faster, and Flexbox layout ~15% faster"; early-exit for single-axis size queries (#1219, #1221).
  - Flex runs multiple measure passes per item. Nested flex-in-flex with text leaves can cause repeated measurement; the 9-entry cache mitigates this.
  - For recto's documents, flex and grid nodes are a small fraction of the tree (most is block/inline/table), so taffy cost is not a bottleneck. **No independent benchmark run** (cargo build is blocked here).
- **Dependencies**: zero mandatory deps; `smallvec` with grid (§1.1). Compatible with `scratch` static builds and `no_std + alloc`.
- **MSRV**: 1.71 (very conservative). Blitz needs 1.91, parley 1.88, typst 1.92.
- **License**: MIT. Vendoring or forking `flexbox.rs` or `grid/` is allowed with notice retention. Servo's flex (MPL-2.0) is file-level copyleft, so copying files means keeping them MPL; prefer taffy as the vendoring source.
- **Maintenance**:
  - Cadence: very high (239 commits per year, a release roughly monthly in 2026).
  - API stability: **low**. 0.15 alone changed `Position` default semantics, required `compute_oof_layout` in custom trees, made `LayoutOutput` non-`Copy`, changed `available_space` margin semantics, and un-`Option`ed alignment fields (CHANGELOG "Changed" list).
  - Blitz already depends on an unreleased git rev (`place_floated_box` gained a caller id in `6c2106e3`, after 0.15.0).
  - Bus factor ≈1 (Nico Burns).
  - Mitigation: depend on a pinned minor and wrap behind a ~300-line adapter module, so that a fork or vendoring stays cheap.

---

## 5. Recommended architecture: own fragmenting engine, LayoutNG/Typst hybrid

### 5.1 Principles

1. **Pure, on-demand, per-fragmentainer layout with break tokens** (LayoutNG shape, as in Azul's `break_token.rs`), *not* Typst's all-regions-upfront `Regions.backlog`. Typst's own code calls its spill mechanism a compatibility shim (`collect.rs:591-600`).
   - Recto still borrows Typst's useful ideas: `Regions`-like `may_progress()` for the "would the next page help?" test, precomputed `need` for widows/orphans, `Stop::Relayout` for page floats and footnotes, and sticky snapshots.
2. **The page loop drives everything**:
   `layout_root(root, page_space_i, token_{i-1}) -> (PageFragment_i, token_i)`.
   - Emit page *i* as soon as it is finished (streaming).
   - Per-page memory is bounded.
   - Re-running a page with different `@page` geometry, or after a `target-counter()` change (two-pass), is cheap and deterministic.
3. **Fixed-point layout units** (e.g. `i32` 1/64 px or `Au`-like 1/60 px). This gives byte-identical determinism, exact fit comparisons, and no `FIT_EPS` hacks (contrast Azul `FIT_EPS = 0.01`).
   - Convert to and from taffy `f32` at the single bridge.
4. **Two modes for every layout algorithm**: `Unfragmented` (intrinsic sizing, measuring, monolithic content, flex/grid item measurement from taffy) and `Fragmented { remaining, … }`. Both share code; unfragmented is "remaining = ∞, no token".
5. **Progress and safety guards**:
   - each page must consume content or emit a monolith;
   - hard max-page cap and time/memory caps;
   - the fulgur DoS (RUSTSEC-2026-0201) is the cautionary example.

### 5.2 Core interface (Rust pseudo-code)

```rust
/// Fixed-point layout unit (e.g. 1/64 CSS px), Ord + Hash, deterministic.
#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub struct Lu(i32);

/// What a parent offers a child for this fragmentainer.
pub struct ConstraintSpace {
    pub available_inline: Lu,               // definite inline size (or Indefinite for intrinsic passes)
    pub percentage_basis: LogicalSize<Option<Lu>>,
    pub fragmentation: Fragmentation,
    pub bfc: Option<BfcOffset>,             // position within BFC (for floats); None if new BFC
    pub margin_strut: MarginStrut,          // incoming collapsible margins (like taffy CollapsibleMarginSet)
    pub exclusions: ExclusionSpaceRef,      // floats in this BFC *for this fragmentainer*
    pub is_new_fc: bool,
    pub stretch_block: Option<Lu>,          // definite block size for stretch/percentages
}

pub enum Fragmentation {
    None,                                    // unfragmented: intrinsic sizing / monolithic / taffy measure
    Page {
        fragmentainer_block_size: Lu,        // full page content height (for % resolution per page)
        block_offset: Lu,                    // where this child starts within the fragmentainer
        // remaining = fragmentainer_block_size - block_offset
        is_at_block_start: bool,             // "first content" → monolith may overflow; margins truncate
        break_appeal_floor: BreakAppeal,     // lowest acceptable appeal before relaxing (css-break §4.4)
        may_progress: bool,                  // would a fresh fragmentainer give more room? (Typst Regions::may_progress)
    },
}

pub struct LayoutResult {
    pub fragment: BoxFragment,               // geometry for THIS fragmentainer only
    pub break_token: Option<BreakToken>,     // None = box finished
    pub end_margin_strut: MarginStrut,
    pub status: LayoutStatus,                // Ok | NeedsEarlierBreak(EarlyBreak) | NeedsRelayout(Reason)
    pub break_before: BreakValue,            // propagated from first child (css-break §3.1)
    pub break_after: BreakValue,             // propagated from last child
    pub best_break: Option<EarlyBreak>,      // best (highest-appeal) breakpoint seen, for rewind
    pub baselines: Baselines,
    pub oof: Vec<OofCandidate>,              // abspos to hoist (cf. taffy OofCandidates)
}

#[derive(Clone, PartialEq, Eq, Hash)]
pub enum BreakToken {
    Block(BlockBreakToken),
    Inline(InlineBreakToken),
    Table(TableBreakToken),
    Flex(FlexBreakToken),
    Grid(GridBreakToken),
    Multicol(MulticolBreakToken),
}

#[derive(Clone, PartialEq, Eq, Hash)]
pub struct BlockBreakToken {
    pub node: BoxId,
    pub consumed_block_size: Lu,             // for fixed heights, % progress, slice decorations
    pub sequence: u32,                       // fragment index (0 = first) → decoration slicing
    pub children: SmallVec<[ChildToken; 2]>, // unfinished tail; everything before is done
    pub has_seen_all_children: bool,
    pub is_forced: bool,                     // forced break → preserve next margin (css-break §5.2)
    pub floats: SmallVec<[BreakToken; 1]>,   // floats continuing into next fragmentainer
}
pub enum ChildToken { Resume { child: BoxId, token: Box<BreakToken> }, BreakBefore { child: BoxId } }

#[derive(Clone, PartialEq, Eq, Hash)]
pub struct InlineBreakToken {
    pub node: BoxId,
    pub item_index: u32, pub text_offset: u32,  // position in the IFC's item/text stream
    pub open_inline_boxes: SmallVec<[BoxId; 4]>,// inline boxes split across the break (decoration slicing)
}

#[derive(Clone, PartialEq, Eq, Hash)]
pub struct TableBreakToken {
    pub node: BoxId, pub next_row: u32,
    pub row_tokens: SmallVec<[(u32 /*col*/, BreakToken); 4]>, // cells split mid-row
    pub consumed_block_size: Lu,
}

/// The single entry point every formatting context implements.
pub trait FormattingContextLayout {
    fn layout(&self, cx: &mut LayoutCx, node: BoxId, space: &ConstraintSpace,
              token: Option<&BreakToken>) -> LayoutResult;
    fn intrinsic_inline_sizes(&self, cx: &mut LayoutCx, node: BoxId) -> MinMax<Lu>; // cached per node
}

/// The page loop.
pub fn paginate(doc: &BoxTree, pages: &mut impl PageSink) -> Result<(), LayoutError> {
    let mut token: Option<BreakToken> = None;
    let mut page_no = 0;
    loop {
        let page = resolve_page_context(doc, page_no, token.as_ref()); // @page, named pages, :first/:left/:right
        let space = ConstraintSpace::for_page(&page);
        let res = layout_root(doc, &space, token.as_ref());
        assert!(res.break_token != token, "no progress");                // Azul's "progress law"
        pages.emit(build_page(page, res.fragment))?;                     // streaming emission
        page_no += 1;
        if page_no > LIMITS.max_pages { return Err(LayoutError::PageCap); }
        match res.break_token { None => break, t => token = t }
    }
    Ok(())
}
```

Best-break and rewind: follow css-break §4.4 "best breaks" (l.786). Each container returns `best_break` with an appeal class:
- `Perfect`;
- `ViolatingOrphansWidows`;
- `ViolatingBreakAvoid`;
- `LastResort`.

If the container runs out of space at a worse appeal than one seen earlier, the parent re-lays out with `EarlyBreak` set to stop there. That gives `break-inside: avoid`, `break-after: avoid` (headings), and orphans/widows. Typst's sticky snapshot (`distribute.rs:32-67`) is the simpler subset. Rewind is bounded: one relayout per page per level.

### 5.3 Module plan

| Module | Responsibility | Fragmentation behaviour | Reuse |
|---|---|---|---|
| `layout::units` | `Lu` fixed-point, logical/physical geometry, writing-mode transforms | — | own |
| `layout::box_tree` | Box generation from styled DOM: anonymous block/inline wrappers, table fixup (CSS 2.1 §17.2.1 anonymous table objects), list markers, `::before/::after`, `display: contents`, out-of-flow placeholders | — | Patterns from Servo `flow/construct.rs`, `table/construct.rs` (MPL: ideas only) |
| `layout::block` | BFC/block flow: margin collapsing (port taffy's `CollapsibleMarginSet` and collapse-through rules, `block.rs`), clearance, `flow-root`, auto margins, `min/max`, `box-sizing`, `align-content` | Break tokens; class A/C breaks; margin truncation at unforced breaks; forced-break margin preservation; `box-decoration-break: slice/clone`; content box fills remaining extent (§"Splitting Boxes"); `break-before/after/inside`, propagation from first/last child | Port taffy `block.rs` collapse logic (MIT) into a fragmenting algorithm |
| `layout::float` | Exclusion space per BFC per fragmentainer: `place_float`, `find_line_slot(min_y, height)`, `find_bfc_slot`, `clearance(clear)` | Floats taller than the remaining space fragment (they get their own tokens). Floats that do not fit are pushed (css-break §"varying-size" notes: order preserved, a later left float may precede a right float's continuation). Exclusion space resets per page; carried floats re-enter at the block-start | Port taffy `float.rs` slot search (`FloatContext`, `find_content_slot`, `find_bfc_slot`), but rebuild the data per fragmentainer and in `Lu` |
| `layout::inline` | IFC: item collection, bidi, shaping (via text crate), line breaking (UAX#14 + optional Knuth–Plass), line boxes, vertical-align, inline-block atoms, `text-align`/justify, `text-indent`, `::first-line`, floats-in-inline | Lines are the break units (class B). `orphans`/`widows` via Typst-style `need`. `InlineBreakToken` (item + text offset + open inline boxes for decoration slicing). Line width may change per page (floats, page width) → re-break the remainder lazily from the token. Parley's `BreakerState` / `MaxHeightExceeded` (`line_break.rs`) is a candidate primitive if parley is chosen | Text stack per the text research doc. Typst `inline/` as reference |
| `layout::table` | Own CSS2.1/css-tables-3 table: column width (auto + fixed), row heights, `border-collapse` (conflict resolution), `border-spacing`, captions, `visibility: collapse`, rowspan/colspan, cell vertical-align, baselines | Break between rows (class A); inside rows only if all cells are breakable (cells fragment in parallel → `TableBreakToken.row_tokens`); **repeat `thead`/`tfoot`** each page, with orphan-header avoidance (checklist: Typst `grid/layouter.rs` `repeating_headers`, `pending_headers`, `lrows_orphan_snapshot`); rowspan across pages (Typst `rowspans.rs`) | Own. Do *not* emulate via taffy grid (Blitz does; this loses `border-collapse` and table semantics) |
| `layout::flex` | Adapter: recto box → `taffy::LayoutFlexboxContainer` (+ `LayoutPartialTree`, `CacheTree`) with `compute_child_layout` → `layout::dispatch` in `Fragmentation::None` mode | **Monolithic by default.** If it fits or `break-inside: avoid`: one taffy call. Otherwise:<br>• **Row flex**: taffy pass (unfragmented) → per line, items' inline sizes and cross positions. Recto then fragments line by line: a line that fits is placed; a line that does not fit has each item laid out fragmented in parallel with `known inline size`, the row's block size per page = max of the item fragments, and stretch items fill the page fragment.<br>• **Column flex** with auto height: treat items as block-like children (breaks between items, inside items). With definite height plus grow/shrink: monolithic (rare in documents).<br>• `FlexBreakToken { line, item_tokens }`. | `taffy::compute_flexbox_layout` (MIT). Vendor `flexbox.rs` only if the per-page "rerun from line length determination" is needed later |
| `layout::grid` (stretch) | Adapter to `taffy::compute_grid_layout` (Servo pattern) | Monolithic, or break between rows using `DetailedGridInfo` row tracks (`LayoutGridContainer::set_detailed_grid_info`); items spanning a break fragment as in row flex | taffy grid |
| `layout::abspos` | Static position, insets, shrink-to-fit, hoisting (cf. taffy `oof.rs`, `OofCandidates`) | Containing block = page for `fixed` (repeat on every page, Paged Media); abspos with a CB that fragments is placed in the fragment containing its static position (simplification; css-break allows UA choice) — UNVERIFIED rule detail, check css-position-3 | Port ideas from taffy `oof.rs` |
| `layout::multicol` | Column balancing (`column-fill: balance`), `column-span: all`, nested in pages | Columns are fragmentainers nested in the page: run the same `layout()` with `Fragmentation::Column`; balancing by binary search over column height (bounded iterations); `MulticolBreakToken` carries the column-content token across pages | own; fulgur `multicol_layout.rs` as reference (MIT/Apache) |
| `layout::page` | `@page` resolution (size, margins, named pages, `:first/:left/:right/:blank`), margin boxes (16 boxes, CSS GCPM / Paged Media §5 sizing), running elements, `string-set`, counters, page floats/footnotes (later) | Drives `paginate()`. A named-page change in the content forces a break (token boundary). Margin boxes laid out unfragmented | own |
| `layout::fragment` | Output: `PageFragment { boxes: Vec<BoxFragment>, … }` → paint/PDF. Immutable, per page, freed after emission | — | own |
| `layout::dispatch` + `cache` | `match` on formatting context; intrinsic-size cache per node; layout cache keyed by `(node, ConstraintSpace hash, token)` for re-runs (two-pass `target-counter`) | Cache must include the token and fragmentainer offset | own |

Estimated size: block+float 3–4k, inline 4–6k (excluding shaping), table 4–5k, flex/grid adapters + fragmentation 1.5–2k, abspos 1k, multicol 1.5k, page 2–3k. Total about 18–23k LOC.

### 5.4 Phasing

1. `Lu`, box tree, block (no floats) with tokens, inline with tokens, page loop. Gate: invoices/letters paginate correctly, with streaming.
2. Floats + clearance (port taffy logic), tables + repeated headers, `break-*`, orphans/widows, best-break rewind.
3. Flex via taffy (monolithic + row-line fragmentation), abspos/fixed, margin boxes.
4. Multicol, grid via taffy, page floats/footnotes.

---

## Findings that affect recto's design

1. **Taffy 0.15.0 has no fragmentation concept at all.** `LayoutInput`/`LayoutOutput` are one-box-in/one-box-out (`tree/layout.rs:125, 472`). Block layout forces `available_space.height = MaxContent` for children (`compute/block.rs:1090`), so a page height cannot even reach descendants. fulgur measured that constraining available height changes nothing (spike `fulgur-ik6o`).
2. **Taffy's block layout is good but block-only.** It covers margin collapsing (siblings, parent/child, collapse-through by used height, min-height rule), floats, clearance, and BFC roots (`block.rs`, `float.rs`). Inline/IFC, tables, `inline-block` and multicol are host responsibilities (`block.rs:1`, `Display` enum `style/mod.rs:251`).
3. **Custom modes plug in only via the host's `compute_child_layout` dispatch.** Floats reach host inline layout via `LayoutBlockContainer::compute_block_child_layout(…, Option<&mut BlockContext>)` + `find_content_slot`/`place_floated_box` (Blitz `inline.rs:676-780`). This is sufficient to embed taffy flex/grid inside recto's own engine (Servo/Azul pattern).
4. **Post-layout slicing (strategy a) is a dead end for correctness.** fulgur's 10.5k-line `pagination_layout.rs` still lacks nested-table fragmentation and header-band fragmentation, and hit f32 drift when re-driving taffy. It also prevents streaming.
5. **Typst's regions model is proven prior art, but its "all regions upfront" API is self-described as a compatibility layer** (`collect.rs:591-600`). Its regions are uniform-width, so floats cannot wrap text across regions (`regions.rs:36-40`). Adopt on-demand **break tokens** (LayoutNG / Azul `break_token.rs` shape). Copy Typst's `need`-based widows/orphans, sticky snapshots, `Stop::Relayout` for insertions, and its grid header/footer/rowspan checklist.
6. **Tables must be our own.** Taffy has none. Blitz's grid emulation lacks `border-collapse`, and fulgur inherits that gap. Repeated headers/footers and row-level breaks are core v1 features for invoices and statements.
7. **Use taffy for flex (and later grid) as unfragmented measurers** behind one adapter. Fragment at container level (between lines/rows; parallel item fragmentation for row flex), as the css-flexbox-1 sample algorithm suggests (`Overview.bs:4658+`). Most document flex containers are monolithic.
8. **Units.** Taffy is `f32`. Use fixed-point `Lu` internally for determinism and exact fit tests, and convert only at the taffy bridge, as Servo does with `Au::from_f32_px`.
9. **Maintenance risk.** Taffy breaks its API every minor release (6 minors in 2026) with a bus factor ≈1, and Blitz already depends on an unreleased rev. Pin an exact minor, isolate it behind `layout::flex`/`layout::grid` adapters (~300–600 LOC), and keep the MIT option to vendor `flexbox.rs` (3460 lines) or `grid/` (~8k lines).
10. **Guards are mandatory.** Assert progress (token must change), cap pages, and force monolith overflow when there is no progress. fulgur shipped a blank-page amplification DoS (RUSTSEC-2026-0201).
11. **Parley's line breaker is resumable** (`BreakerState`, `revert_to`, `MaxHeightExceeded` yield, `line_break.rs:71-75, 531, 996-1028`). If parley is chosen by the text research, `InlineBreakToken` can wrap its state; Blitz leaves `MaxHeightExceeded` as TODO.
12. Taffy dependency footprint is ~zero (only `smallvec` with grid), and MSRV 1.71 / MIT pose no obstacles. Performance is ample (10k nodes ≈ 2.7 ms in the README benchmark).

## Recommendation

**Build recto's own fragmentation-aware layout engine around a LayoutNG-style `layout(node, ConstraintSpace, Option<&BreakToken>) -> LayoutResult { fragment, break_token, … }` contract, driven by a streaming page loop.** Typst's per-region flow ideas (need-based widows/orphans, sticky snapshots, relayout on insertions, table header/footer machinery) supply the policy, not its all-regions-upfront API.

Own: block, floats, inline, table, abspos, multicol, and page/margin boxes.

Reuse from taffy (MIT, pinned version, behind an adapter):
- (1) `compute_flexbox_layout` for flex containers, used monolithically or as the unfragmented measuring pass for row-line/column-item fragmentation;
- (2) `compute_grid_layout` for grid (stretch goal), same pattern;
- (3) **ported code** (not calls) for margin-collapsing rules (`CollapsibleMarginSet`, collapse-through and min-height conditions in `block.rs`) and float slot search (`float.rs` `FloatContext`) into the fragmenting block/float modules.

Do not use taffy's `compute_block_layout` in the main flow: it cannot fragment and would have to be bypassed for every breakable block anyway. Do not adopt strategy (a) or (b).

## Open questions / UNVERIFIED items

- **Taffy 0.15.0 git tag**: there is no `v0.15.0` tag. The inspected commit `eb645069` ("Prepare for v0.15 release") is presumed to equal the published crate; static.crates.io is blocked, so this could not be verified.
- Whether taffy grid supports `subgrid`: not found in the style code. UNVERIFIED.
- Blitz issue #128 maintainer comment (cited by fulgur) about bringing fragmentation into Taffy/Parley: the GitHub API is not accessible from this session. Intent only, UNVERIFIED, with no code in taffy 0.15.0/main `6c2106e3`.
- ironpress, fullbleed, ferropdf architectures: not inspected (WebSearch summaries only).
- Azul's break-token engine maturity and correctness: design read only, no tests run.
- Flex row-line fragmentation fidelity versus Chrome: chosen to follow the css-flexbox-1 informative algorithm. It needs WPT `css/css-break/flexbox/*` comparison later.
- Abspos inside fragmented containing blocks: exact placement rule (css-position-3 / css-break-3) to be checked by the CSS-spec research doc.
- Performance of best-break rewind on 1000-page docs: bounded by design (≤1 rewind per level per page), but not measured.
- Whether to vendor taffy's flexbox now (for per-page "rerun from line length determination") or call the public API: decide after the first flex fragmentation fixtures.
