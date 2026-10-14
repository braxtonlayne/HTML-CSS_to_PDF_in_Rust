# 00 — Research synthesis and chosen foundations

Date: 2026-10-14. Inputs: research docs R01–R13 in this directory. Short names:

| Ref | File |
|---|---|
| R01 | `01-weasyprint-architecture.md` (WeasyPrint v70.0) |
| R02 | `02-wkhtmltopdf-feature-surface.md` (wkhtmltopdf 0.12.6) |
| R03 | `03-chrome-puppeteer-pdf-options.md` (CDP, Puppeteer 25.13, Playwright 1.64, Gotenberg 8.37) |
| R04 | `04-prince-and-pagedjs.md` (Prince docs, Paged.js 0.5.0-beta.2, Vivliostyle 2.45.2) |
| R05a | `05a-css-specs-paged-fragmentation.md` (csswg-drafts @ 1c249b3) |
| R05b | `05b-css-specs-text-fonts-tables-multicol.md` |
| R06 | `06-rust-layout-crates.md` (taffy 0.15.0, Servo, Blitz, Typst, Azul, fulgur) |
| R07 | `07-rust-text-stack.md` (harfrust, parley, cosmic-text, icu_segmenter, hypher, subsetter) |
| R08 | `08-rust-pdf-writers.md` (krilla 0.8.2, pdf-writer 0.15, printpdf 0.12.8) |
| R09 | `09-deployment-and-bindings.md` (47 wrapper/toolchain repos) |
| R10 | `10-security.md` (≈130 advisories, attack catalog, default policy) |
| R11 | `11-test-corpora.md` (WPT, WeasyPrint tests, templates, hayro) |
| R12 | `12-rust-html-css-image-svg-crates.md` (html5ever, cssparser, selectors, image, usvg, minijinja) |
| R13 | `13-server-cli-and-tooling-crates.md` (axum, ureq, clap, notify, barcodes, test tooling) |

This document is normative for the spec set. The spec documents implement the decisions below, and `docs/spec/35-decisions-log.md` records each one as an ADR with the alternatives that were rejected.

Research constraint, stated once: crate tarballs, docs.rs and w3.org were unreachable from the research sandbox. Every crate claim was verified against the upstream git repository at the tag matching the version on the crates.io sparse index. Items marked **UNVERIFIED** in the R-docs become explicit verification items (`*-0xx Spike/Verify …`) in the checklists. None are assumed.

---

## 1. Executive summary

recto is a **purpose-built paged layout engine**. The pipeline is HTML → arena DOM → our own cascade → box tree → **fragmenting layout driven by a streaming page loop** → display list → PDF via krilla. Mature crates cover parsing, shaping and PDF serialization. We own everything that has to know about pages: block, inline, table, float, positioning, multicol, margin boxes and generated content. Taffy is used only to place flex and grid items inside one fragment.

The core bet: no existing Rust layout crate understands fragmentation (R06 §2), and every engine that bolted pagination on afterwards paid for it (fulgur: 10.5k lines of slicing code, a DoS, missing table fragmentation; WeasyPrint: manual rollback bugs, all pages in memory, R01 §10). A layout contract built around break tokens from day one is cheaper overall and is the only route to streaming, bounded memory and determinism.

## 2. Contradictions between research docs and their resolution

| # | Contradiction | Resolution |
|---|---|---|
| C1 | R07 wants a single fontations version (skrifa 0.48 / read-fonts 0.45). krilla 0.8.2 depends on skrifa 0.42 and subsetter 0.2.6 with `variable-fonts` (older fontations), and krilla-svg depends on usvg 0.47 / fontdb 0.23 (krilla `Cargo.toml` L22–58). | Accept **two fontations lines**: ours (shaping, metrics, matching) and krilla's (embedding, subsetting). The duplication is confined behind `recto-pdf`. `cargo deny` gets an explicit, commented skip-list for `skrifa`, `read-fonts`, `font-types` and `fontdb` only. A DET item adds a CI check that both lines agree on glyph IDs and advances for every bundled font. Revisit when krilla bumps (tracked in ADR-0011). |
| C2 | R12 recommends usvg 0.48.1. krilla-svg pins usvg 0.47. | The workspace uses the **usvg version krilla-svg uses** (0.47.x), since one usvg line must cover both our sandbox wrapper and krilla-svg's `Tree` type. |
| C3 | System fonts: R10 says on in the CLI and off in the server; R07 says off unless `--system-fonts`. | CLI: **on** by default ("fonts just work"), bundled fonts first for generic families. `--reproducible`: off (only document + bundled + `--font-dir`), so output does not depend on the machine. Server and library: **off** by default. ADR-0014. |
| C4 | `thead`/`tfoot` repetition: css-tables-3 requires ≤ ¼ page each and `break-inside: avoid`. R01/R05a say users expect Chrome/WeasyPrint behavior. | Repeat `table-header-group`/`table-footer-group` on every fragment **when header+footer together take ≤ 50% of the fragmentainer block size**. Otherwise drop the footer first, then the header (WeasyPrint fallback, R01 §6), with warning `W_TABLE_HEADER_NOT_REPEATED`. ADR-0021. |
| C5 | Margin-box `content: normal`: css-page-3 says `none`, css-content-3 says `contents`. | css-page-3: **no box generated** (R05a open question 3). |
| C6 | `string-set` grammar differs between GCPM and css-content-3. | Accept the GCPM `<content-list>` syntax. Computed value = resolved string. |
| C7 | Letter-spacing: the Aug-2026 spec model (half on each side, none at line edges) vs current browsers (trailing). | Default = **browser model** (spacing after each typographic character unit, trimmed at the line end, matching Chrome output that users diff against). `recto-letter-spacing-model: spec` opt-in. ADR-0027. |
| C8 | `margin-break` L4 `auto` vs L3 truncation. | Implement L3 behavior (truncate to zero at unforced breaks, keep after forced breaks). `margin-break` is parsed; only `discard` is honored. |
| C9 | Margin defaults: Chrome CLI 1 cm, Puppeteer 0, Gotenberg 0.39 in, wkhtmltopdf 10 mm, CSS UA default for `@page` margins (none in spec; Prince/WeasyPrint use 75 px/0.75 in). | recto native default: `@page { size: A4; margin: 2cm }`, overridable by `--page-size`/`--margin` and author CSS. Each compat entry point (wkhtmltopdf, Puppeteer, Playwright, Gotenberg, Chrome CLI) has its own defaults table (R02, R03). ADR-0024. Default paper is A4 because the locale is unknown. `--page-size letter` is one flag. |
| C10 | Lenient vs strict on blocked or missing resources. | CLI and library: **lenient** (warning, rendering continues). Server: **strict**. Both configurable (R10 §7.1). |
| C11 | Units: R06 suggests `i32` 1/64 px or Au 1/60 px. R07 suggests 1/64 pt. | **`Au(i32)` = 1/64 CSS px.** Range ±33.5M px (≈ 8.9 km), exact for 1/2^n subdivisions, and shaping results (font units × size) are converted with round-half-even. ADR-0004. |
| C12 | R11 shows 94% of css-break reftests use multicol as the fragmentainer. Multicol was a "maybe" in the brief. | The fragmentation engine treats **pages and columns as fragmentainers from day one** (the `Fragmentation::Column` variant exists in M1 types). The multicol *layout* (balancing, rules) is scheduled later (M6), but the break machinery is tested against single-column test pages early. |
| C13 | Grid: a stretch goal in the brief. R11 shows Invoice Ninja uses `display:grid` in 18/20 designs. | Grid is in v1: **monolithic grid via taffy in M3**, row-boundary fragmentation in M6. ADR-0016. |
| C14 | R08: krilla cannot stream. The brief requires streaming emission and memory linear in page count. | Layout streams: each page's fragment tree is built, painted into a compact display list, handed to krilla, and freed. krilla keeps only compressed content streams (≈ output size). That meets "memory linear in page count" with a small constant. True byte streaming to the output sink comes from a krilla patch (`finish_to(W)`, R08 §3.3) in M6, proposed upstream first. Output size is capped by `max_output_bytes`. ADR-0012. |
| C15 | R10: ttf-parser/rustybuzz are unmaintained. krilla has an optional rustybuzz (`simple-text`), and usvg's `text` feature may pull ttf-parser via fontdb. | krilla `default-features = false` (no `simple-text`). SVG `<text>`: usvg `text` feature **on** in v1 (it needs fontdb → ttf-parser; accepted and tracked, since documents use SVG text in logos and charts). Post-1.0, replace it with our own text-to-path via `recto-text`. ADR-0018. |

## 3. Chosen foundations

| Concern | Choice (version) | Evidence | Build ourselves |
|---|---|---|---|
| HTML parse | html5ever 0.40.1 + markup5ever 0.40.0; xml5ever 0.40.0 for XHTML | R12 §1.1 | Arena DOM `TreeSink` (`&self`, `RefCell<Arena>`, `Handle = NodeId`), encoding sniffing (BOM → transport override → 1024-byte prescan → UTF-8), depth/node caps, `scripting_enabled: false` |
| CSS parse | cssparser 0.38.0 | R12 §2.1 | Stylesheet/at-rule parsers incl. `@page` + 16 margin rules, `@font-face`, `@media`, `@supports`, `@import`, `@layer`, `@counter-style` (subset); property value parsers |
| Selectors | selectors 0.41.0 (`:is/:where`, `:has`, `:nth-child(of)` opted in) | R12 §2.2 | `Element` impl, rule index, bloom filter, page selectors |
| Cascade / computed values | own | R12 §2.4 (stylo infeasible), §2.3 (lightningcss unsuitable) | Full cascade (origins, layers, importance, specificity, order), inheritance, `var()`, computed values, UA print stylesheet |
| Layout | own fragmenting engine. taffy 0.15.x (exact pin) for flex/grid item placement only | R06 §5 | Block, inline, table, floats, abspos/fixed, multicol, page/margin boxes, break tokens, best-break rewind |
| Shaping | harfrust 0.14.0 | R07 F1 | Fallback nominal-glyph shaping path for malformed fonts |
| Font parsing/metrics | skrifa 0.48 / read-fonts 0.45 | R07 F2 | Font database, CSS Fonts 4 §5 matching, `@font-face` loading, synthesis decisions |
| WOFF/WOFF2 | wuff 0.2.9 | R12 §5.4 | — |
| Segmentation | icu_segmenter 2.3 + icu_properties 2.3 (compiled data; LSTM behind `complex-scripts`) | R07 F6 | Break-override hook (Chromium parity) |
| Bidi | unicode-bidi 0.3.18 | R07 F8 | — |
| Hyphenation | hypher 0.1.8, `default-features=false`, explicit languages, **never Slovak/`full`** (GPL pattern) | R07 F9 | `lang` → language mapping, hyphenate limits |
| Line breaking | own greedy, resumable breaker (parley `BreakerState` design), optional Knuth–Plass for `text-wrap: pretty` | R07 §Rec | All of the inline formatting context |
| Images | image 0.25.10 (`png,jpeg,gif,webp,bmp`, no default features), zune-jpeg 0.5 header parsing, imagesize | R12 §3 | Limits wrappers, JPEG passthrough policy, EXIF → matrix, ICC extraction |
| SVG | usvg 0.47.x (krilla-svg line) sandboxed: roxmltree pre-parse (`allow_dtd: false`, node cap), own href resolvers, own svgz decompression | R10 F5, R12 §4 | Sandbox wrapper |
| PDF | krilla 0.8.2 + krilla-svg 0.8.1, `default-features=false`, features `raster-images` (+ `rayon` native, + `pdf` opt-in for letterhead PDFs) | R08 §Rec | Display-list adapter, tag-tree builder, outline builder, Factur-X XMP (krilla patch), streaming sink (krilla patch, M6) |
| Compression | flate2 1.1.10 + miniz_oxide (exact pin) | R12 §5.3 | — |
| Templating | minijinja 3.0.0 (fuel, recursion limit, forced HTML escaping, no loader) | R12 §5.7 | Data-mode driver, JSONL batch, asset bundle VFS |
| JSON | serde_json (preserve_order) | R12 §5.6 | Options schema (one struct, serde + JSON Schema) |
| HTTP server | axum + tokio + tower-http (versions per R13) | R13 §1 | Supervisor/worker pool, Gotenberg-compatible routes |
| HTTP client (`net` feature) | per R13 §2 recommendation (custom resolver for IP pinning, manual redirects) | R13 §2, R10 F3 | Fetch broker, IP denylist |
| CLI | clap 4 (derive). Hand-written argv parser for the wkhtmltopdf shim (its grammar of page objects and `cover`/`toc` positionals does not fit clap) | R13 §3, R02 | Shim parser |
| Watch / preview | notify + debouncer; preview served by the same axum stack with SSE reload | R13 §4 | PDF.js-free preview: page PNGs rasterized with hayro, plus a PDF download link |
| Barcodes | per R13 §5 (QR + 1D + DataMatrix/PDF417 set) | R13 §5 | `recto-barcode:` URL scheme → SVG |
| Test rasterizer | hayro 0.8 (pure Rust) at 96 dpi, `simd` off | R11 §6 | Harness (`libtest-mimic`), WPT print-reftest runner, pixel-grid tests ported from WeasyPrint |
| Sandboxing | landlock 0.4.7, seccompiler 0.5.0 (Linux, CLI + server workers) | R10 §4.6 | Policy builder |
| Bindings | napi-rs 3 (Node), PyO3 0.29+ / maturin 1.15 (Python, abi3-py310), wasm-bindgen (WASM), cbindgen 0.29 (C ABI → .NET P/Invoke) | R09 §9 | Thin HTTP/subprocess clients for Go, PHP, Ruby, Java |
| Distribution | cargo-dist (archives, installers, Homebrew, attestations, SBOM), napi-rs platform packages, maturin `bin` wheels, `FROM scratch` image, mimalloc on musl | R09 §10 | Release workflow |

MSRV: **1.92** (krilla 0.8.2). Edition 2024.

Licenses: all permissive, plus MPL-2.0 (cssparser, selectors, cbindgen at build time only), which is file-level copyleft and fine for static linking with a NOTICE entry. GPL/AGPL code is banned in the binary and in tests: no Slovak hyphenation patterns, no Ghostscript/MuPDF in the harness, no committed Vivliostyle (AGPL) or openhtmltopdf (LGPL) test files (fetched at CI time only). `cargo deny` enforces the license allowlist.

## 4. Architecture decisions (summary; full ADRs in spec/35)

1. **Pipeline and crates** (spec/02): `recto-common`, `recto-net`, `recto-dom`, `recto-css`, `recto-style`, `recto-fonts`, `recto-text`, `recto-image`, `recto-layout`, `recto-paint`, `recto-pdf`, `recto` (facade), `recto-template`, `recto-cli`, `recto-server`, `recto-capi`, `bindings/{node,python,wasm}`, `clients/{go,php,ruby,java,dotnet}`, `recto-test`, `xtask`, `fuzz`.
2. **Layout contract** (R06 §5.2): `layout(node, &ConstraintSpace, Option<&BreakToken>) -> LayoutResult`. Break tokens are immutable values. Every formatting context implements it. Unfragmented layout is the same call with `Fragmentation::None`.
3. **Page loop**: resolve the page context (named page, side, blank) → lay out the root with the page's constraint space → progress assertion → produce `PageFragment` → paint body → store a per-page `PageState` snapshot (counters, strings, running elements, bookmarks, anchors) → emit or defer.
4. **Two-phase finalization**: margin boxes are laid out after body pagination of that page, from the snapshot. If the document uses `counter(pages)` or forward `target-counter`/`target-text` (static dependency analysis over computed `content`), then margin boxes (resp. affected pages) are finalized after the last page. The body display lists are kept until then (memory linear in pages, compact). Forward references inside the body trigger targeted relayout from the first affected page, at most `max_layout_passes` (default 4) passes, with stable width reservation (widest digit × digit count of the page count estimate) to make convergence likely; non-convergence → `W_LAYOUT_NOT_CONVERGED` and the last pass is used. Deterministic.
5. **Breaking policy** (css-break-3 §4.4 + R06): containers report `best_break` with appeal classes `Perfect > ViolatingOrphansWidows > ViolatingBreakAvoid > LastResort`; a parent re-lays out with `EarlyBreak` to stop at a better earlier break. At most one rewind per container per fragmentainer. Every fragmentainer must consume content (monolith overflow allowed only at fragmentainer start).
6. **Side effects are values**: layout returns out-of-flow candidates, footnote calls, running-element/string assignments, anchors and bookmarks in the `LayoutResult`. The page loop commits them only when the page is accepted, so a rewind just drops values (no WeasyPrint-style `remove_placeholders`).
7. **Display list** (`recto-paint`): writer-agnostic, per page: clip, transform, opacity group, fill rect/path, stroke, glyph run (font id, size, glyph ids + positions + cluster→text ranges), image, SVG tree reference, link rect, named destination, tag begin/end (MCID binding), artifact begin/end. `recto-pdf` translates it to krilla.
8. **Determinism**: no wall-clock reads (dates from `SOURCE_DATE_EPOCH` or `--date`, otherwise omitted in `--reproducible`); no randomized hashing in anything that affects output order (`IndexMap`/`BTreeMap`/sorted vectors; `FxHashMap` only for lookups); fixed-point layout; sorted font scans; content-hash IDs; pinned compression; a single-threaded job pipeline (parallelism only across jobs, plus krilla's deterministic parallel compression). `--reproducible` = no system fonts + fixed epoch + document ID from the content hash.
9. **Security**: one non-`Default`-constructible `Fetcher` with a required `Policy`. An enumerated `ResourceKind` is checked for every fetch (table-driven test). Network code is compiled only with the `net` feature (the default static binary has no HTTP client unless built with `net`; the release binary includes it, off at runtime). R10 §7 defaults verbatim.
10. **Limits**: depth/node caps at parse time; a work-fuel counter checked at deterministic checkpoints (layout per box, shaping per run, cascade per element); a counting allocator with cooperative checks; worker subprocesses with `RLIMIT_AS` in server mode; job threads with a fixed 64 MiB stack and `catch_unwind`.
11. **Error model**: `RenderError { code: ErrorCode, message, location: Option<SourceLocation> }` + `Vec<Diagnostic>` (sorted by document position). Codes and exit classes per R10 §7.5, extended in spec/02.
12. **Options**: a single `RenderOptions` struct (serde, camelCase, snake_case aliases, JSON Schema via schemars) is shared by the CLI (flags map 1:1), server JSON, all bindings and the C ABI. Puppeteer/wkhtmltopdf/Gotenberg compat layers *translate* into it (plus UA-origin CSS) and never extend the engine directly.

## 5. Feature decisions (the brief's "evaluate and decide" list)

| Feature | Decision | Milestone | Rationale |
|---|---|---|---|
| CSS Grid | Yes. Monolithic via taffy; row-boundary fragmentation later | M3 / M6 | R11: grid is ubiquitous in real invoice templates; taffy grid is mature (R06 §1). Prince also does not fragment grid (R04). |
| Multi-column | Yes, basic: `column-count/width/gap/rule`, `column-fill: auto/balance`, column breaks, continuation across pages. `column-span: all` and nesting deferred post-1.0 | M6 | The fragmentation engine supports columns natively (C12), so the layout is cheap. Labels, glossaries, receipts. |
| Footnotes | Yes: `float: footnote`, `::footnote-call`, `::footnote-marker`, `footnote-display: block/inline`, `footnote-policy: auto/line`, `@footnote` area with `max-height`; WeasyPrint/Prince model | M6 | Contracts and reports. No normative algorithm (R05a F13); we follow the de facto model. |
| Page floats (`float: top/bottom`, `float-reference`) | No (parsed, warned, treated as `float: none`) | post-1.0 | Little interop (R04, R05a). Figure placement via breaks suffices. |
| Form fields (AcroForm) | No interactive fields in 1.0. Form controls render as static appearance (border + value text). AcroForm post-1.0 when krilla forms ship | — | krilla forms unreleased (R08 F7g). |
| PDF encryption | Not in 1.0. Post-1.0 as a krilla patch (deterministic IV derivation in `--reproducible`). Incompatible with PDF/A | post-1.0 | No Rust writer supports it (R08). A non-deterministic lopdf post-process conflicts with DET goals. |
| Barcodes / QR | Yes: `recto-barcode:` URL scheme in `<img src>`/`url()` → generated SVG (QR, Code128, EAN-13/UPC-A, Code39, ITF-14, DataMatrix, PDF417 subject to R13 §5), policy-exempt (no I/O) | M6 | Tickets, labels, Swiss QR-bill/EPC invoices. A URL scheme reuses image sizing and needs no new element semantics. |
| MathML | No. Rendered as inline text content with `W_UNSUPPORTED_ELEMENT` | post-1.0 | Not in the target document classes. |
| JavaScript | Never | — | Security and determinism. Shims accept JS flags with a warning. |
| Letterhead/background PDF pages | Yes, opt-in (`--background-pdf`), via krilla `pdf` feature. Disallowed with PDF/A-2+/UA | M6 | Common invoice need (R08 F12). |
| Tagged PDF | On by default (`--no-tagged` to disable) | M5 | Differentiator (Prince default off, R04). |
| PDF/UA-1, PDF/A-1b/2b/2u/3b/3a/4 | Opt-in profiles | M5 | krilla enforces at write time (R08). |
| PDF/UA-2 | When krilla ships it (#449) | post-1.0 | — |
| Factur-X / ZUGFeRD | Yes: `--attach file.xml --facturx <profile>` → PDF/A-3b + AF + XMP extension schema | M5 | High-value invoice feature. Needs a krilla XMP patch (R08 F7a). |
| `:nth()` page selector, page groups | Yes (`:nth(An+B [of <name>])`, Prince 16 semantics `:first` = document first) | M6 | Cheap with page-context cascade (R05a F3). |
| Running elements / string-set | Yes, all of first/start/last/first-except | M2 | Core header/footer feature (R04, R05a). |
| `leader()` | Yes | M3 | TOCs. |
| Hyphenation | `hyphens: manual` M1, `auto` with bundled languages | M1 / M3 | — |
| Vertical writing modes | No (horizontal-tb only; `writing-mode` parsed, warned) | post-1.0 | CJK vertical is out of the target scope. |
| `position: fixed` repeats on every page | Yes | M2 | CSS2 §9.6.1; Chrome/wkhtmltopdf templates rely on it (R05b, R11). |
| `position: sticky` | Treated as `relative` | M2 | Meaningless in paged output. |
| Transforms (2D), opacity, `box-shadow`, gradients, `border-radius`, `filter` | 2D transforms, opacity, box-shadow, linear/radial/conic gradients, border-radius: yes. `filter`/`backdrop-filter`/`mix-blend-mode`: blend modes yes, filters no (warn) | M2–M3 | Common in templates. PDF supports them natively. |
| Webfont formats | TTF/OTF/TTC/WOFF/WOFF2, variable fonts, COLRv0/v1 + sbix/CBDT emoji (via krilla) | M2/M3 | — |
| Image formats | PNG, JPEG, GIF (first frame), WebP, BMP, SVG; no AVIF/HEIC/TIFF (warn) | M2 | Pure-Rust decoders only (R12). |

## 6. Compat surface decisions

- **wkhtmltopdf shim** (`recto wkhtmltopdf …` and `argv[0] == wkhtmltopdf` multicall): full R02 matrix. It reproduces wkhtmltopdf defaults (screen media, backgrounds on, outline depth 4, A4/10 mm, **smart shrinking emulated as a fit-to-width scale mode**), stderr `Warning:`/`Error:` lines plus `Done`, exit codes 0/1/2/3, a `--version` string containing `wkhtmltopdf 0.12.6 (recto x.y.z)`, `--enable-local-file-access` → `--allow-dir` (rooted, R10 §7.6), and header/footer HTML with variable substitution by class/id (`.page`, `.topage`, `.section`, …) without JS. M6.
- **Puppeteer/Playwright options** (Node binding `renderPuppeteer(html, PDFOptions)` and server field `puppeteerOptions`): exact unit rules (bare number = px, cm = 37.8 px), Letter default, `preferCSSPageSize`, header/footer templates with the 5 classes, `pageRanges` grammar, scale 0.1–2. M6.
- **Gotenberg-compatible routes** (`POST /forms/chromium/convert/html`, `/health`, `/version`, port 3000 option): any Gotenberg client switches by changing the base URL. M6 (basic route M4).
- **Engine features required by the shims** (all native, also exposed directly): fit-to-width scale mode, CLI-geometry-overrides-`@page` cascade layer, multi-document jobs with continuous page numbering, header/footer HTML templates bound to the page margin area, fixed-date substitution.

## 7. Testing strategy decisions

- Primary gate: the ~300 **WPT print reftests** (R11 F1) plus the WeasyPrint pixel-grid tests ported (605 tests, BSD-3 with attribution), rendered → rasterized with hayro at 96 dpi → fuzzy compared.
- Every test also renders twice and asserts byte-identical PDFs (determinism).
- Layout snapshot tests via `insta` over a stable text dump of the fragment tree (`--explain` format).
- PDF structure checks with lopdf in-process; nightly veraPDF (PDF/A, PDF/UA), qpdf `--check`.
- 15-document real-world smoke set (MIT/PD/BSD templates only), plus a 1000-page benchmark corpus.
- Fuzzing: HTML sink, CSS parser, selector matching, URL resolver, font loading, image sniffers, SVG sandbox, template engine, full pipeline with limits.

## 8. Performance plan (targets in spec/26)

- Cold start < 100 ms: no eager font parsing (bundled fonts are parsed lazily, and their metadata index is generated at build time); compiled ICU data; UA stylesheet parsed once with a lazily-initialized `OnceLock`.
- 100-page invoice batch < 1 s on one core: shape each paragraph once; intrinsic-size cache per box; shared font/image caches across batch jobs (content-addressed); krilla XObject dedup for repeated headers and logos.
- Memory linear in pages: fragment trees freed per page; compact display lists only retained for deferred finalization; krilla-held compressed streams.

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Own inline + table layout is large (≈ 18–23k LOC layout + 6–10k inline, R06/R07) | Ordered checklists; port WeasyPrint algorithms and tests; WPT gates per milestone |
| taffy API churn (6 minors in 2026) | Exact pin, ~500-LOC adapter, MIT license lets us vendor `flexbox.rs` |
| krilla is a single-maintainer crate; patches needed (XMP, streaming) | Upstream-first. Otherwise a thin fork crate `recto-krilla` pinned by git tag. Adapter isolates krilla types |
| Two fontations lines (C1) | Isolated behind `recto-pdf`; CI glyph-agreement test |
| target-counter non-convergence | Bounded passes, width reservation, warning, deterministic final pass |
| Chrome-pixel-parity expectations | Document deliberate differences (no point rounding, no shrink-to-fit unless a compat mode is selected); compat test suite vs stored Chrome/WeasyPrint references |

## 10. Items explicitly carried forward as verification spikes

These are listed in R-doc open questions and become checklist items, so implementation sessions verify them before relying on them:

- Real `cargo build` of the recommended set on `x86_64/aarch64-unknown-linux-musl`, with `cargo tree -d` duplicate audit and `cargo bloat` size budget (ARC/DEP).
- hayro output identical across x86_64 and aarch64 (TST).
- miniz_oxide/flate2 output identical across architectures (DET).
- krilla on `wasm32-unknown-unknown` (BND).
- HTTP client resolver hook for IP pinning (NET).
- Factur-X XMP schema against the official 1.0.07 spec plus veraPDF (ACC).
- wkhtmltopdf smart-shrinking constants against a real 0.12.6 binary (CMP), Chrome MediaBox/page rounding (CMP).
- Bundled font set: Liberation Sans/Serif/Mono (OFL-1.1), a symbol/emoji fallback (Noto Emoji monochrome or Noto Sans Symbols 2, OFL-1.1); exact files and sizes (FNT).
