# 02 — Architecture overview

Status: normative. Decisions: `research/00-SYNTHESIS.md`, ADR-0002…ADR-0013 in `35-decisions-log.md`.

This document covers the pipeline, the workspace layout, the core shared types, data flow and lifetimes, threading, the error model and feature flags. Everything else in the spec set plugs into the contracts defined here. Types marked *normative* must keep their names and shapes, though fields may be added.

## 1. Pipeline

```
           ┌──────────── RenderOptions / Policy / Limits ────────────┐
Input ──▶ [1 Load] ──▶ [2 Template]? ──▶ [3 Decode+Parse HTML] ──▶ Dom
                                                    │
                     [4 Collect stylesheets] ◀──────┘   (UA sheet, compat layer, user CSS,
                              │                          <link>, <style>, @import, style="")
                              ▼
                     [5 Cascade + computed values] ──▶ StyledDom (ComputedStyle per element/pseudo)
                              │
                              ▼
                     [6 Box tree generation] ──▶ BoxTree (immutable)
                              │      ▲ image intrinsic sizes, fonts (lazy, via Fetcher)
                              ▼
         ┌─────────── [7 Page loop] ─────────────────────────────────────────┐
         │  for each page i: resolve page context (named page, side, blank,   │
         │  :nth) → page constraint space → layout(root, space, token_{i-1})  │
         │  → BodyFragment_i + token_i + PageState_i (counters, strings,      │
         │  running elements, anchors, bookmarks, footnotes)                   │
         │  → [8 Paint body] → DisplayList_i                                   │
         │  → if page finalizable now: [9 Margin boxes] → [10 PDF page emit]   │
         │    else: retain (DisplayList_i, PageState_i) for finalization       │
         └────────────────────────────────────────────────────────────────────┘
                              │ end of content
                              ▼
         [11 Finalize]: total page count known → resolve deferred margin boxes,
         forward target-counter relayout (≤ max_layout_passes) → emit remaining
         pages → outline, named destinations, tag tree, metadata, attachments
                              │
                              ▼
         [12 PDF serialize] (krilla) ──▶ OutputSink (Vec<u8> | io::Write)
```

Stage contracts (each stage lives in one crate; §2):

| # | Stage | Crate | Input → Output | Fallible with |
|---|---|---|---|---|
| 1 | Load | `recto-net` | `Input` → main document bytes + base URL | `E_FETCH_*`, `E_PATH_DENIED`, `E_LIMIT_INPUT_SIZE` |
| 2 | Template | `recto-template` | template bytes + JSON value → HTML bytes | `E_TEMPLATE_*`, `E_JSON_*` |
| 3 | Parse | `recto-dom` | bytes → `Dom` (arena) | `E_INPUT_ENCODING`, `E_LIMIT_DOM_*` |
| 4 | Stylesheets | `recto-css` | `Dom` + Fetcher → `Vec<Stylesheet>` ordered by cascade origin and position | `E_LIMIT_CSS` (parse errors are warnings) |
| 5 | Cascade | `recto-style` | `Dom` + sheets → `StyledDom` | `E_LIMIT_WORK` |
| 6 | Box tree | `recto-layout::boxtree` | `StyledDom` → `BoxTree` | `E_LIMIT_*` |
| 7 | Layout & pagination | `recto-layout` | `BoxTree` → stream of `PageFragment` + `PageState` | `E_LIMIT_PAGES`, `E_LIMIT_WORK` |
| 8–9 | Paint | `recto-paint` | `PageFragment` → `DisplayList` | — |
| 10–12 | PDF | `recto-pdf` | `DisplayList`s + document data → PDF bytes | `E_LIMIT_OUTPUT`, `E_PDF_PROFILE` |

The facade crate `recto` owns orchestration (`Engine::render`), budgets, the diagnostics sink and the page loop driver that connects stages 7–12.

## 2. Workspace layout

```
Cargo.toml                 # [workspace], [workspace.dependencies] exact pins, profile settings
rust-toolchain.toml        # channel = "1.92"
deny.toml                  # licenses, advisories, bans (dup skip-list per ADR-0011)
crates/
  recto-common/            # Au, geometry, ids, diagnostics, errors, limits, budget, deterministic collections
  recto-net/               # Policy, Fetcher, ResourceKind, URL resolution, file roots, data:, VFS, http (feature "net")
  recto-dom/               # encoding sniffing, html5ever/xml5ever TreeSink, arena DOM, DOM queries
  recto-css/               # tokenizer glue, stylesheet + at-rule parsing, property registry, value types, media queries
  recto-style/             # selector matching, cascade, var(), computed values, page-context cascade, UA sheets
  recto-fonts/             # font database, CSS Fonts 4 matching, @font-face loading, WOFF/2, bundled fonts
  recto-text/              # itemization, bidi, segmentation, hyphenation, shaping (harfrust), glyph runs
  recto-image/             # raster probing/decoding, JPEG passthrough, SVG sandbox (usvg), barcodes
  recto-layout/            # box tree, formatting contexts, fragmentation, pagination, paged media, generated content
  recto-paint/             # fragment tree → DisplayList (backgrounds, borders, text, images, effects, links, tags)
  recto-pdf/               # DisplayList → krilla; outlines, destinations, tagging, metadata, PDF/A, PDF/UA, Factur-X
  recto/                   # facade: Engine, RenderOptions, Input, render(), batch, reports
  recto-template/          # minijinja integration, data mode, JSONL batch, asset bundles
  recto-cli/               # binary `recto` (+ multicall `wkhtmltopdf`), subcommands, compat shims, watch/preview
  recto-server/            # binary `recto serve` impl: axum app, supervisor/worker pool, Gotenberg routes
  recto-capi/              # C ABI (cdylib + staticlib) + generated recto.h
  recto-test/              # test harness library: render+rasterize, pixel grids, WPT runner, pdf checks
bindings/
  node/                    # napi-rs package @recto/pdf
  python/                  # PyO3 + maturin package `recto`
  wasm/                    # wasm-bindgen package @recto/wasm
clients/
  go/ php/ ruby/ java/ dotnet/   # thin HTTP/subprocess clients (dotnet also P/Invoke over recto-capi)
fuzz/                      # cargo-fuzz targets
tests/                     # integration fixtures (layout/, render/, pdf/, wpt/, cli/, server/, compat/)
bench/                     # corpus + benchmark harness
xtask/                     # cargo xtask: fetch-corpora, wpt-sync, gen-bundled-fonts-index, release helpers
docs/                      # this spec set
```

Dependency direction (an arrow means "may depend on"; no cycles; enforced by `cargo xtask check-deps`):

```
recto-common ◀── recto-net ◀── recto-dom
recto-common ◀── recto-css ◀── recto-style ◀── (recto-dom)
recto-common ◀── recto-fonts ◀── recto-text
recto-common ◀── recto-image (◀── recto-net)
recto-layout ──▶ recto-style, recto-text, recto-fonts, recto-image, recto-dom
recto-paint  ──▶ recto-layout
recto-pdf    ──▶ recto-paint (display list types), recto-fonts, recto-image; krilla is private to recto-pdf
recto        ──▶ all of the above; re-exports the public API only
recto-template ──▶ recto-common (does not depend on recto)
recto-cli / recto-server / recto-capi / bindings ──▶ recto, recto-template
```

Rules:
- Only `recto` (and the binaries) are public API. Inner crates are published for build reasons with `0.0.x` versions and the doc banner "internal, no stability".
- krilla, taffy, harfrust, usvg and html5ever types never appear in a public signature of `recto`.
- Each crate has `#![forbid(unsafe_code)]` except `recto-capi`, the bindings, and the allocator shim in `recto-common::alloc` (each `unsafe` block carries a `// SAFETY:` comment, enforced by clippy `undocumented_unsafe_blocks`).

## 3. Core shared types (`recto-common`), normative

```rust
/// Layout unit: 1/64 CSS px. 1 px = 1/96 in. Saturating arithmetic.
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub struct Au(pub i32);
impl Au {
    pub const PER_PX: i32 = 64;
    pub const ZERO: Au = Au(0);
    pub const MAX: Au = Au(i32::MAX / 2);          // "infinite" available size sentinel
    pub fn from_px_f32(px: f32) -> Au;             // round half to even
    pub fn from_pt_f32(pt: f32) -> Au;             // pt * 4/3 px
    pub fn to_pt_f32(self) -> f32;                 // only used by recto-pdf
    pub fn scale_by(self, factor: f32) -> Au;      // round half to even
}
// Add/Sub/Neg/Mul<i32>/Div<i32> saturating; no Mul<Au>.

pub struct Point { pub x: Au, pub y: Au }
pub struct Size  { pub width: Au, pub height: Au }
pub struct Rect  { pub origin: Point, pub size: Size }
pub struct Sides<T> { pub top: T, pub right: T, pub bottom: T, pub left: T }
pub struct Transform2D { pub a: f32, pub b: f32, pub c: f32, pub d: f32, pub e: f32, pub f: f32 } // used only in paint

/// Stable identifiers: indices into arenas, assigned in document order.
pub struct NodeId(pub u32);   // DOM node
pub struct BoxId(pub u32);    // box tree node
pub struct FontId(pub u32);   // font database face (stable per ADR-0014 sort order)
pub struct ImageId(pub u32);  // decoded/probed resource
pub struct SourceId(pub u32); // input file / stylesheet / template for diagnostics

pub struct SourceLocation { pub source: SourceId, pub line: u32, pub column: Option<u32> }

pub enum Severity { Warning, Error }
pub struct Diagnostic {
    pub code: DiagCode,                 // e.g. W_CSS_UNSUPPORTED_PROPERTY
    pub severity: Severity,
    pub message: String,                // English, no absolute paths in server mode
    pub location: Option<SourceLocation>,
    pub order_key: (u32, u32),          // (source, byte offset or node index) → deterministic sort
}

pub struct RenderError {
    pub code: ErrorCode,
    pub message: String,
    pub location: Option<SourceLocation>,
}

/// Collects diagnostics; deduplicates (code, location); caps at Limits::max_diagnostics (default 10_000),
/// then emits one W_DIAGNOSTICS_TRUNCATED. Sorted by order_key at the end of the job.
pub struct DiagnosticSink { /* RefCell<Vec<Diagnostic>> + dedup set */ }

/// Deterministic work budget (fuel) + cooperative memory check. One per job.
pub struct Budget {
    // fuel: Cell<u64>, limits: Arc<Limits>, deadline: Option<Instant> (backstop only)
}
impl Budget {
    /// Charge `units` of work at a named checkpoint. Errors are deterministic for fuel and memory;
    /// the deadline check only runs every 4096 charges and yields E_TIMEOUT.
    pub fn charge(&self, units: u64, at: Checkpoint) -> Result<(), RenderError>;
}
pub enum Checkpoint { Parse, Cascade, BoxGen, Layout, Shape, Paint, Pdf, Fetch, Template }

/// All numeric limits (spec 24). Defaults differ for CLI vs server profiles.
pub struct Limits { /* see 24-resource-limits-and-sandboxing.md §2 */ }

/// Deterministic collections: re-exports.
pub type DetMap<K, V> = indexmap::IndexMap<K, V, rustc_hash::FxBuildHasher>;
pub type DetSet<K>    = indexmap::IndexSet<K, rustc_hash::FxBuildHasher>;
pub type FastMap<K,V> = rustc_hash::FxHashMap<K, V>; // lookups only; never iterate into output
```

## 4. Key cross-crate contracts (normative signatures)

```rust
// recto-net
pub enum ResourceKind { Document, Stylesheet, Import, Image, Font, SvgImage, SvgSubresource,
                        Attachment, Background, XmpMetadata, TemplateAsset }
pub struct Policy { /* spec 23 */ }
pub struct Fetcher { /* constructed only via Fetcher::new(policy, limits, vfs) — no Default */ }
impl Fetcher {
    pub fn resolve(&self, base: &Url, reference: &str) -> Result<Url, RenderError>;
    pub fn fetch(&self, url: &Url, kind: ResourceKind, budget: &Budget) -> Result<Resource, FetchFailure>;
}
pub struct Resource { pub url: Url, pub bytes: Arc<[u8]>, pub mime: Option<String>, pub content_hash: [u8; 32] }

// recto-dom
pub struct Dom { /* arena: Vec<Node>; node 0 = Document */ }
pub fn parse_html(bytes: &[u8], opts: &ParseOptions, diags: &DiagnosticSink, budget: &Budget) -> Result<Dom, RenderError>;

// recto-style
pub struct StyledDom<'d> { pub dom: &'d Dom, /* styles: Vec<Option<Arc<ComputedStyle>>>, pseudo styles */ }
pub fn cascade<'d>(dom: &'d Dom, sheets: &[Stylesheet], media: &MediaContext, ...) -> Result<StyledDom<'d>, RenderError>;
pub fn page_style(sheets: &PageRules, page: &PageSelectorContext, root: &ComputedStyle) -> PageStyle; // spec 12

// recto-layout
pub struct BoxTree { /* arena Vec<LayoutBox>; BoxId indices */ }
pub fn build_box_tree(styled: &StyledDom, cx: &mut BoxGenContext) -> Result<BoxTree, RenderError>;
pub trait PageConsumer { fn page(&mut self, page: PageFragment, state: PageState) -> Result<(), RenderError>; }
pub fn paginate(tree: &BoxTree, cx: &mut LayoutContext, out: &mut dyn PageConsumer) -> Result<PaginationSummary, RenderError>;

// Layout core (spec 06, 11) — every formatting context implements:
pub fn layout(cx: &mut LayoutContext, node: BoxId, space: &ConstraintSpace, token: Option<&BreakToken>)
    -> Result<LayoutResult, RenderError>;

// recto-paint
pub struct DisplayList { pub page_size: Size, pub items: Vec<DisplayItem> }  // spec 16b
pub fn paint_page(page: &PageFragment, margin: &[MarginBoxFragment], cx: &PaintContext) -> DisplayList;

// recto-pdf
pub struct PdfWriter { /* wraps krilla::Document */ }
impl PdfWriter {
    pub fn new(cfg: &PdfConfig) -> Result<Self, RenderError>;
    pub fn add_page(&mut self, list: &DisplayList, page_meta: &PageMeta) -> Result<(), RenderError>;
    pub fn finish(self, doc: &DocumentMeta, sink: &mut dyn std::io::Write) -> Result<u64, RenderError>;
}
```

## 5. Data flow, lifetimes and memory

| Data | Lifetime | Approx size | Notes |
|---|---|---|---|
| Input bytes, `Dom`, `StyledDom`, `BoxTree` | whole job | O(document) | Immutable after construction. `BoxTree` holds `Arc<ComputedStyle>` (shared styles deduplicated by hash) |
| Shaped paragraphs / intrinsic sizes | whole job (cache) | O(text) | Keyed by `(BoxId, width-independent)` |
| `PageFragment` | until painted | O(page) | Dropped immediately after paint |
| `PageState` | whole job | O(1) per page | Counters, strings, running element refs, anchors |
| `DisplayList` | until emitted (or until finalization if deferred) | ≈ 1–20 KiB per typical page | Deferred only if the document needs page totals or forward refs (ADR-0012) |
| krilla document | until finish | ≈ compressed output (+1.1× during finish) | Byte streaming after the krilla patch (PDF items, M6) |
| Font/image caches | `Engine` lifetime (shared across jobs) | bounded LRU by bytes | Content-addressed (BLAKE3). Safe across jobs because they are immutable |

## 6. Threading model

- One render job = one thread running stages 1–12 sequentially. That guarantees deterministic ordering and simple borrow lifetimes. The job thread is spawned with a fixed stack (`Limits::job_stack_bytes`, default 64 MiB) and wrapped in `catch_unwind` → `E_INTERNAL_PANIC`.
- Parallelism happens **across jobs** (batch mode, server, bindings): `Engine` is `Send + Sync` and holds shared immutable caches behind `Arc` + `Mutex`/`RwLock`. A job reads the cache. Insertions are idempotent and content-addressed, so results never depend on interleaving.
- Inside a job, the only parallelism is krilla's `rayon` compression (deterministic output order). It is off on wasm.
- The server runs jobs in worker **processes** (spec 19, 24). The library and CLI run them on threads.

## 7. Error model

1. Fatal errors are `RenderError` with a stable `ErrorCode` (string id `E_*`). The full registry is in `recto-common::codes` and must match the tables in specs 23 and 24.
2. Non-fatal problems are `Diagnostic`s with codes `W_*`. Rendering continues, and every warning is returned in `RenderReport::warnings` (CLI: stderr; server: JSON `warnings[]`).
3. Exit codes (CLI): 0 success (possibly with warnings), 1 generic failure (wkhtmltopdf-compatible), 2 usage, 3 input invalid, 4 policy violation (strict), 5 resource limit, 6 timeout, 7 fetch failure (strict), 70 internal. In wkhtmltopdf shim mode the exit codes follow R02 (0/1/2/3).
4. Panics are bugs: caught at the job boundary, reported as `E_INTERNAL_PANIC` with the panic message (server: message withheld, request id logged).
5. Every error and warning code is documented in `docs/user/errors.md` (DOC items) with cause and fix.

Initial code registry (each owning spec extends it; codes are never renamed):

| Code | Class | Owner |
|---|---|---|
| `E_USAGE` | 2 | CLI |
| `E_INPUT_ENCODING`, `E_JSON_SYNTAX`, `E_TEMPLATE_SYNTAX`, `E_TEMPLATE_RUNTIME`, `E_BUNDLE_PATH` | 3 | DOM / TPL |
| `E_SCHEME_DENIED`, `E_HOST_DENIED`, `E_IP_DENIED`, `E_PATH_DENIED`, `E_NETWORK_DISABLED`, `E_ATTACHMENT_DENIED` | 4 | SEC / NET |
| `E_LIMIT_*` (see spec 24), `E_SVG_DTD`, `E_TEMPLATE_DEPTH`, `E_BUNDLE_LIMIT` | 5 | LIM |
| `E_TIMEOUT`, `E_FETCH_TIMEOUT` | 6 | LIM / NET |
| `E_FETCH_FAILED`, `E_FETCH_STATUS`, `E_FETCH_REDIRECT_LIMIT` | 7 | NET |
| `E_PDF_PROFILE` (profile violation, e.g. PDF/A with transparency where not allowed) | 3 | ACC |
| `E_INTERNAL_PANIC`, `E_WORKER_CRASHED`, `E_SANDBOX_VIOLATION` | 70 | ARC / SRV |

## 8. Cargo features (crate `recto`, propagated)

| Feature | Default | Effect |
|---|---|---|
| `net` | off in library, **on in release binaries** | HTTP(S) fetching (still runtime-off by policy) |
| `bundled-fonts` | on | Liberation Sans/Serif/Mono + symbol fallback compiled in (FNT) |
| `fonts-cjk` | off | Noto Sans CJK subset bundle |
| `system-fonts` | on (native), off (wasm) | Directory scanning of system font dirs |
| `complex-scripts` | on | icu_segmenter LSTM model (Thai/Lao/Khmer/Myanmar) |
| `hyphenation` | on | hypher with the language list in spec 14 |
| `svg` | on | usvg + krilla-svg |
| `rayon` | on (native), off (wasm) | krilla parallel compression |
| `pdf-import` | off | krilla `pdf` feature: background/letterhead PDF pages |
| `barcodes` | on | `recto-barcode:` scheme |
| `server` | binary only | axum server |
| `sandbox` | on (linux) | landlock + seccomp in CLI/server workers |

## 9. Configuration precedence

Effective options = defaults (profile: `cli` | `server` | `library` | compat entry point) < config file (`recto.toml`, CLI only, explicitly named via `--config`) < environment variables (`RECTO_*`, documented per option) < CLI flags / request JSON. Document CSS interacts through cascade layers: UA sheet < compat layer (e.g. wkhtmltopdf CLI geometry when overriding) < author < user `--css` (user origin, below author normal but `!important` beats author) < `--page-css-override` (a dedicated override layer above author, used by `--page-size`/`--margin` when `--override-page-css` is given). See spec 04b §4 and spec 12 §3.

## 10. Checklist

- [ ] **ARC-001** Create the Cargo workspace skeleton with all crates from §2 as empty libraries/binaries.
      Acceptance: `cargo build --workspace` and `cargo test --workspace` succeed on stable 1.92; `rust-toolchain.toml` pins 1.92; edition 2024 everywhere; every crate except `recto-capi`/bindings has `#![forbid(unsafe_code)]`.
      Tests: CI job `workspace-build` (cargo build + test, linux x86_64)
      Depends on: none
      Milestone: M0
      Spec ref: §2

- [ ] **ARC-002** Add `[workspace.dependencies]` with exact pins for every third-party crate named in research/00-SYNTHESIS §3 and R13, plus `deny.toml`.
      Acceptance: all versions pinned with `=`; `cargo deny check licenses bans advisories` passes; the license allowlist is exactly MIT, Apache-2.0, BSD-2/3-Clause, ISC, Zlib, Unicode-3.0, MPL-2.0, OFL-1.1 (fonts), CC0-1.0, BSL-1.0; the duplicate skip-list contains only the entries justified in ADR-0011 with comments.
      Tests: CI job `cargo-deny`
      Depends on: ARC-001
      Milestone: M0
      Spec ref: research/00-SYNTHESIS §3, ADR-0011

- [ ] **ARC-003** Verify the dependency set builds statically for x86_64 and aarch64 musl and record the duplicate-crate and binary-size baseline.
      Acceptance: `cargo build --release --target {x86_64,aarch64}-unknown-linux-musl -p recto-cli` succeeds with all default features; `cargo tree -d` output is committed to `docs/build/dup-baseline.txt` and contains only ADR-0011 duplicates; `cargo bloat --crates` top-30 is committed to `docs/build/size-baseline.txt`; the release binary is ≤ 25 MiB stripped (else open an ADR before proceeding).
      Tests: CI job `musl-static` (also runs `ldd` → "not a dynamic executable")
      Depends on: ARC-002
      Milestone: M0
      Spec ref: research/00-SYNTHESIS §10

- [ ] **ARC-004** Implement `Au` with saturating arithmetic, conversions and rounding rules from §3.
      Acceptance: `Au::from_px_f32(0.5/64.0)` = `Au(0)` and `Au::from_px_f32(1.5/64.0)` = `Au(2)` (half-even); `Au::MAX + Au(1)` saturates; `Au(96*64).to_pt_f32()` = 72.0 exactly; property test: `from_px_f32(x.to_px())` round-trips for all i32 within ±2^24.
      Tests: recto_common::au::tests::{rounding_half_even, saturation, pt_conversion}, proptest `au_roundtrip`
      Depends on: ARC-001
      Milestone: M0
      Spec ref: §3, ADR-0004

- [ ] **ARC-005** Implement geometry types `Point`, `Size`, `Rect`, `Sides<T>`, `Transform2D` with the operations layout and paint need.
      Acceptance: `Rect::union`, `intersect`, `inflate(Sides)`, `deflate(Sides)`, `contains`; `Transform2D::{identity, translate, scale, rotate, then, inverse, apply}` with the inverse of a singular matrix returning `None`; all ops are `const fn` where possible.
      Tests: recto_common::geom::tests::*
      Depends on: ARC-004
      Milestone: M0
      Spec ref: §3

- [ ] **ARC-006** Implement `Diagnostic`, `DiagnosticSink`, `RenderError`, `ErrorCode`/`DiagCode` registries and exit-code classes.
      Acceptance: every code in §7 exists with a string id, an exit class and a one-line description; `DiagnosticSink` deduplicates identical (code, location), caps at `max_diagnostics` with a single `W_DIAGNOSTICS_TRUNCATED`, and `into_sorted()` orders by `order_key`; a unit test asserts the registry has no duplicate string ids.
      Tests: recto_common::diag::tests::{dedup, cap, sort_order, registry_unique}
      Depends on: ARC-001
      Milestone: M0
      Spec ref: §7

- [ ] **ARC-007** Implement `Budget` (fuel + deadline backstop) and the `Checkpoint` enum.
      Acceptance: with fuel = 1000, charging 600 then 500 fails with `E_LIMIT_WORK` on the second call regardless of timing; the deadline is consulted only every 4096 charges; a zero fuel limit means unlimited; `Budget` is `!Sync` (per job).
      Tests: recto_common::budget::tests::{fuel_exhaustion_deterministic, deadline_sampling, unlimited}
      Depends on: ARC-006
      Milestone: M0
      Spec ref: §3, spec 24

- [ ] **ARC-008** Provide deterministic collection aliases and a clippy/lint configuration that forbids `std::collections::HashMap`/`HashSet` in non-test code of output-affecting crates.
      Acceptance: `clippy.toml` `disallowed-types` lists `std::collections::HashMap`, `std::collections::HashSet`, `std::time::SystemTime::now`, `std::time::Instant::now` (the latter two allowed only in `recto-common::budget` and `recto-server`); `cargo clippy --workspace -- -D warnings` passes.
      Tests: CI job `clippy`
      Depends on: ARC-001
      Milestone: M0
      Spec ref: §3, spec 25

- [ ] **ARC-009** Add the dependency-direction checker `cargo xtask check-deps`.
      Acceptance: the command parses `cargo metadata` and fails if any edge outside §2's allowed graph exists, or if any `recto` public signature mentions a type from krilla, taffy, harfrust, usvg or html5ever (checked via `cargo public-api` diff on `recto`).
      Tests: CI job `check-deps`; xtask unit test with a fabricated metadata JSON containing a forbidden edge
      Depends on: ARC-001
      Milestone: M0
      Spec ref: §2

- [ ] **ARC-010** Implement the `Engine`/job skeleton in `recto`: job thread with fixed stack, `catch_unwind`, `Budget`, `DiagnosticSink`, and stage sequencing with stub stages.
      Acceptance: `Engine::render` on any input runs stages in order (verified by a trace of stage names) and returns `RenderReport`; a stage that panics yields `E_INTERNAL_PANIC` and the engine remains usable for the next job; the job stack size equals `Limits::job_stack_bytes`.
      Tests: recto::engine::tests::{stage_order, panic_isolation, engine_reusable}
      Depends on: ARC-006, ARC-007
      Milestone: M0
      Spec ref: §1, §6

- [ ] **ARC-011** Wire the M0 "hello PDF" vertical slice end to end through the real stages.
      Acceptance: `Engine::render` on `<p>Hello, world</p>` produces a 1-page A4 PDF whose extracted text (lopdf) is `Hello, world`, using a bundled font; the same input rendered twice yields byte-identical output.
      Tests: tests/render/m0/hello.html (golden raster), tests/pdf/m0/hello.pdfcheck.toml
      Depends on: ARC-010, DOM-010, CSS-010, CSS-210, BOX-010, LAY-010, LAY-210, TXT-010, FNT-010, PNT-010, PDF-010, TST-010
      Milestone: M0
      Spec ref: §1

- [ ] **ARC-012** Implement the page-loop driver connecting `paginate`, paint, margin-box finalization and the PDF writer, with immediate vs deferred emission decided by static analysis.
      Acceptance: for a document without `counter(pages)`/forward references, each page is passed to `PdfWriter::add_page` before the next page's layout starts (asserted by an event trace); for a document using `counter(pages)` in `@bottom-center`, body display lists are retained and margin boxes are rendered after the last page with the correct total; the peak count of retained `PageFragment`s is 1 in both cases.
      Tests: recto::driver::tests::{immediate_emission_trace, deferred_pages_total, single_fragment_resident}; tests/render/pagination/page-x-of-y.html
      Depends on: ARC-011, PAG-020, PGM-030, GEN-040, PDF-020
      Milestone: M2
      Spec ref: §1, ADR-0012

- [ ] **ARC-013** Implement forward-reference relayout in the driver: dependency analysis, dirty-page detection, bounded passes and width reservation.
      Acceptance: a TOC using `target-counter(attr(href url), page)` before 30 chapters converges in ≤ 2 passes with correct numbers; an adversarial fixture whose page numbers oscillate stops after `max_layout_passes` with `W_LAYOUT_NOT_CONVERGED` and identical output on repeated runs; relayout restarts at the first page whose resolved values changed (asserted via trace).
      Tests: tests/render/gencontent/toc-forward-refs.html; tests/layout/gencontent/oscillation.html; recto::driver::tests::relayout_starts_at_first_dirty_page
      Depends on: ARC-012, GEN-110
      Milestone: M3
      Spec ref: ADR-0013, spec 13

- [ ] **ARC-014** Implement multi-document jobs (several inputs concatenated into one PDF) with continuous page numbering and per-document outlines.
      Acceptance: `Input::Documents([a, b])` yields pages of `a` then `b`; `counter(page)` continues across documents unless the second document's root has `counter-reset: page`; the outline has one top-level entry per document titled from `<title>`; stylesheets do not leak between documents.
      Tests: tests/render/multidoc/two-docs.html (+ second fixture), tests/pdf/multidoc/outline.pdfcheck.toml
      Depends on: ARC-012, PDF-110
      Milestone: M3
      Spec ref: R02 (cover/toc/page objects)

- [ ] **ARC-015** Document the architecture for contributors in `docs/dev/architecture.md`, generated from this spec's §1–§7 with code links.
      Acceptance: every crate in §2 has a section linking to its `lib.rs`; the pipeline diagram matches §1; CI fails if a crate exists in the workspace without a section (`cargo xtask check-docs`).
      Tests: CI job `check-docs`
      Depends on: ARC-009
      Milestone: M1
      Spec ref: §1–§7
