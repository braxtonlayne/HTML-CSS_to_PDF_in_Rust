# Phase 1 drafting plan (shared by all spec-drafting agents)

Read in this order before writing anything:
1. /home/user/Placeholder_name/docs/spec/CONVENTIONS.md: item format, prefixes, test locations. MANDATORY.
2. /home/user/Placeholder_name/docs/research/00-SYNTHESIS.md: all foundational decisions. NORMATIVE; do not contradict it.
3. /home/user/Placeholder_name/docs/spec/02-architecture-overview.md: crates, core types, contracts, error model. NORMATIVE.
4. The research docs relevant to your documents (docs/research/NN-*.md). Cite them as [R06 §5] etc.
5. This file: milestones, ADR numbers, anchor IDs.

## Milestones (every item gets exactly one)

| ID | Name | Exit criteria (summary) |
|---|---|---|
| M0 | Hello PDF | Workspace, CI, `recto render hello.html -o hello.pdf` with a bundled font; one page; deterministic; golden raster harness works |
| M1 | Block text with page breaks | Full block + inline layout of styled text (multiple fonts, bidi, line-height, text-align), the fragmentation engine (break tokens, forced/avoid breaks, orphans/widows), @page size/margins, :first/:left/:right/:blank, backgrounds/borders, @font-face, text dump snapshots, WPT print reftest runner |
| M2 | Invoice-complete | Tables (auto/fixed/collapse, thead/tfoot repeat), floats, relative/absolute/fixed positioning, flex (taffy), margin boxes, counters incl. page/pages, string-set, running elements, images (PNG/JPEG), SVG, lists, ::before/::after, URI links, template+JSON data mode, typical invoice templates render correctly |
| M3 | Report-complete: tables, images, TOC | target-counter/target-text, leader(), bookmarks/outline, internal links, named pages, table row splitting + rowspans across pages, grid (monolithic), hyphens:auto, more image formats, box-shadow, performance targets met, network fetching (`net`), counting allocator |
| M4 | Server + bindings | HTTP server (JSON/multipart/async jobs/health/metrics/limits), worker processes, C ABI, Node, Python, WASM, thin clients, asset bundles, Docker image, release pipeline |
| M5 | Accessibility + archival | Tagged PDF by default, PDF/UA-1, PDF/A-1b/2b/2u/3b/3a, attachments, Factur-X/ZUGFeRD, veraPDF CI |
| M6 | Polish, compat shims, 1.0 | wkhtmltopdf shim, Puppeteer/Gotenberg compat, watch + live preview, footnotes, multicol, grid fragmentation, :nth() pages, barcodes, krilla streaming patch, sandboxing, docs + migration guides, 1.0 release |

Rules: an item's dependencies must be in the same or an earlier milestone. Schedule work as early as the milestone exit criteria require and no earlier.

## ADR numbers (written by the lead in spec/35; reference as [ADR-00NN])

0001 working name "recto" · 0002 own fragmenting layout engine, taffy only for flex/grid · 0003 break-token layout contract + streaming page loop · 0004 Au = i32 1/64 px · 0005 own inline layout on harfrust/icu_segmenter/unicode-bidi/hypher · 0006 krilla PDF backend · 0007 html5ever + own arena DOM · 0008 own cascade on cssparser+selectors · 0009 usvg sandboxed + krilla-svg · 0010 image formats & JPEG passthrough · 0011 two fontations lines; usvg follows krilla-svg · 0012 two-phase finalization & streaming emission · 0013 forward-reference bounded relayout · 0014 font sources, system fonts defaults, bundled fonts · 0015 tagged PDF on by default · 0016 grid: monolithic M3, fragmentation M6 · 0017 multicol basic in v1 · 0018 SVG text via usvg text feature · 0019 footnotes in v1 · 0020 page floats deferred · 0021 thead/tfoot repetition rule · 0022 form controls static, no AcroForm · 0023 encryption deferred · 0024 default page size/margins & per-entry-point compat defaults · 0025 barcodes via `recto-barcode:` URL scheme · 0026 MathML deferred · 0027 letter-spacing browser model default · 0028 minijinja template engine · 0029 single Fetcher, deny-by-default; lenient (CLI/lib) vs strict (server) · 0030 server supervisor + worker processes · 0031 binding strategy (native Node/Python/WASM/C-ABI/.NET; thin Go/PHP/Ruby/Java) · 0032 single RenderOptions schema (camelCase + snake aliases) · 0033 hayro test rasterizer, no AGPL tooling · 0034 MSRV 1.92, edition 2024 · 0035 hyphenation language set (no Slovak) · 0036 HTTP client choice · 0037 clap + hand-written wkhtmltopdf argv parser · 0038 determinism rules & --reproducible · 0039 horizontal-tb only (vertical writing deferred) · 0040 default media `print` (native), `screen` in wkhtmltopdf shim · 0041 error codes & exit classes · 0042 axum/tokio server stack · 0043 license policy · 0044 letterhead/background PDF import opt-in · 0045 position:fixed repeats per page; sticky = relative · 0046 transforms/effects scope (2D transforms, opacity, shadows, gradients, blend modes yes; filters no)

If your document needs a decision not on this list, write it under a final section `## ADR proposals` in your document with the template: `### PROPOSED: <title>` / Context / Decision / Alternatives considered / Consequences. The lead assigns numbers and moves it into spec/35. Until then, reference it as [ADR-PROPOSED: <title>].

## ID ranges per document (prefixes shared by two docs are split by range)

CSS: 04 → 001–199, 04b → 200–399. LAY: 06 → 001–199, 06b → 200–399. FLT and POS both live in 09. IMG and SVG both live in 15. Every other prefix is owned by exactly one document (see CONVENTIONS §2), which may use 001–999. Number in steps of 10 (or 5) to leave room for insertions. Anchors below are fixed. Choose other numbers so document order roughly increases, but order in the document is what counts.

## Anchor IDs: you MUST define these exactly (same ID; title may be refined; milestone fixed)

Other documents may depend on anchors before they exist. Cross-document dependencies may ONLY target anchor IDs (or IDs in spec/02: ARC-001…ARC-015). Within your own document, depend on anything you define. If you need something from another document that has no anchor, add an entry under a final section `## Cross-doc requests` (needed ID prefix, what, why); the lead resolves it in the consistency pass.

### 03 DOM
DOM-010 Parse UTF-8 HTML into the arena DOM via an html5ever TreeSink (M0) · DOM-020 Implement encoding sniffing (BOM, override, meta prescan, UTF-8 default) (M1) · DOM-030 Enforce DOM depth/node/attribute caps in the sink (M1) · DOM-040 Track source lines for DOM nodes and parse errors (M1) · DOM-050 Parse XHTML input via xml5ever (M3) · DOM-060 Provide the DOM query API: id index, lang resolution, attribute access, text content (M0)

### 04 CSS parsing (001–199)
CSS-010 Parse stylesheets into rules/declarations with source locations (M0) · CSS-020 Implement the property registry with longhand/shorthand expansion (M0) · CSS-030 Parse lengths, percentages, numbers, colors (M0) · CSS-040 Evaluate @media (print/screen, width/height/orientation, resolution) (M1) · CSS-050 Parse @page rules, page selectors and the 16 margin at-rules (M1) · CSS-060 Parse @font-face descriptors (M1) · CSS-070 Resolve @import through the Fetcher (M2) · CSS-080 Parse GCPM content functions (counter, counters, string, element, target-counter(s), target-text, leader, content(), running()) (M2) · CSS-090 Emit unsupported-property/value warnings with locations (M1) · CSS-100 Parse custom properties and var() references (M2)

### 04b Cascade & computed values (200–399)
CSS-210 Compute styles for the M0 property subset (display, margin, padding, color, font-size, font-family, line-height) (M0) · CSS-220 Implement selectors::Element for the arena DOM with a rule index (M0) · CSS-230 Ship the UA stylesheet (HTML defaults + print) (M0) · CSS-240 Implement inheritance and CSS-wide keywords (initial/inherit/unset/revert/revert-layer) (M1) · CSS-250 Implement the full cascade (origins, importance, layers, specificity, order, style attribute) (M1) · CSS-260 Compute box-model property values (M1) · CSS-270 Compute font property values (M1) · CSS-280 Substitute var() at computed-value time with cycle detection and expansion caps (M2) · CSS-290 Implement the page-context cascade with page selector specificity (M1) · CSS-300 Share and deduplicate computed styles (Arc + hash) (M3) · CSS-310 Compute pseudo-element styles (::before, ::after, ::marker, ::first-line, ::first-letter, ::footnote-call/marker) (M2) · CSS-320 Evaluate calc()/min()/max()/clamp() (M2)

### 05 Box tree
BOX-010 Generate block and inline boxes with anonymous block wrapping for display block/inline/none (M0) · BOX-020 Implement complete anonymous box fixups (inline-in-block, block-in-inline splitting) (M1) · BOX-030 Generate ::before/::after boxes (M2) · BOX-040 Generate list-item marker boxes (M2) · BOX-050 Implement anonymous table object fixup (CSS 2.1 §17.2.1) (M2) · BOX-060 Support display flex/grid/inline-block/flow-root/contents/inline-flex/inline-grid (M2) · BOX-070 Create out-of-flow placeholders (float, abspos, fixed, running, footnote) (M2) · BOX-080 Precompute break-value and named-page propagation (first/last child) (M1) · BOX-090 Generate replaced-element boxes (img, svg, object/embed fallback, form controls static) (M2)

### 06 Block layout (001–199)
LAY-010 Lay out stacked block boxes without fragmentation (M0) · LAY-020 Define ConstraintSpace, LayoutResult, BreakToken and fragment types (M1) · LAY-030 Implement margin collapsing (M1) · LAY-040 Resolve widths/heights, min/max, box-sizing, auto margins (M1) · LAY-050 Fragment block containers with break tokens (M1) · LAY-060 Define BoxFragment/PageFragment output types (M0) · LAY-070 Compute block intrinsic sizes (min/max-content) (M2) · LAY-080 Cache layout and intrinsic sizes (M3) · LAY-090 Implement box-decoration-break slice/clone (M3) · LAY-100 Implement overflow and clipping semantics (M2)

### 06b Inline layout (200–399)
LAY-210 Lay out a single-style paragraph with greedy line breaking (M0) · LAY-220 Collect inline items with white-space processing (phase I/II) (M1) · LAY-230 Build line boxes with strut, half-leading and vertical-align (M1) · LAY-240 Implement the resumable line breaker with per-line available width (M1) · LAY-250 Paint-ready inline box decorations sliced across lines (M2) · LAY-260 Implement text-align, justify, text-align-last, text-indent (M1) · LAY-270 Fragment inline formatting contexts with InlineBreakToken (M1) · LAY-280 Place atomic inlines (inline-block, images) in lines (M2) · LAY-290 Implement ::first-line and ::first-letter (M3) · LAY-300 Compute IFC intrinsic sizes (M2)

### 07 Flex / 07b Grid
FLX-010 Implement the taffy adapter (Au↔f32, tree traits, child dispatch) (M2) · FLX-020 Lay out flex containers monolithically (M2) · FLX-030 Fragment row flex containers between lines and across items (M3) · FLX-040 Fragment column flex containers (M3)
GRD-010 Lay out grid containers monolithically via taffy (M3) · GRD-020 Fragment grid containers between rows (M6)

### 08 Tables
TBL-010 Build the table grid model (rows, columns, spans, groups) (M2) · TBL-020 Implement the auto table layout algorithm (M2) · TBL-030 Implement fixed table layout (M2) · TBL-040 Implement border-collapse with CSS2 conflict resolution (M2) · TBL-050 Compute row heights and cell vertical-align (M2) · TBL-060 Fragment tables between rows (M2) · TBL-070 Repeat thead/tfoot on each fragment (M2) · TBL-080 Split rows across fragmentainers (M3) · TBL-090 Handle rowspans across fragmentainers (M3) · TBL-100 Lay out table captions (M2)

### 09 Floats & positioning
FLT-010 Implement the exclusion space and float placement (M2) · FLT-020 Implement clearance (M2) · FLT-030 Shorten line boxes around floats (M2) · FLT-040 Fragment floats across pages (M3)
POS-010 Implement relative positioning (M2) · POS-020 Implement absolute positioning (M2) · POS-030 Repeat position:fixed boxes on every page (M2) · POS-040 Build stacking contexts and z-order lists (M2)

### 10 Multicol
COL-010 Lay out multicol containers with fixed column count/width (M6) · COL-020 Balance column heights (M6) · COL-030 Continue multicol content across pages (M6)

### 11 Fragmentation
PAG-010 Implement paginate() with the progress guarantee (M1) · PAG-020 Snapshot PageState and deliver pages to a PageConsumer (M1) · PAG-030 Implement forced breaks incl. legacy page-break-* aliases (M1) · PAG-040 Implement break classes A/B/C and best-break rewind (M1) · PAG-050 Implement orphans and widows (M1) · PAG-060 Implement break-inside: avoid (M1) · PAG-070 Truncate margins at unforced breaks, keep after forced (M1) · PAG-080 Implement break-after/before: avoid (keep-with-next) (M1) · PAG-090 Enforce max_pages and no-progress guards (M1) · PAG-100 Support column fragmentainers in the break machinery (M1)

### 12 Paged media
PGM-010 Compute page geometry from @page size and margins (M1) · PGM-020 Implement :first/:left/:right/:blank page selectors (M1) · PGM-030 Lay out the 16 page-margin boxes (M2) · PGM-040 Resolve counters and strings inside margin boxes from PageState (M2) · PGM-050 Implement bleed and crop/cross marks (M3) · PGM-060 Implement named pages (page property) (M3) · PGM-070 Implement :nth() page selectors and page groups (M6) · PGM-080 Implement page-orientation (M3) · PGM-090 Implement the CLI page-geometry override layer (M2) · PGM-100 Bind header/footer HTML templates to page margin areas (compat) (M6)

### 13 Generated content / 13b Footnotes
GEN-010 Implement counters (reset/increment/set, counter(), counters(), scoping) (M2) · GEN-020 Implement content strings, attr(), quotes (M2) · GEN-030 Implement list-style-type counter styles (M2) · GEN-040 Implement counter(page) and counter(pages) (M2) · GEN-050 Implement string-set and string() (M2) · GEN-060 Implement running elements and element() (M2) · GEN-070 Statically analyse page-dependent content for deferral (M2) · GEN-080 Implement bookmark-level/label/state (M3) · GEN-090 Implement leader() (M3) · GEN-100 Implement target-counter/target-counters/target-text (M3) · GEN-110 Record forward-reference resolution data for relayout (M3)
FTN-010 Lay out the footnote area and float: footnote (M6) · FTN-020 Generate footnote calls and markers (M6) · FTN-030 Implement footnote-policy and footnote-display (M6)

### 14 Text / 14b Fonts
TXT-010 Shape a single-font LTR run with harfrust (M0) · TXT-020 Itemize text by script, bidi level, font and style (M1) · TXT-030 Apply the Unicode bidi algorithm with CSS direction/unicode-bidi (M1) · TXT-040 Compute line-break opportunities with icu_segmenter and CSS options (M1) · TXT-050 Implement hyphens: manual (soft hyphens) (M1) · TXT-060 Implement hyphens: auto with hypher (M3) · TXT-070 Implement letter-spacing and word-spacing (M2) · TXT-080 Implement text-transform (M2) · TXT-090 Map font-variant-*/font-feature-settings to OpenType features (M2) · TXT-100 Reshape at line edges (unsafe-to-break) (M1) · TXT-110 Compute text-decoration geometry (M2) · TXT-120 Fall back to nominal-glyph shaping for malformed fonts (M2) · TXT-130 Implement text-wrap: pretty (Knuth–Plass) (M6) · TXT-140 Implement tab stops (tab-size) (M2)
FNT-010 Load a bundled font and expose metrics (M0) · FNT-020 Build the font database with sorted scanning and stable FontId (M1) · FNT-030 Implement CSS Fonts 4 §5 font matching (M1) · FNT-040 Load @font-face fonts (TTF/OTF/TTC from files and data:) (M1) · FNT-050 Decode WOFF/WOFF2 (M2) · FNT-060 Implement per-cluster font fallback (M1) · FNT-070 Discover system fonts without fontconfig (M2) · FNT-080 Synthesize bold and oblique (M2) · FNT-090 Support variable fonts (M3) · FNT-100 Support color/emoji fonts (M3) · FNT-110 Bundle the default font set with licenses (M1) · FNT-120 Compute vertical metrics and line-height: normal (M1)

### 15 Images & SVG
IMG-010 Probe image format and dimensions with limits before decoding (M2) · IMG-020 Decode PNG (M2) · IMG-030 Pass JPEG through as DCT (M2) · IMG-040 Decode GIF/WebP/BMP (M3) · IMG-050 Apply EXIF orientation and extract ICC profiles (M3) · IMG-060 Implement object-fit/object-position/image-rendering (M3) · IMG-070 Render CSS background-image (raster) (M2)
SVG-010 Parse SVG in the sandbox via roxmltree+usvg (M2) · SVG-020 Render inline <svg> elements (M2) · SVG-030 Render SVG as image (img src, background-image) (M2) · SVG-040 Generate barcodes via the recto-barcode: scheme (M6)

### 16 PDF / 16b Paint
PDF-010 Emit a page with text and an embedded subset font through krilla (M0) · PDF-020 Implement the PdfWriter add_page/finish API (M1) · PDF-030 Make PDF output deterministic (document ID, dates, ordering) (M0) · PDF-040 Embed raster images (M2) · PDF-050 Emit vector paths, fills, strokes, clips (M1) · PDF-060 Emit URI link annotations (M2) · PDF-070 Emit internal links and named destinations (M3) · PDF-080 Embed SVG via krilla-svg (M2) · PDF-090 Write Info dictionary and XMP metadata (M1) · PDF-100 Write MediaBox/BleedBox/TrimBox (M3) · PDF-110 Build the outline from bookmarks (M3) · PDF-120 Write page labels (M3) · PDF-130 Deduplicate repeated content as XObjects (M3) · PDF-140 Stream PDF output via the krilla patch (M6) · PDF-150 Write viewer preferences (M6) · PDF-160 Enforce max_output_bytes (M2) · PDF-170 Import background/letterhead PDF pages (M6)
PNT-010 Define DisplayList and paint glyph runs (M0) · PNT-020 Paint background colors (M1) · PNT-030 Paint borders (all styles) (M1) · PNT-040 Paint in CSS 2.1 Appendix E stacking order (M2) · PNT-050 Paint gradients (M2) · PNT-060 Paint box-shadow (M3) · PNT-070 Apply opacity and 2D transforms (M2) · PNT-080 Apply overflow clipping and border-radius clipping (M2) · PNT-090 Emit link and destination display items (M2) · PNT-100 Emit tag and artifact marks (M5)

### 17 Accessibility & archival
ACC-010 Build the structure tree from HTML semantics (M5) · ACC-020 Tag headings, paragraphs, lists, links (M5) · ACC-030 Tag tables with headers/scope (M5) · ACC-040 Tag figures with alt text (M5) · ACC-050 Mark margin boxes and decorations as artifacts (M5) · ACC-060 Implement the PDF/UA-1 profile (M5) · ACC-070 Implement PDF/A profiles (M5) · ACC-080 Embed file attachments (M5) · ACC-090 Produce Factur-X/ZUGFeRD invoices (M5) · ACC-100 Validate with veraPDF in CI (M5) · ACC-110 Set document language and title (M5)

### 18 CLI / 18b compat
CLI-010 Implement `recto render <in> -o <out>` (M0) · CLI-020 Map all RenderOptions to flags (M2) · CLI-030 Support stdin/stdout (M1) · CLI-040 Implement exit codes and stderr diagnostics (M1) · CLI-050 Implement batch rendering with --data (M2) · CLI-060 Generate shell completions and man pages (M6)
CMP-010 Parse wkhtmltopdf argv (M6) · CMP-020 Map wkhtmltopdf options and defaults (M6) · CMP-030 Emulate smart shrinking via fit-to-width scale (M6) · CMP-040 Render wkhtmltopdf header/footer HTML with variable substitution (M6) · CMP-050 Translate Puppeteer/Playwright PDFOptions (M6) · CMP-060 Serve Gotenberg-compatible routes (M6)

### 19 Server / 20 API / 21 Bindings / 22 Templating
SRV-010 Serve POST /v1/render with JSON input (M4) · SRV-020 Accept multipart uploads (M4) · SRV-030 Run jobs in a worker process pool (M4) · SRV-040 Provide async jobs (M4) · SRV-050 Provide health and metrics endpoints (M4) · SRV-060 Enforce concurrency limits and timeouts (M4)
API-010 Publish the Engine/RenderOptions/Input API (M1) · API-020 Derive serde and JSON Schema for RenderOptions (M2) · API-030 Provide streaming output sinks (M3) · API-040 Provide a resource resolver callback (M4) · API-050 Enforce the semver policy with public-api checks (M4)
BND-010 Expose the C ABI with a generated header (M4) · BND-020 Ship the Node binding (napi-rs) (M4) · BND-030 Ship the Python binding (PyO3) (M4) · BND-040 Ship the WASM build (M4) · BND-050 Ship thin Go/PHP/Ruby/Java clients (M4) · BND-060 Ship the .NET binding over the C ABI (M4)
TPL-010 Render a minijinja template with JSON data to HTML (M2) · TPL-020 Render JSONL batches to multiple PDFs (M2) · TPL-030 Load asset bundles into an in-memory VFS (M4) · TPL-040 Enforce template limits and escaping (M2)

### 23 Security / 23b Net / 24 Limits / 25 Determinism
SEC-010 Prove every ResourceKind is policy-checked (table test) (M0) · SEC-020 Allowlist link URI schemes in PDF output (M2) · SEC-030 Assert no JavaScript/Launch/OpenAction can be emitted (M2) · SEC-040 Deny hidden and special files (M1) · SEC-050 Apply a Landlock sandbox in the CLI (M6) · SEC-060 Apply seccomp to server workers (M4) · SEC-070 Maintain the security regression corpus (M3)
NET-010 Implement Policy, Fetcher and ResourceKind (M0) · NET-020 Resolve file: URLs within allowed roots (M0) · NET-030 Decode data: URLs (M1) · NET-040 Implement HTTP(S) fetching behind the net feature (M3) · NET-050 Enforce the IP denylist with pinning and redirect re-validation (M3) · NET-060 Provide the in-memory VFS (M2) · NET-070 Cache resources by content hash across jobs (M3)
LIM-010 Define Limits with CLI/server/library profiles (M0) · LIM-020 Enforce DOM/CSS caps (M1) · LIM-030 Enforce image and decompression caps (M2) · LIM-040 Implement the counting allocator (M3) · LIM-050 Enforce the page cap (M1) · LIM-060 Apply worker RLIMIT_AS and kill-on-deadline (M4) · LIM-070 Implement wall-clock and fetch timeouts (M3)
DET-010 Assert byte-identical double renders in the harness (M0) · DET-020 Implement SOURCE_DATE_EPOCH and --reproducible (M1) · DET-030 Run cross-architecture golden hash CI (M3) · DET-040 Check fontations-line glyph agreement (M2)

### 26 Perf / 27 Testing / 28 Diagnostics / 29 DX / 30 Deployment / 31–33 Docs
PERF-010 Build the benchmark harness and corpus (M1) · PERF-020 Meet cold start < 100 ms (M3) · PERF-030 Meet 100-page batch < 1 s (M3) · PERF-040 Prove memory linear in page count (M3) · PERF-050 Gate CI on performance regressions (M3)
TST-010 Build the render → rasterize → golden compare harness (M0) · TST-020 Build the layout snapshot harness (M1) · TST-030 Build the PDF structure check harness (M1) · TST-040 Run WPT print reftests with expectations (M1) · TST-050 Port WeasyPrint tests (tooling + first batch) (M1) · TST-060 Set up fuzz targets and CI smoke fuzzing (M1) · TST-070 Maintain the real-world smoke corpus (M2) · TST-080 Store compat reference outputs (M6)
DBG-010 Dump box and fragment trees as text (--explain) (M1) · DBG-020 Format unsupported-CSS warnings (M1) · DBG-030 Render --debug-overlay (M3) · DBG-040 Trace page-break decisions (M3) · DBG-050 Emit structured logs via tracing (M2)
DX-010 Implement `recto watch` (M6) · DX-020 Serve a live preview with hot reload (M6) · DX-030 Render error messages with source snippets (M3) · DX-040 Ship a VS Code preview extension (M6)
DEP-010 Set up the CI pipeline (M0) · DEP-020 Build static musl release binaries (M4) · DEP-030 Publish the FROM scratch Docker image (M4) · DEP-040 Release via cargo-dist (M4) · DEP-050 Publish Homebrew and cargo-binstall metadata (M6) · DEP-060 Produce SBOMs and signatures (M6)
DOC-010 Set up the user documentation site (M1) · DOC-020 Publish the error code reference (M2) · DOC-030 Generate the CSS support reference (M3) · DOC-040 Publish migration guides (M6) · DOC-050 Publish the compatibility matrix (M6)

## Agent assignments

| Agent | Documents |
|---|---|
| A1 | 03-html-parsing-and-dom.md, 04-css-parsing.md (title: "CSS parsing, property registry and values"), 04b-css-cascade-and-computed-values.md |
| A2 | 05-box-tree-generation.md, 06-layout-block.md, 06b-layout-inline.md |
| A3 | 07-layout-flex.md, 07b-layout-grid.md, 09-layout-floats-and-positioning.md |
| A4 | 08-layout-table.md, 10-layout-multicolumn.md |
| A5 | 11-fragmentation-and-pagination.md, 12-paged-media.md |
| A6 | 13-generated-content-and-counters.md, 13b-footnotes.md |
| A7 | 14-text-shaping-and-line-breaking.md, 14b-fonts.md, 15-images-svg-and-media.md |
| A8 | 16-pdf-output.md, 16b-painting-and-display-list.md, 17-pdf-accessibility-and-archival.md |
| A9 | 18-cli.md, 18b-compat-shims.md, 22-templating-and-data-mode.md |
| A10 | 19-http-server-mode.md, 20-library-api.md, 21-bindings.md |
| A11 | 23-security-model.md, 23b-resource-loading.md, 24-resource-limits-and-sandboxing.md, 25-determinism-and-reproducibility.md |
| A12 | 26-performance-targets-and-benchmarks.md, 27-testing-strategy.md, 28-observability-and-diagnostics.md, 29-developer-experience.md, 30-deployment.md |
| A13 | 00-vision-and-positioning.md, 01-scope-v1-and-non-goals.md, 31-compatibility-matrix.md, 32-differentiators.md, 33-migration-guides.md, 36-glossary.md |
| Lead | 02 (done), 34 roadmap, 35 decisions log, README, MASTER-CHECKLIST |

Spec 10 must start with an explicit statement: multicol layout is scheduled for M6 (not deferred past 1.0); `column-span: all` and nested multicol are deferred past 1.0 (ADR-0017).

## Document structure template (each spec document)

```
# NN — Title
Status: draft for implementation. Owner prefix(es): XXX. Depends on documents: …
## 1. Purpose and scope (what is in / out; links to ADRs)
## 2. Background and references (spec sections, research refs)
## 3+. Design (data structures with Rust signatures, algorithms step by step, edge cases, error/warning codes, configuration)
## N. Test plan (fixtures, what each proves)
## N+1. Checklist (all items, in implementation order)
## Cross-doc requests (optional)
## ADR proposals (optional)
```

Quality bar:
- Algorithms written as numbered steps an implementer can code directly, including exact rounding and tie-break rules.
- Every CSS property in scope is listed with its value grammar, initial value, inherited flag, computed value, and support milestone.
- Every warning/error code introduced is listed in a table: code, condition, message template.
- Items: each ≤ ~1 day of work; acceptance criteria give concrete inputs and expected numeric or structural outputs; tests name real paths following CONVENTIONS §4.
- No vague items. No implementable content outside items.
- Split any document over ~800 lines into NNc etc. (keep the ID ranges disjoint and say which range each part uses).
- Run `python3 /home/user/Placeholder_name/docs/tools/checklist.py check` when done. Errors about unknown dependencies are expected only for anchors other agents have not written yet. Fix every other error (format, missing fields, milestone ordering within your doc, cycles, duplicate IDs).
