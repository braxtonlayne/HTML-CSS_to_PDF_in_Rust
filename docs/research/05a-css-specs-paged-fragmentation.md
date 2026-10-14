# 05a — CSS specs: Paged Media 3, Fragmentation 3/4, GCPM 3 (+ Content 3, Lists 3 counters), Page Floats 3

Date: 2026-10-14 · Topic slug: `cssspecs` · Companion file: `05b-css-specs-text-fonts-tables-multicol.md`

Purpose: extract concrete, testable requirements (numbered, with § references to the Bikeshed source) that
recto's paginator must satisfy, mark stability, and separate v1 scope from deferred work.

## Sources inspected

All specs read from one sparse clone of `w3c/csswg-drafts` (HEAD `1c249b342ee7a0dfe0fcf7f7dc75272b1e794d52`,
committed 2026-10-14). Clone location: `/tmp/claude-0/src/cssspecs/csswg-drafts`. License (repo `LICENSE.md`):
W3C Software and Document License. "Last commit" = last commit touching that `Overview.bs` (`git log -1 -- <dir>/Overview.bs`).

| Spec (shortname) | File | Bikeshed `Status` / `Work Status` | Date field | Last commit touching file | Maintenance / stability assessment |
|---|---|---|---|---|---|
| CSS Paged Media 3 (`css-page-3`) | `css-page-3/Overview.bs` (2605 lines) | ED / **Revising** | none (ED) | `f541930` 2026-03-03 | Core model stable for 10+ years; implemented by Prince, WeasyPrint, Vivliostyle, Antenna House, Chromium (margin boxes since Chrome 131). Safe to implement. |
| CSS Fragmentation 3 (`css-break-3`) | `css-break-3/Overview.bs` (1329) | ED / **Testing** (CR on TR) | none | `367b9f5` 2025-12-08 | Most stable of the set. Normative rules 1–4 are the contract. |
| CSS Fragmentation 4 (`css-break-4`) | `css-break-4/Overview.bs` (1308) | ED / **Exploring**; `At Risk: break-before/all` | none | `b17c61c` 2026-06-24 | = L3 + `margin-break` + `always`/`all` values. `margin-break` has open issue #3254. |
| CSS GCPM 3 (`css-gcpm-3`) | `css-gcpm-3/Overview.bs` (1021) | ED / **Exploring**; `Prepare for TR: no` | none | `58354da` 2026-10-08 | Running elements + footnotes are de-facto standardized by Prince/WeasyPrint/AH/PagedJS rather than by this text; spec has "We need an algorithm for laying out footnotes" issue. |
| CSS Generated Content 3 (`css-content-3`) | `css-content-3/Overview.bs` (1502) | ED / **Exploring**; Status Text: "very rough draft, and is not ready for implementation" | none | `4f200bd` 2026-10-09 | Home of `leader()`, `target-counter()`, `target-text()`, `string-set`/`string()`, `bookmark-*`. Behaviour is de facto Prince/WeasyPrint. |
| CSS Lists 3 (`css-lists-3`) | `css-lists-3/Overview.bs` (1697) | ED / **Refining** | none | `bd473df` 2026-04-28 | Counter inheritance/instantiation algorithm is precise and interop-tested. |
| CSS Page Floats 3 (`css-page-floats-3`) | `css-page-floats-3/Overview.bs` (1237) | ED / **Exploring** | none | `906d33c` 2025-12-22 | Speculative; low implementation. Defer. |

## Conventions

- `PG-n` = requirement from css-page-3, `BRK-n` css-break-3/4, `GC-n` GCPM 3, `CT-n` css-content-3, `LS-n` css-lists-3, `PF-n` page floats.
- "§x" uses the section `id` in the `.bs` file (e.g. `css-page-3#variable-sizing`), plus the source line where helpful (`L1109`).
- **[stable]** = normative text with interop; **[unstable]** = ED text with open issues / no algorithm; **[de facto]** = behaviour fixed by existing print engines rather than by the text.

---

## 1. CSS Paged Media Level 3

### 1.1 Page model (§page-model, L225; §painting L279)

- **PG-1 [stable]** The page box has margin/border/padding/content; content area = **page area**. The page area of the **first** page establishes the initial containing block (ICB).
- **PG-2 [stable]** Page box width & horizontal margins are computed "exactly as for a non-replaced block element in normal flow" (CSS2 §10.3.3) against the containing block given by `size`; height & vertical margins analogously. **Over-constrained: margins are not ignored; instead the containing block (sheet) is resized** to coincide with the margin edges. (So `@page { size: A4; width: 100mm; margin: auto }` centers a 100 mm page area — css-page-3 example at L759–764 relies on `width`/`height` in the page context; Appendix A lists `width`, `min-/max-width`, `height`, `min-/max-height` as page properties.)
- **PG-3 [stable]** Painting order on a page (bottom → top): 1 page background, 2 document canvas, 3 page borders, 4 document contents, 5 page-margin boxes.
- **PG-4 [stable]** Page background painting area = **bleed area** (entire page box incl. margins, regardless of `background-clip`); positioning area = page **padding box** by default (honours `background-origin`); with `background-attachment: fixed` positioning area = page **margin box**.
- **PG-5 [stable]** Root/canvas background is painted as the page box's background over the page's **border box** (follows root `background-clip`), positioned relative to root element / page area as usual.
- **PG-6 [stable]** Document canvas + page borders + contents act as one stacking context with `z-index: 0` relative to margin boxes; margin boxes never interleave with document content. `z-index` applies to margin boxes as if positioned; each margin box always establishes a stacking context.
- **PG-7 [stable]** Default (tree) paint order of margin boxes: top-left-corner, top-left, top-center, top-right, top-right-corner, right-top, right-middle, right-bottom, bottom-right-corner, bottom-right, bottom-center, bottom-left, bottom-left-corner, left-bottom, left-middle, left-top (clockwise from TL corner).
- **PG-8 [stable]** *Content-empty page* (§content-outside-box): page area contains no printable content other than backgrounds/borders. A page with generated content, `visibility:hidden` content, or a ZWSP is **not** content-empty; a page with only backgrounds/borders/margin-box content **is**. UA SHOULD avoid generating many content-empty pages for positioned content; handling of content outside the page box is undefined (discard or append pages).

### 1.2 Page progression, left/right, first page (§progression L404)

- **PG-9 [stable]** Every page is left or right; they alternate. Horizontal text: page progression = inline base direction of the root (principal writing mode); vertical: = block flow direction.
- **PG-10 [stable]** LTR progression ⇒ **first page is a right page**; RTL ⇒ left.
- **PG-11 [stable]** A forced `break-before` that propagates to the root (e.g. `html { break-before: left }`) selects the side of the first page; the UA **must suppress the leading empty page(s)** and `:first` matches the first *printed* page.

### 1.3 `@page` rule, selectors, cascade (§at-page-rule L465, §page-selectors L492, §syntax-page-selector L643, §cascading-and-page-context L713)

- **PG-12 [stable]** Grammar:
  `@page = @page <page-selector-list>? { <declaration-rule-list> }`;
  `<page-selector> = [ <ident-token>? <pseudo-page>* ]!`; `<pseudo-page> = : [ left | right | first | blank ]`.
  No whitespace inside a `<page-selector>`. `@page` may only contain page properties + the 16 margin at-rules; margin at-rules only page-margin properties. Errors inside → CSS2 error recovery (keep valid declarations).
- **PG-13 [stable]** Page type name is a **case-sensitive** identifier matching named pages from the `page` property; the name `auto` (ASCII-ci) is valid syntax but **never matches**. Pseudo-classes are ASCII case-insensitive.
- **PG-14 [stable]** Selector matches iff all components match. `@page` with no selector matches all pages. Selector list = OR.
- **PG-15 [stable]** Specificity `(f, g, h)`: f = # page type names (0/1), g = # `:first`+`:blank`, h = # `:left`+`:right`; repeated pseudo-classes **do** add; compare lexicographically; clamp (not overflow) at implementation limits. Examples: `@page`=(0,0,0), `:left`=(0,0,1), `:first`=(0,1,0), `:blank:left`=(0,1,1), `artsy`=(1,0,0), `artsy:first`=(1,1,0).
- **PG-16 [stable]** Page and margin contexts **cascade like normal style rules** (origin, importance, specificity, then order) — e.g. two unselected `@page` rules merge (`margin` from one, `font-size` from another). Margin-box declarations cascade per margin box name across all matching `@page` rules (the `:first` example: `@top-left` from `:first` coexists with `@top-center` from bare `@page`).
- **PG-17 [stable]** `:left`/`:right` must be honoured even when output is single-sided.
- **PG-18 [stable]** `:first` matches the first printed page of the document (only; GCPM `:nth()` is needed for "first page of each chapter").
- **PG-19 [stable]** `:blank` matches content-empty pages **that appear as a result of forced page breaks** — in practice only pages inserted by `left`/`right`/`recto`/`verso` to fix parity (note at L589). A `:blank` page may also match `:left`/`:right` etc.

### 1.4 Page context property semantics (§page-properties L1396; Appendix A L2313)

- **PG-20 [stable]** Normative property lists: **page context**: direction, background-*, border-*, counter-reset/increment, color, font-*, height/min/max-height, line-height, margin-*, outline-*, padding-*, quotes, letter-spacing, text-align, text-decoration, text-indent, text-transform, white-space, word-spacing, visibility, width/min/max-width. **Margin context** additionally: unicode-bidi, content, overflow, vertical-align, z-index. Properties outside CSS 2.1 are "undefined" (so supporting e.g. `border-radius`, `box-shadow`, `background-size` in margin boxes is permitted).
- **PG-21 [stable, with legacy allowance]** Inheritance: margin boxes inherit from the page context; the **page context inherits from the root element** (an implementation that uses initial values instead is still L3-conformant; removed in L4). Recto: inherit from root (matches Prince/WeasyPrint/Chromium).
- **PG-22 [stable]** `em`/`ex` on `font-size` in margin context are relative to the page context font; in page context, relative to root `font-size`.
- **PG-23 [stable]** Percentages on margin/padding in page/margin contexts: left/right relative to containing block **width**, top/bottom relative to containing block **height** (differs from normal flow, where all are relative to width).
- **PG-24 [stable]** On margin boxes `vertical-align` behaves like on **table cells** (`top|middle|bottom|baseline` aligning content in the box), always in the physical vertical dimension. `content: normal` computes to `none` on margin boxes (css-content-3 says `normal`→`contents` for page-margin boxes, but css-page-3 L1029/L1462 is normative for paged layout: margin box is **generated iff computed `content` ≠ `none`**). `display` does not apply.
- **PG-25 [stable]** UA default stylesheet values (Table 2, L1560): text-align / vertical-align per box —
  TLC right/middle; TL left/middle; TC center/middle; TR right/middle; TRC left/middle;
  LT center/top; LM center/middle; LB center/bottom; RT center/top; RM center/middle; RB center/bottom;
  BLC right/middle; BL left/middle; BC center/middle; BR right/middle; BRC left/middle.

### 1.5 Page-margin boxes: geometry (§margin-boxes L815, §margin-dimension L1032)

- **PG-26 [stable]** 16 boxes. Corner boxes = fixed size: intersection of the two adjacent page margins. Side boxes' containing block = the page margin strip minus the adjacent corner rectangles: for top/bottom boxes its width is the **available width** = page box border-box width (border-left + padding-left + page area width + padding-right + border-right); height = used top/bottom page margin. Left/right: height = **available height** (page border-box height), width = used left/right margin.
- **PG-27 [stable]** min/max-width/height apply to margin boxes (re-run of computation); UA without min-* support behaves as min = 0.

#### PG-28 Variable-dimension algorithm (§variable-sizing L1109) — applies to {A=@top-left, B=@top-center, C=@top-right}, mirrored to bottom, and to {@left-top, @left-middle, @left-bottom} / right with width→height, left→top, right→bottom, center→middle

1. `margin-left`/`margin-right` `auto` ⇒ used 0 (for all three).
2. Non-generated boxes (computed `content: none`) count as `width` = outer width = 0.
3. Terms: *outer width* = margin-box width; *min-content width/max-content width* = physical-width min/max-content size; *outer min width / outer max width* = outer width using min-/max-content width when computed `width: auto`.
4. **If B is not generated**: distribute available width to A and C:
   - If exactly one of A, C has `width:auto`: its used width = available width − Σ outer widths of the others (sum of outer widths = available width).
   - If both auto ("flex-fit", L1141):
     a. If Σ outer **max-content** widths < available width: flex space = difference; flex factor_i ∝ outer max-content width_i; used outer width_i = max_i + space × f_i / Σf.
     b. Else if Σ outer **min-content** widths < available width: flex space = available − Σ min; flex factor_i ∝ (max-content_i − min-content_i); used outer width_i = min_i + space × f_i / Σf.
     c. Else: as (b) (base = min-content, space possibly negative) but flex factor_i ∝ outer min-content width_i.
     In every case, if Σ flex factors = 0, both factors = 1.
   - (If neither is auto: no rule; used widths = specified; overflow/overlap allowed.)
5. **If B is generated**:
   1. Resolve B's auto width by running the A/C two-box procedure on B and an imaginary box **AC** whose every dimension (min-content, max-content, outer width) = **2 × max(A, C)** (preserves centering).
   2. Then each auto-width side box gets outer width = (available width − used outer width of B) / 2.
6. min/max (§variable-minmax): compute tentative widths; if any box's tentative width > its `max-width`, rerun with `max-width` as computed `width`; then if any resulting width < `min-width`, rerun with `min-width` as `width`.
7. Positioning: A's left outer edge flush with containing block left; B's outer box **centered** in the containing block (centered on the page box, independent of A/C); C's right outer edge flush right.

Testable consequences (examples L1304–1396): only `@top-left` generated ⇒ it may extend across the page centre; `@top-left`+`@top-right` with 2:1 content ⇒ widths ≈ 2:1 split of the line; `@top-center` alone ⇒ centered, and A/C = (avail − B)/2 even if not generated.

#### PG-29 Fixed-dimension algorithm (§fixed-sizing L1240) — height/margin-top/margin-bottom of the 5 top boxes (incl. corners); mirrored for bottom, and for left/right with width

1. Constraint: `margin-top + border-top + padding-top + height + padding-bottom + border-bottom + margin-bottom = top page margin`.
2. If border+padding+height (if not auto) + non-auto margins > top page margin, any `auto` margins are treated as `<safe-printable-inset>` (0 unless `page-margin-safety` is used) for the next steps.
3. If none of height/margin-top/margin-bottom is `auto` (over-constrained): treat **margin-top** as auto (top boxes); for bottom boxes ignore **margin-bottom**; for left boxes ignore **margin-left**; right boxes **margin-right** (i.e. the margin on the sheet-edge side gives way).
4. Exactly one `auto` ⇒ solve from equality.
5. If `height:auto`: auto margins become `<safe-printable-inset>` and height follows from the equality (⇒ by default a margin box fills the full margin depth).
6. Both margins auto ⇒ equal (vertical centering); if safe-printable-inset ≠ 0 and margin-top < inset, move the deficit from margin-bottom (not below 0) to margin-top.

- **PG-30 [stable]** Corner boxes use the fixed-dimension rules in *both* axes (they belong to both the top list and the left list).

### 1.6 Page-based counters (§page-based-counters L1489)

- **PG-31 [stable]** `counter-increment` in page or margin context increments once per page box generated.
- **PG-32 [stable]** Counter reset/incremented in the **page context** is in scope for all margin boxes of that page and hides same-named document counters; in a **margin context**, scoped to that box only and hides page + document counters.
- **PG-33 [stable]** A counter used in a margin box but not reset/incremented in page/margin context takes the value **as if the margin box were an element at the start of the page, inside the deepest normal-flow element spanning the page break**; using it doesn't change it. (Enables `counter(chapter)` in headers.)
- **PG-34 [stable]** Counter `page` is created automatically and incremented by 1 per page **unless** page-context `counter-increment` names `page` explicitly (then that increment is used, e.g. `page 2`). It is a real counter: `counter-reset: page 1` on an element or `@page :first`, `counter()`/`counters()` and styles (`lower-roman`) work.
- **PG-35 [stable]** Counter `pages` = total page count; `counter-reset`/`counter-increment` on it are valid but **ignored**. (Requires a second pass or deferred margin-box rendering — see Findings.)

### 1.7 `size`, `page-orientation`, `marks`, `bleed`, `page-margin-safety` (§page-size L1656)

- **PG-36 [stable]** `size: <length [0,∞]>{1,2} | auto | [ <page-size> || [portrait | landscape] ]`, initial `auto`, computed = specified with absolute lengths. One length ⇒ square. `em/ex` relative to page context font. Negative invalid.
- **PG-37 [stable]** `<page-size>` table: A5 148×210 mm, A4 210×297, A3 297×420, B5 176×250, B4 250×353, JIS-B5 182×257, JIS-B4 257×364, letter 8.5×11 in, legal 8.5×14 in, ledger 11×17 in. `landscape` ⇒ longer side horizontal (swap if needed); `portrait` ⇒ shorter side horizontal. `landscape`/`portrait` alone ⇒ UA-chosen sheet size in that orientation. (A4/letter/legal/A3/A5/B4/B5/ledger/JIS — note **no** "tabloid"/"A6"; those are Chromium extensions — treat as recto extensions if desired.)
- **PG-38 [stable]** A `size` declaration inside a size-dependent media query (`width`, `height`, `aspect-ratio`, `orientation`, device-*) **must be ignored**; media queries evaluate against the UA default page size, not `size`.
- **PG-39 [stable]** Different `size` per named page is allowed (`@page wide { size: A4 landscape }`) — a PDF writer can emit per-page MediaBox; content flows across differently sized pages (break-3 §varying-size-boxes).
- **PG-40 [stable]** `page-orientation: upright | rotate-left | rotate-right` — post-layout rotation of the output page (in PDF: `/Rotate 270` / `/Rotate 90`); margin boxes rotate with the page.
- **PG-41 [stable]** `marks: none | [crop || cross]`; `bleed: auto | <length>`, `auto` = 6pt if marks has `crop` else 0. Bleed area = extent outside page box where rendering is clipped (PDF: BleedBox; TrimBox = page box; MediaBox = page box + bleed + mark area).
- **PG-42 [unstable]** `page-margin-safety: none | clamp | add` (initial listed as `auto`, not in the value grammar — spec bug). Defer.
- **PG-43 [informative]** Page box vs sheet mismatch: prefer larger sheet > rotate > scale > tile > clip. For PDF output the sheet = page box, so N/A.

### 1.8 Named pages: `page` (§using-named-pages L2163)

- **PG-44 [stable]** `page: auto | <custom-ident>`, initial auto, **not inherited**, applies to boxes creating class-A break points. Used value of `auto` = nearest ancestor's non-auto value; on root, `auto` ⇒ empty string (unnamed). (Legacy: implementations that inherit are still conformant.)
- **PG-45 [stable]** Algorithm: (1) resolve auto against ancestors; (2) each box has a **start page value** and **end page value** = value propagated from its first/last child box (only children to which `page` applies propagate), else its own used value; (3) **first page's type = start page value of the root**; (4) at every class-A break point, if end value of the preceding box ≠ start value of the following box ⇒ **forced page break**, next page is of the following box's type.
  Test: `div{page:narrow} table{page:rotated}` with `<div><table/><table/><p/></div>` ⇒ both tables on the same `rotated` page(s), `<p>` on a `narrow` page.
- **PG-46 [stable]** Named-page forced breaks interact with `:blank`? No — `:blank` only for parity pages; named page changes produce ordinary pages.

---

## 2. CSS Fragmentation Level 3 (+ Level 4 deltas)

### 2.1 Model (§fragmentation-model L80, §parallel-flows L166, §nested-flows L205)

- **BRK-1** Terms: fragmentainer, fragmentation context (one block-flow direction), fragmented flow, fragmentation root, box fragment (each fragment has its own margin/border/padding areas, subject to `box-decoration-break`), remaining fragmentainer extent.
- **BRK-2 [stable]** Parallel flows fragment independently: float vs. surrounding content, adjacent floats, **each table cell in a row**, flex items in a row, grid items in a row, abspos boxes. UA may balance unforced breaks in parallel flows but **must not** align them to match a forced break.
- **BRK-3 [stable]** Content overflowing a fixed-size box is parallel to the following content and still generates/spills into fragmentainers (does not grow the box).
- **BRK-4 [stable]** Nested: a page break inside a multicol container is both a page break and a column break; multicol continues with a new row of columns on the next page.

### 2.2 Properties (§break-between L257, §break-within L413, §widows-orphans L454, §page-break-properties L510)

- **BRK-5** `break-before`, `break-after`: `auto | avoid | avoid-page | page | left | right | recto | verso | avoid-column | column | avoid-region | region` (L4 adds `always | all`, `all` at-risk). Initial `auto`. Applies to block-level boxes, grid items, flex items, table row groups, table rows. Not inherited. Computed: keyword.
  - MUST apply to boxes in the normal flow of the fragmentation root; SHOULD apply to floats whose containing block is in that normal flow; MUST NOT apply to abspos boxes.
  - Page values have no effect outside paged contexts; column values only in multicol.
  - `left`/`right` force one or two page breaks so next page is left/right; `recto`/`verso` = second/first page of a spread per page progression (LTR: recto = right).
  - L4 `always`: break of the immediately containing fragmentation context type (column inside multicol, page otherwise). `all`: breaks through all contexts.
- **BRK-6** `break-inside: auto | avoid | avoid-page | avoid-column | avoid-region`, initial auto, applies to all elements except inline-level, internal ruby, table column/column-group, abspos. Not inherited.
- **BRK-7** `orphans`, `widows`: `<integer [1,∞]>`, initial **2**, **inherited**, apply to block containers establishing an IFC. 0/negative invalid ⇒ declaration ignored. If a block has fewer lines than widows/orphans, all lines must be kept together.
- **BRK-8** Legacy shorthands: `page-break-before/after/inside` map `auto|left|right|avoid` 1:1 and `always`→`page` (legacy shorthand semantics: computed value read back via the shorthand).

### 2.3 Propagation (§break-propagation L382)

- **BRK-9 [stable]** `break-before` on the **first in-flow child** propagates to its container; `break-after` on the **last in-flow child** likewise (recursively), except where layout modes define their own (flex/grid). Propagation stops before breaking through the nearest matching fragmentation context. Does not change computed values. Conflicting values combine per BRK-11.
  Test: `<section><h1 style="break-before:page">` ⇒ the break occurs between section's previous sibling and section (so section's top border/margin go to the next page with the h1).

### 2.4 Break points (§possible-breaks L549)

- **BRK-10 [stable]**
  - **Class A**: between siblings — (block-parallel) in-flow block-level boxes; a float and an immediately adjacent in-flow or floated box; table row groups; table rows; multicol column rows. (Block-perpendicular: column groups, columns, column boxes.)
  - **Class B**: between line boxes inside a block container.
  - **Class C**: between the content edge of a block container and its child content's outer edges (block children's margin edges / line box edges) **if there is a non-zero gap** (e.g. a fixed-height box taller than its content; bottom padding area is *not* class C — the gap is inside the content box).
  - No inherent priority between classes.
  - **Monolithic** content has no break points: replaced elements, scrollable elements, a single line. Forced breaks inside monolithic content are ignored by the outer context. UA **may** treat as monolithic: `overflow: auto|scroll`, `overflow:hidden` + definite block-size (no max); inline-block/inline-table.
- **BRK-11 [stable]** (§forced-breaks L677) Forced break at class A iff any of the `break-after` values (specified on or propagated to the earlier sibling) or `break-before` values (later sibling) is a forced value — forced overrides avoid. Multiple forced values combine so all break types are honoured; among `left/right/recto/verso` the value on the **latest element in the flow wins**. A forced break not inside a matching fragmentation context has no effect. Forced page break also at class A when `page` values differ (PG-45).
- **BRK-12 [stable]** Fragmentainers have minimum block size 1px for progress.

### 2.5 Unforced breaks — Rules 1–4 (§unforced-breaks L708)

- **Rule 1**: break at class A only if all applicable `break-after`/`break-before` values allow it — i.e. at least one forces, or none is `avoid` / `avoid-<type>` matching the break type (`avoid-page` forbids page breaks; `avoid-column` only column breaks; `avoid` all).
- **Rule 2**: if all of them are `auto` and a **common ancestor** of all the elements has `break-inside: avoid` (or the type-matching avoid-*), not allowed.
- **Rule 3**: class B allowed only if #lines between break and start of the block ≥ `orphans` and #lines between break and end ≥ `widows`.
- **Rule 4**: class B or class C allowed only if `break-inside` of **all ancestors** is `auto` (for the relevant break type).
- **Relaxation order** (normative): if not enough break points to avoid overflow → drop Rule 3; still not enough → drop Rules 1, 2, 4 (UA may weigh remaining avoids, no algorithm); still not → truncate **cloned** margin/border/padding at block-end, then block-start; finally if no break point below the fragmentainer top, UA may break anywhere and may slice monolithic content — but **must place some content on each fragmentainer** (no infinite empty pages).
- **BRK-13 [recommended]** (§best-breaks) Break as few times as possible; make non-forced-break fragmentainers equally full; avoid breaking inside replaced elements. Worked example: orphans 4, widows 2, 20 lines left: ≤20 lines → place; 21–22 lines → first fragment ≥4, second ≥2 (so 19/2 or 20/2 split, etc.); ≥23 lines → 20 lines then rest. orphans 10, widows 20, 8 lines left: ≥9-line block moves entirely.
- **BRK-14 [stable]** A **zero-sized box fragment must be placed before the break** if it fits (e.g. empty anchors/bookmark targets at page bottom stay on the earlier page) unless it follows content that itself overflows. Important for target-counter of empty `<a id>`.

### 2.6 Box model at breaks (§varying-size-boxes L863, §break-margins L974, §box-splitting L988)

- **BRK-15 [stable]** Varying-size fragmentainers: layout per fragmentainer with its own size; progress tracked as percentage of used/remaining extent and of content; intrinsic sizes computed once for the whole element (ICB-dependent intrinsic sizes use the first fragmentainer). Continuation fragments may not be positioned above the fragmentainer block-start. Consequence: stretch-fit/percentage-width boxes re-resolve inline size per page; min/max-content/fixed widths keep it. Monolithic elements may keep consistent sizes.
- **BRK-16 [stable] (L3)** Margins: at an **unforced** break, margins adjoining the break are **truncated to zero** (both before and after). At a **forced** break, margins before are truncated, margins **after are preserved**. Cloned margins on block-level boxes always truncated to zero.
- **BRK-17 [L4, unstable]** `margin-break: auto | keep | discard` (initial auto; applies to all elements). `auto` (L4 wording): unforced break → margins before the break truncate *to the remaining fragmentainer extent*, after → zero; forced → before truncated, after preserved. `keep` = never truncate. `discard` = always truncate incl. start/end of the fragmentation context (also used for inline margins at line edges). Two-keyword form (AH) is an open issue (#3254).
- **BRK-18 [stable]** When a box breaks, its content box **extends to fill the remaining fragmentainer extent** (minus cloned decorations) — i.e. a bordered box's slice reaches the page bottom; this extra extent counts toward `height`/`max-height` progress. L4 adds: a table cell / grid item spanning multiple rows split between rows should not extend into the inter-row gap.

### 2.7 `box-decoration-break` (§break-decoration L1015)

- **BRK-19 [stable]** `box-decoration-break: slice | clone`, initial slice, all elements, not inherited.
  - `slice`: as if laid out unbroken then cut; no border/padding inserted at breaks; no box-shadow on broken edges; backgrounds, border-radius, border-image apply to the **composite** geometry. Composite for pages: fragments glued in the root's block-flow direction; differing widths: each piece draws background assuming whole element has its width, except images whose size derives from box width use the **widest fragment** and stay fixed.
  - `clone`: each fragment independently wrapped with border+padding+margin (margins then truncated per BRK-16), border-radius/border-image/box-shadow per fragment, background drawn per fragment (no-repeat image appears in each).
  - Applies to line breaks of inline boxes too (broken edge determined by the **parent's** inline direction); should apply at bidi and block-in-inline splits, else treated as slice.
- **BRK-20 [stable]** (§transforms L1164) Fragmentation happens before relative positioning and transforms; these apply per fragment (each fragment gets its own transform origin). Transformed fragments spanning pages SHOULD print in full (sliced at page breaks) rather than clip. Abspos boxes fragment with their containing block's coordinate system; UAs need not correctly position boxes whose block-start depends on fragmentation, nor abspos elements landing on **already-emitted pages** (explicit permission for streaming UAs).

### 2.8 Table fragmentation (css-tables-3 §fragmentation L3264, recorded here for paginator design; detail in 05b)

- **BRK-21 [unstable but specific]** UA must try to keep a row unfragmented if its cells span no later row and the row height is < ½ of both fragmentainer height and width; others are *freely fragmentable*. If the first non-fitting row is not freely fragmentable (and ≥1 row fit), push it (insert gap). If freely fragmentable or no row fits, give all remaining space to that row's cells, fill each cell independently, continue each cell's content in the next fragment (**top borders not repainted** in continuation fragments).
- **BRK-22** `break-before/after` on row groups/rows insert the gap. Repeated footer comes directly after the last row in the fragmentainer; gap goes after the repeated footer.
- **BRK-23** Repeat `thead`/`tfoot` rows on each page spanned by the table when: the page is the table's fragmentainer; the header/footer has avoid `break-inside` (text at L3313 lists it as a condition — **de facto** Chromium (≥ M96 LayoutNG) and WeasyPrint/Prince repeat `thead` without requiring it — UNVERIFIED for the exact Chromium condition); total ≤ ½ page height (≤ ¼ each); no row shown twice on the page. Leave room for and render the table top/bottom border when repeating. UA may also repeat across columns.

---

## 3. GCPM 3 and css-content-3 (running content, footnotes, cross-refs, leaders, bookmarks)

### 3.1 Named strings (gcpm §named-strings L55; content-3 §named-strings L1046)

- **GC-1** `string-set: [ <custom-ident> <content-list> ]# | none` (GCPM; `<content-list> = [<string> | counter() | counters() | content() | attr()]+`), initial none, all elements **not pseudo-elements**, not inherited. css-content-3 (L1094) gives the *computed* form `[ <custom-ident> <string>+ ]#` (i.e. counters/content()/attr() are resolved to strings at computed-value time). Recto: parse the GCPM form, compute to strings.
- **GC-2** `content()` = `content( [ text | before | after | first-letter | marker ]? )` (GCPM omits `marker`). `text` (default) = element string value **as if `white-space: normal`** (collapse whitespace); `before`/`after` = string value of `::before`/`::after`; `first-letter` per `::first-letter`.
  Test: `h1::before{content:'Chapter ' counter(chapter)} h1{string-set: header content(before) ':' content(text)} h1::after{content:'.'}` ⇒ "Chapter 1:Loomings" (spec text shows "Chapter 1: Loomings" — whitespace literal in the example is inconsistent; recto concatenates literally).
- **GC-3** Assignment happens **when the element's content box is first created** (or would be, if `display:none` — so `display:none` elements *do* set strings — contrast counters, LS-6). Multiple assignments per page are recorded; UA must recall past/current/future values.
- **GC-4** Entry value of page = assignment in effect at end of previous page; exit value = in effect at end of current page.
- **GC-5** `string( <custom-ident> , [ first | start | last | first-except ]? )`:
  - `first` (default): first assignment on the page, else entry value.
  - `start`: if the element (the assigning element) is the **first element on the page**, use the first assignment; otherwise entry value. (De facto, WeasyPrint/Prince: "start" = value at the top of the page, i.e. includes an assignment only if the assigning element starts at the very top.)
  - `last`: exit value.
  - `first-except`: like `first`, but empty string on any page where the value is assigned.
- **GC-6** Style containment (`contain: style`) blocks `string-set` effects on descendants (content-3).

### 3.2 Running elements (gcpm §running-elements L262–L400)

- **GC-7** `position: running(<custom-ident>)` removes the element (with its `::before`/`::after`) from normal flow; it **inherits from its original position** but is not displayed there. Value of `element()` updated whenever a new element with that running name occurs.
- **GC-8** `content: element( <custom-ident> , [ first | start | last | first-except ]? )` — only in page-margin boxes, cannot be combined with other content values. Keyword semantics as `string()` (GC-5).
- **GC-9 [de facto]** Each page instantiates a *copy* of the running element in the margin box (the same running element may appear on many pages); counters inside (e.g. `counter(page)` in `::before`) evaluate in the margin box/page context. The `running` property / `:running` copy-mode (Bert Bos proposal) is in an issue block only — **not** to implement.

### 3.3 Footnotes (gcpm §footnotes L400–L700)

- **GC-10** `float: footnote` ⇒ (1) element removed from flow, `::footnote-call` inserted in its place; (2) `::footnote-marker` placed at the start of the footnote element (marker + element = footnote body); (3) **`footnote` counter incremented**; (4) body placed in the page's footnote area, in document order.
- **GC-11** `footnote-display: block | inline | compact` (initial block; applies to elements; not inherited). `compact`: UA chooses; footnotes that fit on one line should be inline.
- **GC-12** `@footnote` rule inside `@page` defines the footnote area (grammar not specified — issue). Bottom margin edge of footnote area touches bottom of page area; only footnotes may go there. `max-height` on `@footnote` limits it except when the page contains only footnotes; UA may set a default max-height.
- **GC-13** Footnote counter: predefined counter, any counter style; may be reset per page via `@page { counter-reset: footnote }`. **Value depends on document-tree position**, not placement (call and marker share the value even if the body moves to a later page).
- **GC-14** `::footnote-call` default: `content: counter(footnote)`, superscript (UA sheet Appendix B: `vertical-align: super; font-size: 65%`, or `font-variant-position: super` if supported). `::footnote-marker` behaves like `::marker` with `list-style-position: inside`; UA sheet `content: counter(footnote)` and `::footnote-marker::after { content: '. ' }`.
- **GC-15** `footnote-policy: auto | line | block` (initial auto): `auto` — body may move to a later page but **never before** the call's page; `line` — if body doesn't fit, force a page break before the line containing the call (respect widows/orphans, possibly earlier); `block` — force break before the paragraph containing the call. Spec explicitly lacks a footnote layout algorithm ("We need an algorithm for laying out footnotes"); a commented-out pseudo-code (L640–670) suggests: leftover footnotes first, footnote area grows from bottom, default max-height 75% of page area.

### 3.4 Page selectors & page groups (gcpm §the-first-page-pseudo-element L705)

- **GC-16 [unstable]** `:nth( <An+B> [of <custom-ident>]? )` page pseudo-class: plain = document page index (1-based, independent of `page` counter). `of NAME`: index within a **page group**. A page group is created when an element has `page: NAME` **and** a forced break; it is all pages created by that element instance; a new instance starts a new group; groups nest. Specificity of `:nth()` not defined in css-page-3 (de facto Prince/WeasyPrint count it like `:first` in `g`) — UNVERIFIED.

### 3.5 Cross-references (content-3 §cross-references L899)

- **CT-1** `target-counter( [ <string> | <url> ] , <custom-ident> , <counter-style>? )` — value of the **innermost** counter of that name *at the target element*; only same-document fragment URLs; missing fragment/ID or external URL ⇒ error (handling undefined; de facto: render nothing). Typical: `target-counter(attr(href url), page)` ⇒ page number on which the target is laid out (requires the `page` counter at the target's position, i.e. after pagination).
- **CT-2** `target-counters( [<string>|<url>], <custom-ident>, <string>, <counter-style>? )` — all nested counters joined by the string.
- **CT-3** `target-text( [<string>|<url>], [ content | before | after | first-letter ]? )` — text of the target element (`content` = `content(text)`).
- **CT-4 [implementation note]** These create a **layout dependency on pagination results**: changing a number's width can reflow the TOC page and shift targets. Standard practice (Prince, WeasyPrint, AH): iterate layout until page numbers stabilize (or 2–3 passes max).

### 3.6 Leaders (content-3 §leaders L734)

- **CT-5** `leader( dotted | solid | space | <string> )`: dotted=".", solid="_", space=" " (string form "Issue: Define this").
- **CT-6** Rules: leader string appears in full ≥ once; as long as possible; visible glyphs align vertically across lines when possible (i.e. aligned to a grid anchored at the **end edge**); line break chars ignored; white space per normal rules; leader only between before and after content; single line only; can't be alone on a line.
- **CT-7** Procedure: lay out before-content to its last line; tile the leader string from the **end edge toward the start edge** across the line; draw before/after content over it, hiding any leader glyph overlapped; if not one full copy visible, break after the before-content and draw leader + after-content on the next line. Open issues: after-content wider than line; leaders in tables. Implicit assumption: after-content end-aligned.

### 3.7 Bookmarks (content-3 §bookmark-generation L1305)

- **CT-8** `bookmark-level: none | <integer [1,∞]>` (initial none, all elements) — creates a bookmark iff not none. `bookmark-label: <content-list>` (initial `content(text)`). `bookmark-state: open | closed` (initial open; applies to block-level elements). Hierarchy needn't be strict (level 1 → 3 allowed). Activating = navigate to element (PDF outline destination = element's first fragment position). `display:none` behaviour is an open issue (de facto: no bookmark). GCPM UA sheet: `h1..h6 { bookmark-level: 1..6 }`.

### 3.8 `content` property bits relevant to margin boxes (content-3 §content-property L114)

- **CT-9** `content: normal | none | [ <content-replacement> | <content-list> ] [/ <alt-text>]?`; `<content-list>` includes `<string> | <image> | attr() | contents | <quote> | leader() | <target> | string() | content() | <counter> | <symbolic-counter-style>`; each item contributes an inline-level box. Single `<image>` ⇒ replaced content. `/ alt` text goes to the accessibility tree (→ PDF `/Alt` or `ActualText` in tagged PDF).

## 4. CSS Lists 3 — counters (affects page counters & target-counter)

- **LS-1** (§auto-numbering L740) Per element order: inherit counters → instantiate (`counter-reset`) → increment (`counter-increment`) → set (`counter-set`) → use. Clamp to implementation range.
- **LS-2** `counter-reset: [ <counter-name> <integer>? | reversed(<counter-name>) <integer>? ]+ | none` (default 0; reversed without value ⇒ computed at layout). Duplicate names: last wins. `counter-increment` (default +1) / `counter-set` (default 0): `[ <counter-name> <integer>? ]+ | none`; duplicates all processed in order (increments compound; last set wins); create the counter at 0 if absent. `none` is invalid as a counter name.
- **LS-3** (§inheriting-counters L1017) Inherit: counters set from **preceding sibling, else parent**; values from the **element immediately preceding in tree order**; keep only counters present in both (same name + creator).
- **LS-4** (§instantiating-counters L1112) Instantiate on element: if the innermost same-name counter was created by this element or a previous sibling, remove it; append new. (Siblings replace; ancestors nest.)
- **LS-5** Reversed counter without start: start = −(Σ negated increments up to a `counter-set`) + last non-zero negated increment (algorithm at L1150).
- **LS-6** (§counters-without-boxes L1172) Elements generating no box (`display:none`, pseudo with `content:none`) **cannot** set/reset/increment counters. `visibility:hidden` still counts.
- **LS-7** (§list-item-counter L1206) List items implicitly increment `list-item` by 1 (−1 if reversed) unless `counter-increment` names `list-item` explicitly.
- **LS-8** (§counter-functions L1346) `counter(name, style?)`, `counters(name, sep, style?)`; default style `decimal`; using a non-existent counter instantiates it at 0 on that element.

## 5. CSS Page Floats 3 (all **[unstable]**)

- **PF-1** `float-reference: inline | column | region | page` (initial inline). Non-inline references create a *page float* in a new BFC sized like the reference.
- **PF-2** `float` extended: `block-start | block-end | inline-start | inline-end | snap-block | snap-block(<length>{1,2}, [start|end|near]?) | snap-inline | snap-inline(...) | left | right | top | bottom | none`. `snap-block` = `snap-block(2em, near)`; on tie `end` wins.
- **PF-3** `clear` extended with `block-start/-end, inline-start/-end, top, bottom, both-inline, both-block, both, all` (`all` appears in prose, not grammar); on page floats, clear closes the reference for subsequent floats in that direction.
- **PF-4** `float-defer: <integer> | last | none` (deferral to Nth next / Nth-from-last fragmentainer); `float-offset: <length-percentage>` (pushes float away from its edge; % = (cb − float size) × p).
- **PF-5** Placement order: all `page`-reference floats first (document order), then column/region floats; per float: initial reference (anchor + defer) → advance to next fragmentainer until it fits (growing to max size) → add a fragmentainer if possible. Stacking: in order of placement, no overlap, spacing N = float-offset. Block-direction floats assumed full inline size for space accounting.

---

## Findings that affect recto's design

1. **Pagination needs two-plus passes by spec, not by choice.** `counter(pages)` (PG-35), `target-counter(..., page)` (CT-1), `string(…, last)`/`element(…, last)` (exit values, GC-4/GC-5) and footnote placement all depend on the final page assignment. Design the paginator so margin boxes are laid out **after** the page's body content is fixed (they don't affect body layout: margin box sizes depend only on page margins and their own content), and so `pages` is substituted at emission. For streaming emission, `counter(pages)` blocks streaming unless rendered as a deferred PDF object (e.g. a Form XObject per distinct digit-width placeholder) — recommend: buffer only margin-box rendering, or reserve width using the max digit width and patch the content stream at the end (deterministic). target-counter in TOCs *before* the target requires a relayout loop (CT-4) — cap at N iterations (Prince-like), deterministic.
2. **Margin boxes are a self-contained algorithm (PG-28/PG-29)** needing only min-content/max-content widths of a block-level box; implement as a pure function `(available, [A,B,C] intrinsic sizes, specified widths, min/max) → (widths, x-positions)` with golden tests from the examples. Corner boxes use fixed rules on both axes.
3. **Page context cascade is ordinary cascade with page specificity (f,g,h)** (PG-15/16): compute styles per *page* (per (name, first, blank, left/right, nth) combination), cacheable by that key — the number of distinct page styles in an invoice is tiny.
4. **Page context inherits from the root element** (PG-21) and percentages for vertical margins use page **height** (PG-23) — differs from regular blocks; easy to get wrong.
5. **Break model = class A/B/C + Rules 1–4 + ordered relaxation** (BRK-10–BRK-12): implement breaking as "find the last allowed break point that fits, with a penalty-ordered fallback". The relaxation order is normative: (orphans/widows) → (avoid rules) → (truncate cloned decorations) → (break anywhere, always progress). Guarantee ≥1 piece of content per page (no infinite loops) — matches recto's "memory/time caps" goal.
6. **Break propagation from first/last child** (BRK-9) and **named-page start/end propagation** (PG-45) share the same "first/last in-flow child" walk; compute both in the box-tree build phase.
7. **Margin truncation** (BRK-16): unforced break → zero both sides; forced break → keep the margin after. Matches Chromium/WeasyPrint print output that authors expect (`h1 { margin-top: 2cm; break-before: page }` keeps 2 cm). Do not implement L4 `margin-break` in v1 except perhaps `discard`.
8. **Box splitting fills the remaining extent** (BRK-18) and `box-decoration-break: slice` composite backgrounds — invoices with bordered/background boxes spanning pages need both; `clone` is cheap once fragments are independent.
9. **Zero-height fragments stay before the break** (BRK-14): anchors (`<a id>` targets for TOC links/bookmarks) at a page bottom must resolve to the earlier page.
10. **Table header/footer repetition** is the single most important fragmentation feature for invoices/statements (BRK-23). The spec's conditions (≤¼ page each, break-inside:avoid on the group) are stricter than what Chromium/WeasyPrint users expect; recommend: always repeat `thead`/`tfoot` (`display: table-header-group/footer-group`) when it fits within ¼ page, behind a compat note. Rows < ½ page are kept unsplit (BRK-21).
11. **Running elements** (GC-7/GC-9) mean a running element's box subtree must be re-laid-out per page inside the margin box (with page-dependent counters); store running elements as styled subtrees keyed by (name, document position) and select per page with first/start/last/first-except.
12. **Named strings are set even for `display:none` elements but counters are not** (GC-3 vs LS-6) — the classic `<meta>`/`<title>` → `string-set` trick relies on this.
13. **Footnotes have no normative layout algorithm** (GC-15): if implemented, follow the de facto Prince/WeasyPrint model (footnote area grows up from page-area bottom, call and body on the same page by default, push the call's line if the body doesn't fit).
14. **Legacy `page-break-*`** must be supported as aliases (BRK-8): wkhtmltopdf-era templates use `page-break-before: always` / `page-break-inside: avoid` overwhelmingly.
15. **`size` per named page + `page-orientation`** map directly onto PDF per-page MediaBox and `/Rotate`; bleed/marks map to BleedBox/TrimBox — straightforward in a PDF writer, useful for labels/tickets/certificates.
16. **Abspos content on previously-emitted pages need not be positioned correctly** (BRK-20) — explicit spec permission that supports recto's streaming page emission.

## Recommendation — "Requirements recto v1 must implement" vs "defer"

### Must implement in v1
| Req | Justification (document generation) |
|---|---|
| PG-1…PG-7, PG-9…PG-11 page model, painting order, left/right/first-page side | Every invoice/report; duplex margins for reports. |
| PG-12…PG-19 `@page` grammar, `:first/:left/:right/:blank`, named page selectors, specificity, cascade | Cover pages without header (`@page :first`), mirrored margins. |
| PG-20…PG-25 page/margin context property semantics, defaults table | Headers/footers look right with zero author CSS. |
| PG-26…PG-30 margin box geometry incl. exact variable/fixed algorithms | Core differentiator vs wkhtmltopdf; must match Prince/WeasyPrint/Chromium pixel-for-pixel on common cases. |
| PG-31…PG-35 `page`/`pages` counters, page-context counters, document counters in margin boxes | "Page X of Y", chapter in header. |
| PG-36…PG-41 `size` (keywords + lengths + orientation), media-query exclusion, `page-orientation`, `marks`/`bleed` (cheap PDF boxes) | Labels, tickets, A4/Letter switching; marks/bleed are ~trivial with PDF boxes. |
| PG-44…PG-45 named pages via `page` | Landscape table pages in reports, distinct cover/back pages. |
| BRK-1…BRK-16, BRK-18, BRK-19, BRK-20 entire Fragmentation L3 | The paginator's contract. |
| BRK-21…BRK-23 table fragmentation + header/footer repetition | Multi-page invoices/statements. |
| GC-1…GC-6 `string-set`/`string()`/`content()` | Running headers ("Statement for ACME"). |
| GC-7…GC-9 `position: running()` + `element()` | Rich HTML headers/footers (logos, tables) — what Puppeteer `headerTemplate` users need. |
| CT-1…CT-4 `target-counter()`/`target-counters()`/`target-text()` | TOCs, "see page N" — explicitly in brief. |
| CT-5…CT-7 `leader()` (dotted/solid/space/string) | TOCs. |
| CT-8 `bookmark-level/label/state` (+ GCPM UA sheet h1–h6) | PDF outlines — explicitly in brief. |
| LS-1…LS-8 counters per css-lists-3 | Numbered clauses in contracts, list numbering. |
| BRK-8 legacy `page-break-*` aliases | Compat with wkhtmltopdf templates. |

### Defer (post-v1)
| Req | Justification |
|---|---|
| GC-10…GC-15 footnotes (`float: footnote`, `@footnote`, `footnote-policy/display`) | No normative algorithm; rare in invoices/receipts; moderate in contracts/reports → good v1.x candidate after core pagination is stable. |
| GC-16 `:nth()` page selector & page groups | Exploring; workaround via named pages + `:first` of a named page group is not in L3 either — v1.x if users ask. |
| BRK-17 `margin-break` (L4), BRK-5 L4 `always`/`all` | Exploring / at-risk. (`always` is trivial to alias to `page`/`column` if cheap.) |
| PG-42 `page-margin-safety` | Spec bug in initial value; printers not targeted. |
| PF-1…PF-5 page floats (`float: top/bottom` with `float-reference: page`) | Exploring, little interop; figure placement in reports can use breaks. |
| Regions-related values (`region`, `avoid-region`) | Parse and ignore (no region contexts). |
| GC-9 `running` property / `:running` copy semantics | Issue-only proposal. |

## Open questions / UNVERIFIED items

1. **UNVERIFIED**: exact Chromium/WeasyPrint/Prince condition for repeating `thead`/`tfoot` vs css-tables-3's "header/footer has avoid break-inside" requirement (BRK-23). Needs WPT `css/css-break/table/` or engine source inspection (not done here).
2. **UNVERIFIED**: de facto semantics of `string(x, start)` when the assigning element is not first on the page but the page starts mid-element; and specificity of `:nth()` (GC-16).
3. css-page-3 says margin-box `content: normal` → `none` (L1029, L1462), css-content-3 says `normal` → `contents` for page-margin boxes (L134-ish, "For a regular element or page-margin box, this computes to contents"). Conflict; recto follows css-page-3 (box not generated) because that's what all print engines do.
4. `string-set` value grammar differs between GCPM (`<content-list>`) and css-content-3 (`<string>+` — which is the *computed* form). Recto should accept GCPM syntax.
5. css-break-4 `margin-break: auto` text says margins before an unforced break "truncate to the remaining fragmentainer extent" whereas L3 says "truncated to zero" — affects whether trailing margins can push a fragmentainer's content; L3 behaviour recommended for v1.
6. `pages` counter in streaming mode: whether recto pre-computes total pages (requires full layout before first page emission) or patches — design decision for the lead (see Finding 1).
7. Spec does not say whether `@page` `width`/`height` (PG-2) are honoured by browsers; Chromium ignores them (UNVERIFIED); Prince honours. Low priority.
8. No per-directory history before 2023-01-01 was fetched (shallow clone since 2023); "last commit" dates above are accurate since each is after that date.
